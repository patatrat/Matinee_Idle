#!/usr/bin/env python3
"""
Step 1b: Genre enrichment via Last.fm artist.getTopTags.

Reads songs_enriched.json (or songs.json if that doesn't exist), fetches
genre tags for every unique artist that still has no genre, writes result
back to songs_enriched.json.

Usage:
    LASTFM_API_KEY=your_key python3 enrich_genres_lastfm.py
    python3 enrich_genres_lastfm.py --dry-run
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

def fetch_artist_genre(artist: str) -> str | None:
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
    if isinstance(tags, dict):
        tags = [tags]

    for tag in tags:
        name = tag.get("name", "").lower().strip()
        count = int(tag.get("count", 0))
        if count < 10:
            break  # tags are sorted by count desc; stop when they get sparse
        if name not in SKIP_TAGS and len(name) > 1:
            return name

    return None


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}

def save_checkpoint(cache: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cache, f)


def main():
    src = SONGS_IN if os.path.exists(SONGS_IN) else SONGS_FALL
    print(f"Reading from: {os.path.basename(src)}")
    songs = json.load(open(src))

    no_genre = [s for s in songs if not s.get("genre")]
    unique_artists = list(dict.fromkeys(normalize_artist(s["artist"]) for s in no_genre))

    print(f"Songs without genre:       {len(no_genre)}")
    print(f"Unique artists to look up: {len(unique_artists)}")
    print(f"Songs already have genre:  {sum(1 for s in songs if s.get('genre'))}")

    if DRY_RUN:
        print("\n--dry-run: exiting without fetching.")
        return

    cache = load_checkpoint()
    already_cached = sum(1 for a in unique_artists if a in cache)
    to_fetch = len(unique_artists) - already_cached
    print(f"Cached from prior run:     {already_cached}")
    print(f"Fetches needed:            {to_fetch}")
    print(f"ETA at 4 req/sec:          ~{int(to_fetch * RATE_LIMIT // 60)} min\n")

    fetched = 0
    errors = 0
    for artist in unique_artists:
        if artist in cache:
            continue
        try:
            genre = fetch_artist_genre(artist)
            cache[artist] = genre
            fetched += 1
            if fetched % 50 == 0:
                found = sum(1 for v in cache.values() if v)
                pct = 100 * found / len(cache) if cache else 0
                print(f"  [{fetched:5d}] fetched  |  {found} genres found ({pct:.0f}% hit rate)  |  {errors} errors")
            if fetched % SAVE_EVERY == 0:
                save_checkpoint(cache)
            time.sleep(RATE_LIMIT)
        except Exception as e:
            errors += 1
            cache[artist] = None
            print(f"  ERROR {artist!r}: {e}")
            time.sleep(RATE_LIMIT * 4)

    save_checkpoint(cache)
    print(f"\nDone fetching. {fetched} new lookups, {errors} errors.")

    # Build artist -> original-case lookup for applying results
    artist_key = {normalize_artist(s["artist"]): s["artist"] for s in songs}

    applied = 0
    for song in songs:
        if not song.get("genre"):
            genre = cache.get(normalize_artist(song["artist"]))
            if genre:
                song["genre"] = genre
                applied += 1

    print(f"Genres applied to songs:   {applied}")
    print(f"Total songs with genre:    {sum(1 for s in songs if s.get('genre'))} / {len(songs)}")

    with open(SONGS_OUT, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written to {SONGS_OUT}")


if __name__ == "__main__":
    main()
