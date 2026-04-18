#!/usr/bin/env python3
"""
Spotify track enrichment: adds spotify_url, spotify_popularity,
spotify_preview_url, and album_art_url to songs.

Uses Client Credentials flow — no user login required.
Reads songs_enriched.json (falls back to songs.json).
Writes back to songs_enriched.json.

Usage:
    python3 enrich_spotify.py
    python3 enrich_spotify.py --dry-run
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import base64

HERE        = os.path.dirname(os.path.abspath(__file__))
SONGS_IN    = os.path.join(HERE, "songs_enriched.json")
SONGS_FALL  = os.path.join(HERE, "songs.json")
SONGS_OUT   = os.path.join(HERE, "songs_enriched.json")
CHECKPOINT  = os.path.join(HERE, "spotify_cache.json")

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID",     "f3bcd797aeaa4a50bcb6132366835d64")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "30e26fd9d30844d08b94dced12fe380d")

RATE_LIMIT  = 0.15   # ~6 req/sec — safe for Spotify search
SAVE_EVERY  = 200
DRY_RUN     = "--dry-run" in sys.argv


# ── token management ────────────────────────────────────────────────────────

_token = None
_token_expiry = 0.0

def get_token() -> str:
    global _token, _token_expiry
    if _token and time.time() < _token_expiry - 60:
        return _token
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    _token = data["access_token"]
    _token_expiry = time.time() + data["expires_in"]
    return _token


# ── matching helpers ─────────────────────────────────────────────────────────

def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)          # strip parenthetical suffixes
    s = re.sub(r"feat\.?.*$", "", s)                # strip "feat. X"
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def similarity(a: str, b: str) -> float:
    """Simple token overlap ratio."""
    ta = set(normalize(a).split())
    tb = set(normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))

def best_match(song: dict, candidates: list) -> dict | None:
    """Pick the best Spotify track from search candidates."""
    target_artist = song["artist"]
    target_title  = song["title"]
    target_year   = song.get("release_year")

    scored = []
    for track in candidates:
        sp_artists = " ".join(a["name"] for a in track["artists"])
        artist_sim = max(similarity(target_artist, a["name"]) for a in track["artists"])
        title_sim  = similarity(target_title, track["name"])
        score      = artist_sim * 0.5 + title_sim * 0.5

        # boost if release year is close
        if target_year and track.get("album", {}).get("release_date"):
            sp_year = int(track["album"]["release_date"][:4])
            year_diff = abs(sp_year - target_year)
            if year_diff <= 2:
                score += 0.1
            elif year_diff > 10:
                score -= 0.05

        scored.append((score, track))

    scored.sort(key=lambda x: -x[0])
    if scored and scored[0][0] >= 0.5:
        return scored[0][1]
    return None


# ── Spotify search ───────────────────────────────────────────────────────────

def search_track(artist: str, title: str) -> list:
    """Try field-qualified search first, fall back to free-text."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    strategies = [
        f"artist:{artist} track:{title}",
        f"{artist} {title}",
    ]

    for query in strategies:
        params = urllib.parse.urlencode({"q": query, "type": "track", "limit": 5})
        req = urllib.request.Request(
            f"https://api.spotify.com/v1/search?{params}",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            tracks = data.get("tracks", {}).get("items", [])
            if tracks:
                return tracks
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 5))
                print(f"  Rate limited — sleeping {retry_after}s")
                time.sleep(retry_after)
                return search_track(artist, title)   # retry same call
            if e.code in (400, 404):
                return []
            raise

    return []


def enrich_song(song: dict) -> dict | None:
    """Return Spotify fields dict if a match is found, else None."""
    candidates = search_track(song["artist"], song["title"])
    track = best_match(song, candidates)
    if not track:
        return None

    images = track.get("album", {}).get("images", [])
    return {
        "spotify_url":         track["external_urls"].get("spotify"),
        "spotify_popularity":  track.get("popularity"),
        "spotify_preview_url": track.get("preview_url"),
        "album_art_url":       images[0]["url"] if images else None,
    }


# ── checkpoint helpers ───────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}

def save_checkpoint(cache: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cache, f)

def cache_key(song: dict) -> str:
    return f"{normalize(song['artist'])}|||{normalize(song['title'])}"


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    src = SONGS_IN if os.path.exists(SONGS_IN) else SONGS_FALL
    print(f"Reading from: {os.path.basename(src)}")
    songs = json.load(open(src))

    to_enrich = [s for s in songs if not s.get("spotify_url")]
    print(f"Songs without Spotify data: {len(to_enrich)}")
    print(f"Songs already matched:      {len(songs) - len(to_enrich)}")

    if DRY_RUN:
        print("\n--dry-run: exiting without fetching.")
        return

    cache = load_checkpoint()
    keys_needed = [cache_key(s) for s in to_enrich]
    already_cached = sum(1 for k in keys_needed if k in cache)
    to_fetch = len(to_enrich) - already_cached
    print(f"Cached from prior run:      {already_cached}")
    print(f"Searches needed:            {to_fetch}")
    print(f"ETA at 6 req/sec:           ~{int(to_fetch * RATE_LIMIT // 60)} min\n")

    # Refresh token upfront
    get_token()

    fetched = 0
    matched = 0
    errors  = 0

    for song in to_enrich:
        key = cache_key(song)
        if key in cache:
            continue
        try:
            result = enrich_song(song)
            cache[key] = result   # None = searched, no match
            fetched += 1
            if result:
                matched += 1
            if fetched % 100 == 0:
                pct = 100 * matched / fetched if fetched else 0
                print(f"  [{fetched:5d}] searched  |  {matched} matched ({pct:.0f}%)  |  {errors} errors")
            if fetched % SAVE_EVERY == 0:
                save_checkpoint(cache)
            time.sleep(RATE_LIMIT)
        except Exception as e:
            errors += 1
            cache[key] = None
            print(f"  ERROR {song['artist']!r} — {song['title']!r}: {e}")
            time.sleep(RATE_LIMIT * 5)

    save_checkpoint(cache)
    print(f"\nDone. {fetched} searches, {matched} matched, {errors} errors.")

    # Apply cache to songs
    applied = 0
    for song in songs:
        key = cache_key(song)
        result = cache.get(key)
        if result and not song.get("spotify_url"):
            song.update(result)
            applied += 1

    print(f"Spotify data applied:       {applied} songs")
    print(f"Total with Spotify:         {sum(1 for s in songs if s.get('spotify_url'))} / {len(songs)}")

    with open(SONGS_OUT, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written to {SONGS_OUT}")


if __name__ == "__main__":
    main()
