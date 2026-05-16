#!/usr/bin/env python3
"""
Fetch release_year and genre from Spotify for songs that already have a
spotify_url but are missing one or both fields.

  - release_year: from GET /tracks?ids=... → track.album.release_date
  - genre:        from GET /artists?ids=... → artist.genres[] mapped to
                  the canonical genre list

Only touches songs where spotify_url is set AND (release_year is None OR
genre == "unmatched").

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
import urllib.request
import urllib.error

HERE       = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH = os.path.join(HERE, "explorer/public/songs.json")
SONGS_BACK = SONGS_PATH + ".bak"

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID",     "f3bcd797aeaa4a50bcb6132366835d64")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "30e26fd9d30844d08b94dced12fe380d")

RATE_LIMIT = 0.6     # seconds between API calls
DRY_RUN    = "--dry-run" in sys.argv
SAVE_EVERY = 200

# ── Canonical genre mapping (mirrors enrich_genres_missing.py) ────────────────

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
    """Map a list of Spotify artist genre strings to a canonical genre."""
    for g in raw_genres:
        g_low = g.lower()
        if g_low in SKIP:
            continue
        if g_low in CANONICAL:
            return g_low
        if g_low in MAPPING:
            return MAPPING[g_low]
        # keyword scan
        for kw, canon in MAPPING.items():
            if kw in g_low:
                return canon
    return None


# ── Spotify auth ─────────────────────────────────────────────────────────────

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


def spotify_get(path: str) -> dict:
    """GET from Spotify API with simple retry on 429."""
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
            print(f"  HTTP {e.code} on {path[:80]}: {body[:300]}")
            if e.code == 429:
                retry_after = int(e.headers.get("Retry-After", 10))
                print(f"  Rate limited — waiting {retry_after}s …")
                time.sleep(retry_after)
            elif e.code == 401:
                global _token
                _token = None  # force token refresh
                time.sleep(1)
            else:
                raise
    raise RuntimeError(f"Failed after retries: {path}")


# ── helpers ───────────────────────────────────────────────────────────────────

def track_id_from_url(url: str) -> str | None:
    m = re.search(r"spotify\.com/track/([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


def release_year_from_date(date_str: str) -> int | None:
    if not date_str:
        return None
    m = re.match(r"(\d{4})", date_str)
    return int(m.group(1)) if m else None


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    songs = json.load(open(SONGS_PATH))

    # Identify targets
    need_year  = {s["id"] for s in songs if s.get("spotify_url") and not s.get("release_year")}
    need_genre = {s["id"] for s in songs if s.get("spotify_url") and s.get("genre") == "unmatched"}
    targets    = need_year | need_genre

    print(f"Songs needing release_year : {len(need_year)}")
    print(f"Songs needing genre        : {len(need_genre)}")
    print(f"Total unique targets       : {len(targets)}")

    if DRY_RUN:
        print("Dry run — exiting.")
        return

    # Build id→song index
    by_id = {s["id"]: s for s in songs}

    # Collect (song_id, track_id) for targets
    target_songs = [(sid, track_id_from_url(by_id[sid]["spotify_url"]))
                    for sid in targets]
    target_songs = [(sid, tid) for sid, tid in target_songs if tid]

    print(f"Valid Spotify track IDs    : {len(target_songs)}")
    print()

    # ── Combined pass: individual track + artist lookups ─────────────────────
    # Uses /tracks/{id} and /artists/{id} (individual endpoints) instead of
    # batch endpoints, which require elevated API access.

    year_updates  = 0
    genre_updates = 0
    artist_cache  = {}  # artist_id → canonical genre (avoid duplicate lookups)

    print(f"Fetching track + artist data ({len(target_songs)} songs) …")
    for i, (song_id, track_id) in enumerate(target_songs):
        song = by_id[song_id]

        # ── Track lookup ──────────────────────────────────────────────────────
        try:
            track = spotify_get(f"/tracks/{track_id}")
        except Exception as e:
            print(f"  [{i+1}] track {track_id} error: {e}")
            time.sleep(RATE_LIMIT)
            continue

        # release year
        if song_id in need_year:
            yr = release_year_from_date(track.get("album", {}).get("release_date", ""))
            if yr:
                song["release_year"] = yr
                year_updates += 1

        # ── Artist lookup for genre ───────────────────────────────────────────
        if song_id in need_genre:
            artist_ids = [a["id"] for a in track.get("artists", []) if a.get("id")]
            if artist_ids:
                artist_id = artist_ids[0]
                if artist_id not in artist_cache:
                    time.sleep(RATE_LIMIT)
                    try:
                        artist = spotify_get(f"/artists/{artist_id}")
                        artist_cache[artist_id] = spotify_genre(artist.get("genres", []))
                    except Exception as e:
                        print(f"  [{i+1}] artist {artist_id} error: {e}")
                        artist_cache[artist_id] = None
                canon = artist_cache[artist_id]
                if canon:
                    song["genre"] = canon
                    genre_updates += 1

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(target_songs)} — +{year_updates} years, +{genre_updates} genres")

        time.sleep(RATE_LIMIT)

    print(f"Done. release_year filled: {year_updates}, genre filled: {genre_updates} / {len(need_genre)}")
    print()

    # ── Save ──────────────────────────────────────────────────────────────────

    import shutil
    shutil.copy(SONGS_PATH, SONGS_BACK)
    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))

    print(f"Saved {SONGS_PATH}")
    print(f"Summary: +{year_updates} release years, +{genre_updates} genres")


if __name__ == "__main__":
    main()
