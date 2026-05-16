#!/usr/bin/env python3
"""
Fetch release_year and genre from Spotify for songs that have a spotify_url
but are missing one or both fields.

Two-phase approach to avoid hitting artist endpoint rate limits:
  Phase 1 — Track lookups (fast, ~0.6s each):
      GET /tracks/{id} → album.release_date (release_year) + artist IDs
  Phase 2 — Artist lookups (slow, deduplicated, ~3s each):
      GET /artists/{id} → genres[] → mapped to canonical genre list
      Only unique artists are fetched, so repeat artists cost nothing.

Usage:
    python3 enrich_spotify_metadata.py
    python3 enrich_spotify_metadata.py --dry-run
"""

import json
import os
import re
import sys
import time
import base64
import shutil
import urllib.request
import urllib.error

HERE          = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH    = os.path.join(HERE, "explorer/public/songs.json")
SONGS_BACK    = SONGS_PATH + ".bak"
ARTIST_CACHE  = os.path.join(HERE, "spotify_artist_genre_cache.json")

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID",     "f3bcd797aeaa4a50bcb6132366835d64")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "30e26fd9d30844d08b94dced12fe380d")

TRACK_RATE    = 0.6    # seconds between track calls
ARTIST_RATE   = 3.0    # seconds between artist calls (much more conservative)
MAX_WAIT      = 300    # if Retry-After > this, save and exit cleanly
SAVE_EVERY    = 250
DRY_RUN       = "--dry-run" in sys.argv


# ── Canonical genre mapping ───────────────────────────────────────────────────

CANONICAL = {
    "rock", "classic rock", "soul", "pop", "country", "new wave", "folk",
    "jazz", "blues", "indie", "comedy", "rockabilly", "progressive rock",
    "funk", "punk", "electronic", "alternative", "reggae", "bluegrass",
    "disco", "metal", "hip-hop", "world", "classical", "soundtrack",
}

MAPPING: dict[str, str] = {
    "hard rock": "rock", "art rock": "rock", "garage rock": "rock",
    "garage": "rock", "pub rock": "rock", "surf rock": "rock",
    "southern rock": "rock", "soft rock": "rock", "pop rock": "rock",
    "pop/rock": "rock", "rock and roll": "rock", "rock n roll": "rock",
    "rock'n'roll": "rock", "rock & roll": "rock", "beat": "rock",
    "oldies": "rock", "british invasion": "rock",
    "rhythm and blues": "soul", "r&b": "soul", "rnb": "soul",
    "quiet storm": "soul", "motown": "soul", "neo soul": "soul",
    "contemporary r&b": "soul",
    "dance pop": "pop", "adult contemporary": "pop", "bubblegum": "pop",
    "teen pop": "pop", "europop": "pop", "synth-pop": "new wave",
    "synthpop": "new wave", "post-punk": "new wave", "new romantic": "new wave",
    "power pop": "pop",
    "folk rock": "folk", "singer-songwriter": "folk", "acoustic": "folk",
    "americana": "folk", "anti-folk": "folk",
    "country rock": "country", "outlaw country": "country",
    "alt-country": "country", "bluegrass": "bluegrass",
    "jazz fusion": "jazz", "smooth jazz": "jazz", "bebop": "jazz",
    "big band": "jazz", "swing": "jazz",
    "delta blues": "blues", "electric blues": "blues", "chicago blues": "blues",
    "indie rock": "indie", "indie pop": "indie", "lo-fi": "indie",
    "jangle pop": "indie",
    "comedy rock": "comedy", "novelty": "comedy", "parody": "comedy",
    "prog rock": "progressive rock", "progressive": "progressive rock",
    "krautrock": "progressive rock", "psychedelic rock": "progressive rock",
    "psychedelic": "progressive rock", "space rock": "progressive rock",
    "funk rock": "funk", "funk soul": "funk",
    "hardcore punk": "punk", "post-punk": "punk", "oi": "punk",
    "ska punk": "punk",
    "electronica": "electronic", "ambient": "electronic", "techno": "electronic",
    "house": "electronic", "trance": "electronic", "idm": "electronic",
    "electro": "electronic", "dance": "electronic", "edm": "electronic",
    "synth": "electronic",
    "alternative rock": "alternative", "grunge": "alternative",
    "shoegaze": "alternative", "dream pop": "alternative",
    "ska": "reggae", "dub": "reggae", "rocksteady": "reggae",
    "latin": "world", "bossa nova": "world", "afrobeat": "world",
    "worldbeat": "world", "celtic": "world", "flamenco": "world",
    "chanson": "world",
    "orchestral": "classical", "opera": "classical", "chamber": "classical",
    "film score": "soundtrack", "film music": "soundtrack",
    "heavy metal": "metal", "thrash metal": "metal", "doom metal": "metal",
    "death metal": "metal", "glam metal": "metal",
    "hip hop": "hip-hop", "rap": "hip-hop", "trap": "hip-hop",
}

SKIP = {
    "seen live", "favorites", "love", "awesome", "under 2000 listeners",
    "new zealand", "australian", "british", "american", "heard on matinee idle",
    "rnz", "male vocalists", "female vocalists", "all",
}


def spotify_genre(raw_genres: list[str]) -> str | None:
    for g in raw_genres:
        g_low = g.lower()
        if g_low in SKIP:
            continue
        if g_low in CANONICAL:
            return g_low
        if g_low in MAPPING:
            return MAPPING[g_low]
        for kw, canon in MAPPING.items():
            if kw in g_low:
                return canon
    return None


# ── Spotify auth ──────────────────────────────────────────────────────────────

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
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Token fetch failed ({e.code}): {body[:300]}") from e
    _token = data["access_token"]
    _token_expiry = time.time() + data["expires_in"]
    print(f"Token acquired (expires in {data['expires_in']}s)")
    return _token


def spotify_get(path: str, rate: float) -> dict | None:
    """GET from Spotify API. Returns None on 404. Raises SystemExit on long rate limits."""
    url = f"https://api.spotify.com/v1{path}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {get_token()}"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode(errors="replace")
            except Exception:
                pass
            if e.code == 404:
                return None
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 10))
                if retry_after > MAX_WAIT:
                    print(f"  429 Retry-After={retry_after}s exceeds {MAX_WAIT}s cap — aborting phase")
                    raise SystemExit(0)
                print(f"  429 — waiting {retry_after}s …")
                time.sleep(retry_after)
            elif e.code == 401:
                global _token
                _token = None
                time.sleep(1)
            else:
                print(f"  HTTP {e.code} on {path[:80]}: {body[:200]}")
                raise
    return None


# ── helpers ───────────────────────────────────────────────────────────────────

def track_id_from_url(url: str) -> str | None:
    m = re.search(r"spotify\.com/track/([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


def release_year_from_date(date_str: str) -> int | None:
    if not date_str:
        return None
    m = re.match(r"(\d{4})", date_str)
    return int(m.group(1)) if m else None


def save_songs(songs: list) -> None:
    shutil.copy(SONGS_PATH, SONGS_BACK)
    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    songs = json.load(open(SONGS_PATH))
    by_id = {s["id"]: s for s in songs}

    need_year  = {s["id"] for s in songs if s.get("spotify_url") and not s.get("release_year")}
    need_genre = {s["id"] for s in songs if s.get("spotify_url") and s.get("genre") == "unmatched"}
    targets    = need_year | need_genre

    print(f"Songs needing release_year : {len(need_year)}")
    print(f"Songs needing genre        : {len(need_genre)}")
    print(f"Total unique targets       : {len(targets)}")

    if DRY_RUN:
        return

    target_list = [(sid, track_id_from_url(by_id[sid]["spotify_url"]))
                   for sid in targets]
    target_list = [(sid, tid) for sid, tid in target_list if tid]

    # ── Phase 1: Track lookups — get years + collect artist IDs ──────────────
    # Fast (0.6s each). Collect artist IDs for all genre-needing songs.

    print(f"\nPhase 1: track lookups ({len(target_list)} songs, ~{len(target_list)*TRACK_RATE/60:.0f} min) …")

    year_updates = 0
    song_to_artist: dict[str, str] = {}  # song_id → first artist_id

    for i, (song_id, track_id) in enumerate(target_list):
        try:
            track = spotify_get(f"/tracks/{track_id}", TRACK_RATE)
        except SystemExit:
            save_songs(songs)
            print(f"  Saved progress: +{year_updates} years. Re-run to continue.")
            raise

        if track:
            if song_id in need_year:
                yr = release_year_from_date(track.get("album", {}).get("release_date", ""))
                if yr:
                    by_id[song_id]["release_year"] = yr
                    year_updates += 1

            if song_id in need_genre:
                artist_ids = [a["id"] for a in track.get("artists", []) if a.get("id")]
                if artist_ids:
                    song_to_artist[song_id] = artist_ids[0]

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(target_list)} — +{year_updates} years, "
                  f"{len(song_to_artist)} artist IDs collected")

        if (i + 1) % SAVE_EVERY == 0:
            save_songs(songs)

        time.sleep(TRACK_RATE)

    save_songs(songs)
    print(f"Phase 1 done: +{year_updates} release years")
    print(f"Unique artists to look up: {len(set(song_to_artist.values()))}")

    # ── Phase 2: Artist lookups — get genres ─────────────────────────────────
    # Slow (3s each), but deduplicated: each unique artist fetched only once.

    unique_artists = list(set(song_to_artist.values()))
    print(f"\nPhase 2: artist lookups ({len(unique_artists)} unique artists, "
          f"~{len(unique_artists)*ARTIST_RATE/60:.0f} min) …")

    # Load persisted artist genre cache so interrupted runs don't re-fetch
    artist_genre_cache: dict[str, str | None] = {}
    if os.path.exists(ARTIST_CACHE):
        artist_genre_cache = json.load(open(ARTIST_CACHE))
        already_cached = sum(1 for a in unique_artists if a in artist_genre_cache)
        print(f"  {already_cached} artists already in cache, {len(unique_artists)-already_cached} to fetch")

    genre_updates = 0

    for i, artist_id in enumerate(unique_artists):
        if artist_id in artist_genre_cache:
            continue

        try:
            artist = spotify_get(f"/artists/{artist_id}", ARTIST_RATE)
        except SystemExit:
            # Save what we have before exiting
            json.dump(artist_genre_cache, open(ARTIST_CACHE, "w"), indent=2)
            _apply_genres(songs, by_id, song_to_artist, artist_genre_cache, need_genre)
            save_songs(songs)
            print(f"  Rate limited. Saved cache ({len(artist_genre_cache)} artists) and songs. Re-run to continue.")
            raise

        artist_genre_cache[artist_id] = spotify_genre(artist.get("genres", [])) if artist else None

        if (i + 1) % 50 == 0:
            json.dump(artist_genre_cache, open(ARTIST_CACHE, "w"), indent=2)
            print(f"  {i+1}/{len(unique_artists)} artists fetched")

        time.sleep(ARTIST_RATE)

    json.dump(artist_genre_cache, open(ARTIST_CACHE, "w"), indent=2)

    genre_updates = _apply_genres(songs, by_id, song_to_artist, artist_genre_cache, need_genre)
    save_songs(songs)

    print(f"\nDone.")
    print(f"  +{year_updates} release years")
    print(f"  +{genre_updates} genres filled ({len(need_genre) - genre_updates} still unmatched)")


def _apply_genres(songs, by_id, song_to_artist, artist_genre_cache, need_genre):
    count = 0
    for song_id, artist_id in song_to_artist.items():
        if song_id not in need_genre:
            continue
        canon = artist_genre_cache.get(artist_id)
        if canon:
            by_id[song_id]["genre"] = canon
            count += 1
    return count


if __name__ == "__main__":
    main()
