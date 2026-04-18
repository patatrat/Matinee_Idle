#!/usr/bin/env python3
"""
Step 1b: Genre enrichment via Last.fm track.getTopTags + artist.getTopTags fallback.

Fetches track-specific tags for every song (more accurate than artist-level tags),
falling back to artist.getTopTags when a track has no tags. Overwrites ALL existing
genres — including bad data from the original enrichment.

Reads songs_enriched.json (or songs.json). Writes back to songs_enriched.json.
If lastfm_genre_cache.json exists from a previous artist-only run, delete it first
— the cache key format changed to artist|||title.

Usage:
    python3 enrich_genres_lastfm.py --dry-run
    python3 enrich_genres_lastfm.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

HERE       = os.path.dirname(os.path.abspath(__file__))
SONGS_IN   = os.path.join(HERE, "songs_enriched.json")
SONGS_FALL = os.path.join(HERE, "songs.json")          # fallback if enriched doesn't exist
SONGS_OUT  = os.path.join(HERE, "songs_enriched.json")
CHECKPOINT = os.path.join(HERE, "lastfm_genre_cache.json")
API_KEY    = os.environ.get("LASTFM_API_KEY", "68aae586eac1ab54f7cf77fa6ca9f9a7")
RATE_LIMIT = 0.25   # seconds between requests (4/sec, under the 5/sec limit)
SAVE_EVERY = 200
DRY_RUN    = "--dry-run" in sys.argv

# Tags that aren't useful genre labels
SKIP_TAGS = {
    "seen live", "favorites", "favourite", "love", "awesome", "beautiful",
    "sexy", "cool", "amazing", "best", "classic", "all", "good", "great",
    "under 2000 listeners", "under 5000 listeners",
    "male vocalists", "female vocalists", "male vocalist", "female vocalist",
    "singer-songwriter",  # keep this actually - it's useful
    "albums i own", "my favorites", "to listen", "wishlist",
    "new zealand", "australia", "uk", "usa", "american", "british",
    "canadian", "australian", "german", "french", "swedish", "japanese",
    "heard on matinee idle", "rnz", "radio nz",
}

def normalize_artist(name: str) -> str:
    return name.lower().strip()

def best_tag(tags: list, min_count: int = 5) -> str | None:
    if isinstance(tags, dict):
        tags = [tags]
    for tag in tags:
        name = tag.get("name", "").lower().strip()
        count = int(tag.get("count", 0))
        if count < min_count:
            break
        if name not in SKIP_TAGS and len(name) > 1:
            return name
    return None

def fetch_track_genre(artist: str, title: str) -> str | None:
    """Track-level tags — most accurate, but not always populated."""
    params = urllib.parse.urlencode({
        "method": "track.getTopTags",
        "artist": artist,
        "track": title,
        "api_key": API_KEY,
        "format": "json",
        "autocorrect": 1,
    })
    url = f"https://ws.audioscrobbler.com/2.0/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MatineeIdleArchive/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return None
        raise
    if "error" in data:
        return None
    tags = data.get("toptags", {}).get("tag", [])
    return best_tag(tags, min_count=5)

def fetch_artist_genre(artist: str) -> str | None:
    """Artist-level tags — broader but better coverage as fallback."""
    params = urllib.parse.urlencode({
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": API_KEY,
        "format": "json",
        "autocorrect": 1,
    })
    url = f"https://ws.audioscrobbler.com/2.0/?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MatineeIdleArchive/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return None
        raise
    if "error" in data:
        return None
    tags = data.get("toptags", {}).get("tag", [])
    return best_tag(tags, min_count=10)


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}

def save_checkpoint(cache: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cache, f)


def song_key(song: dict) -> str:
    return f"{normalize_artist(song['artist'])}|||{song['title'].lower().strip()}"

def artist_key(song: dict) -> str:
    return normalize_artist(song["artist"])

def main():
    src = SONGS_IN if os.path.exists(SONGS_IN) else SONGS_FALL
    print(f"Reading from: {os.path.basename(src)}")
    songs = json.load(open(src))

    # Enrich ALL songs — overwrite existing genres with accurate track-level data
    print(f"Total songs:               {len(songs)}")
    print(f"Currently have genre:      {sum(1 for s in songs if s.get('genre'))}")

    if DRY_RUN:
        # Estimate unique fetches needed
        unique_tracks  = len(set(song_key(s) for s in songs))
        unique_artists = len(set(artist_key(s) for s in songs))
        print(f"Unique track lookups:      {unique_tracks}")
        print(f"Unique artist fallbacks:   {unique_artists} (only if track lookup fails)")
        print(f"Max ETA at 4 req/sec:      ~{int(unique_tracks * RATE_LIMIT // 60)} min")
        print("\n--dry-run: exiting without fetching.")
        return

    cache = load_checkpoint()
    to_fetch = [s for s in songs if song_key(s) not in cache]
    print(f"Cached from prior run:     {len(songs) - len(to_fetch)}")
    print(f"Track lookups needed:      {len(to_fetch)}")
    print(f"ETA at 4 req/sec:          ~{int(len(to_fetch) * RATE_LIMIT // 60)} min\n")

    # Per-artist fallback cache (populated lazily)
    artist_cache: dict = {}

    fetched = 0
    errors  = 0
    for song in to_fetch:
        key = song_key(song)
        try:
            # 1. Try track-specific tags first
            genre = fetch_track_genre(song["artist"], song["title"])
            time.sleep(RATE_LIMIT)

            # 2. Fall back to artist tags if track has none
            if not genre:
                ak = artist_key(song)
                if ak not in artist_cache:
                    artist_cache[ak] = fetch_artist_genre(song["artist"])
                    time.sleep(RATE_LIMIT)
                genre = artist_cache[ak]

            cache[key] = genre
            fetched += 1
            if fetched % 100 == 0:
                found = sum(1 for v in cache.values() if v)
                pct = 100 * found / len(cache) if cache else 0
                print(f"  [{fetched:5d}] fetched  |  {found} genres found ({pct:.0f}% hit rate)  |  {errors} errors")
            if fetched % SAVE_EVERY == 0:
                save_checkpoint(cache)
        except Exception as e:
            errors += 1
            cache[key] = None
            print(f"  ERROR {song['artist']!r} — {song['title']!r}: {e}")
            time.sleep(RATE_LIMIT * 4)

    save_checkpoint(cache)
    print(f"\nDone fetching. {fetched} new lookups, {errors} errors.")

    applied = overridden = 0
    for song in songs:
        new_genre = cache.get(song_key(song))
        if new_genre:
            if song.get("genre") and song["genre"] != new_genre:
                overridden += 1
            elif not song.get("genre"):
                applied += 1
            song["genre"] = new_genre

    print(f"New genres applied:        {applied}")
    print(f"Bad genres overridden:     {overridden}")
    print(f"Total songs with genre:    {sum(1 for s in songs if s.get('genre'))} / {len(songs)}")

    with open(SONGS_OUT, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written to {SONGS_OUT}")


if __name__ == "__main__":
    main()
