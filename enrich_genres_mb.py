#!/usr/bin/env python3
"""
Step 1: Genre enrichment via MusicBrainz direct MBID lookups.

Reads songs.json, fetches genres for songs that have an mbid but no genre,
writes songs_enriched.json. Saves a checkpoint cache so it can be interrupted
and resumed without re-fetching already-looked-up MBIDs.

Usage:
    python3 enrich_genres_mb.py              # run (or resume)
    python3 enrich_genres_mb.py --dry-run    # show stats without fetching
"""

import json
import time
import sys
import os
import urllib.request
import urllib.error

HERE          = os.path.dirname(os.path.abspath(__file__))
SONGS_IN      = os.path.join(HERE, "songs.json")
SONGS_OUT     = os.path.join(HERE, "songs_enriched.json")
CHECKPOINT    = os.path.join(HERE, "mb_genre_cache.json")
MB_BASE       = "https://musicbrainz.org/ws/2/recording"
USER_AGENT    = "MatineeIdleArchive/1.0 ( radomski.co.nz )"
RATE_LIMIT    = 1.1   # seconds between requests (stay under 1/sec limit)
SAVE_EVERY    = 50    # checkpoint after this many new fetches
DRY_RUN       = "--dry-run" in sys.argv


def fetch_mb_genres(mbid: str) -> str | None:
    """Fetch the top genre tag for a recording MBID. Returns None if not found."""
    url = f"{MB_BASE}/{mbid}?inc=genres+tags&fmt=json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        raise

    # Prefer explicit MB genres over user tags
    genres = data.get("genres") or []
    tags   = data.get("tags") or []

    if genres:
        best = max(genres, key=lambda g: g.get("count", 0))
        return best["name"] if best.get("count", 0) >= 1 else None

    if tags:
        # Filter out non-genre tags (years, countries, moods are less useful)
        skip = {"nz", "new zealand", "australia", "uk", "us", "heard on matinee idle"}
        candidates = [t for t in tags if t["name"].lower() not in skip]
        if candidates:
            best = max(candidates, key=lambda t: t.get("count", 0))
            return best["name"] if best.get("count", 0) >= 1 else None

    return None


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}


def save_checkpoint(cache: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cache, f)


def ensure_songs_json():
    """Generate songs.json from the backup if it doesn't exist."""
    if os.path.exists(SONGS_IN):
        return
    backups = [f for f in os.listdir(HERE) if f.endswith(".backup.gz")]
    if not backups:
        sys.exit(f"ERROR: {SONGS_IN} not found and no .backup.gz file in {HERE}")
    extract = os.path.join(HERE, "extract_songs.py")
    if not os.path.exists(extract):
        sys.exit(f"ERROR: {SONGS_IN} not found. Run extract_songs.py first.")
    print(f"songs.json not found — running extract_songs.py first...")
    import subprocess
    subprocess.run([sys.executable, extract], check=True)


def main():
    ensure_songs_json()
    songs = json.load(open(SONGS_IN))

    # Songs needing genre lookup: have mbid, no genre
    to_enrich = [s for s in songs if s.get("mbid") and not s.get("genre")]
    unique_mbids = list(dict.fromkeys(s["mbid"] for s in to_enrich))

    print(f"Songs needing genre:    {len(to_enrich)}")
    print(f"Unique MBIDs to fetch:  {len(unique_mbids)}")
    print(f"Already have genre:     {sum(1 for s in songs if s.get('genre'))}")

    if DRY_RUN:
        print("\n--dry-run: exiting without fetching.")
        return

    # Load resume cache
    cache = load_checkpoint()
    already_cached = sum(1 for m in unique_mbids if m in cache)
    print(f"Cached from prior run:  {already_cached}")
    print(f"Fetches needed:         {len(unique_mbids) - already_cached}")
    eta_secs = (len(unique_mbids) - already_cached) * RATE_LIMIT
    print(f"ETA at 1 req/sec:       ~{int(eta_secs // 60)} min\n")

    # Fetch missing MBIDs
    fetched = 0
    errors  = 0
    for i, mbid in enumerate(unique_mbids):
        if mbid in cache:
            continue
        try:
            genre = fetch_mb_genres(mbid)
            cache[mbid] = genre   # None means "looked up, no genre found"
            fetched += 1
            if fetched % 10 == 0:
                found = sum(1 for v in cache.values() if v)
                print(f"  [{fetched:5d}] fetched  |  {found} genres found so far  |  {errors} errors")
            if fetched % SAVE_EVERY == 0:
                save_checkpoint(cache)
            time.sleep(RATE_LIMIT)
        except Exception as e:
            errors += 1
            cache[mbid] = None
            print(f"  ERROR {mbid}: {e}")
            time.sleep(RATE_LIMIT * 2)

    save_checkpoint(cache)
    print(f"\nDone fetching. {fetched} new lookups, {errors} errors.")

    # Apply cache to songs
    applied = 0
    for song in songs:
        if not song.get("genre") and song.get("mbid"):
            genre = cache.get(song["mbid"])
            if genre:
                song["genre"] = genre
                applied += 1

    print(f"Genres applied to songs: {applied}")
    print(f"Total songs with genre:  {sum(1 for s in songs if s.get('genre'))}")

    with open(SONGS_OUT, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written to {SONGS_OUT}")


if __name__ == "__main__":
    main()
