#!/usr/bin/env python3
"""
Fix release years using MusicBrainz recording first-release-date.

For each song with an MBID, queries the MB recording API for
`first-release-date` — the date the recording was first released
on ANY release. This corrects years that came from compilations,
remasters, or re-issues rather than the original release.

Reads/writes explorer/public/songs.json.
Caches MB responses to mb_first_release_cache.json.

Usage:
    python3 fix_release_years.py --dry-run
    python3 fix_release_years.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

HERE       = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH = os.path.join(HERE, "explorer/public/songs.json")
CHECKPOINT = os.path.join(HERE, "mb_first_release_cache.json")
MB_BASE    = "https://musicbrainz.org/ws/2/recording"
RATE_LIMIT = 1.1   # MB requires ≤ 1 req/sec without authentication
SAVE_EVERY = 200
DRY_RUN    = "--dry-run" in sys.argv


def fetch_first_release_date(mbid: str) -> str | None:
    url = f"{MB_BASE}/{mbid}?fmt=json"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MatineeIdleArchive/1.0 (radomski.co.nz)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get("first-release-date")  # e.g. "1965-03-15" or "1965"
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return None
        if e.code == 503:
            print("  MB rate limited, sleeping 10s…")
            time.sleep(10)
            return fetch_first_release_date(mbid)
        raise


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}


def save_checkpoint(cache: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cache, f)


def main():
    songs = json.load(open(SONGS_PATH))
    unique_mbids = list(dict.fromkeys(s["mbid"] for s in songs if s.get("mbid")))

    print(f"Total songs:   {len(songs)}")
    print(f"Unique MBIDs:  {len(unique_mbids)}")

    if DRY_RUN:
        REISSUE_KEYWORDS = [
            "best of", "greatest", "collection", "anthology", "complete",
            "essential", "definitive", "ultimate", "platinum", "gold",
            "remaster", "deluxe", "edition", "box set", "vol.", "hits",
            "compilation", "retrospective", "legacy", "archive",
        ]
        flagged = [
            s for s in songs
            if s.get("release_year") and s.get("mb_release")
            and any(kw in s["mb_release"].lower() for kw in REISSUE_KEYWORDS)
        ]
        print(f"\nLikely wrong (matched to compilation/remaster): {len(flagged)}")
        for s in flagged[:20]:
            print(f"  {s['artist']} — {s['title']}")
            print(f"    current year: {s['release_year']}  |  album: {s['mb_release']!r}")
        print(f"\n--dry-run: would fetch {len(unique_mbids)} MBIDs from MusicBrainz.")
        print(f"ETA at 1 req/sec: ~{len(unique_mbids) // 60} min")
        return

    cache = load_checkpoint()
    to_fetch = [m for m in unique_mbids if m not in cache]
    print(f"Cached:        {len(cache)}")
    print(f"To fetch:      {len(to_fetch)}")
    print(f"ETA at 1 req/sec: ~{len(to_fetch) // 60} min\n")

    fetched = errors = 0
    for mbid in to_fetch:
        try:
            date = fetch_first_release_date(mbid)
            cache[mbid] = date
            fetched += 1
            if fetched % 100 == 0:
                found = sum(1 for v in cache.values() if v)
                print(f"  [{fetched:5d}] fetched  |  {found} with dates")
            if fetched % SAVE_EVERY == 0:
                save_checkpoint(cache)
            time.sleep(RATE_LIMIT)
        except Exception as e:
            errors += 1
            cache[mbid] = None
            print(f"  ERROR {mbid}: {e}")
            time.sleep(RATE_LIMIT * 4)

    save_checkpoint(cache)
    print(f"\nDone fetching. {fetched} fetched, {errors} errors.\n")

    # Apply: use first-release-date year; only update if it differs
    updated = no_date = 0
    for song in songs:
        mbid = song.get("mbid")
        if not mbid:
            continue
        first_release = cache.get(mbid)
        if not first_release:
            no_date += 1
            continue
        try:
            first_year = int(first_release[:4])  # guard against MB's '????' unknown dates
        except ValueError:
            no_date += 1
            continue
        if song.get("release_year") != first_year:
            song["release_year"] = first_year
            updated += 1

    now_with_year = sum(1 for s in songs if s.get("release_year"))
    print(f"Release years updated: {updated}")
    print(f"MBIDs with no date:    {no_date}")
    print(f"Total with year:       {now_with_year} / {len(songs)}")

    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written to {SONGS_PATH}")


if __name__ == "__main__":
    main()
