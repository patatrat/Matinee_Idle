#!/usr/bin/env python3
"""
Enrich release years using Discogs master release data.

For each unique (artist, title) pair, searches Discogs for a master release
(the canonical original recording) and takes its year. Master releases on
Discogs represent the original release, not compilations or remasters.

Strategy:
  1. Search type=master first (most accurate — original releases only)
  2. Fallback to type=release and take the earliest year found

Cache key: normalize(artist)|||normalize(title)
Cache file: discogs_year_cache.json

Usage:
    python3 enrich_release_years_discogs.py [--dry-run] [--apply-only]

    --dry-run    Show stats and sample, don't fetch or write
    --apply-only Skip fetching, just apply the existing cache to songs.json

Set DISCOGS_TOKEN env var for higher rate limit (60/min vs 25/min).
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

HERE        = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH  = os.path.join(HERE, "explorer/public/songs.json")
CACHE_PATH  = os.path.join(HERE, "discogs_year_cache.json")
DISCOGS_URL = "https://api.discogs.com/database/search"
SAVE_EVERY  = 100

DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN", "")
# Discogs rate limits: 25/min unauth, 60/min with token
# Use conservative values to avoid 429s
RATE_LIMIT = 1.1 if DISCOGS_TOKEN else 2.5

DRY_RUN    = "--dry-run"    in sys.argv
APPLY_ONLY = "--apply-only" in sys.argv


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def normalize(s: str) -> str:
    """Lowercase, strip non-alphanumeric for fuzzy key matching."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def cache_key(artist: str, title: str) -> str:
    return f"{normalize(artist)}|||{normalize(title)}"


def artist_matches(result_title: str, query_artist: str) -> bool:
    """Loose check: normalised query artist appears in normalised result title."""
    na = normalize(query_artist)
    nt = normalize(result_title)
    # Accept if at least 80% of the query artist chars appear in the result
    if not na:
        return False
    if na in nt:
        return True
    # Check first word of artist
    first = normalize(query_artist.split()[0]) if query_artist.split() else ""
    return bool(first) and first in nt and len(first) >= 3


# ---------------------------------------------------------------------------
# Discogs search
# ---------------------------------------------------------------------------

def _build_req(params: dict) -> urllib.request.Request:
    qs  = urllib.parse.urlencode(params)
    url = f"{DISCOGS_URL}?{qs}"
    headers = {
        "User-Agent": "MatineeIdleArchive/1.0 +https://radomski.co.nz",
    }
    if DISCOGS_TOKEN:
        headers["Authorization"] = f"Discogs token={DISCOGS_TOKEN}"
    return urllib.request.Request(url, headers=headers)


def _get_json(req: urllib.request.Request, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "60"))
                print(f"  Rate limited — sleeping {wait}s…", flush=True)
                time.sleep(wait)
                continue
            if e.code in (400, 404):
                return None
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  HTTP {e.code} on {req.full_url[:80]}", flush=True)
            return None
        except Exception as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  Error: {exc}", flush=True)
            return None
    return None


def fetch_year(artist: str, title: str) -> int | None:
    """Return best-guess original release year from Discogs, or None."""

    # --- Strategy 1: master releases ---
    params = {
        "artist": artist,
        "track":  title,
        "type":   "master",
        "per_page": 5,
    }
    data = _get_json(_build_req(params))
    if data:
        results = data.get("results", [])
        years = []
        for r in results:
            year = r.get("year")
            if not year:
                continue
            try:
                y = int(year)
            except (ValueError, TypeError):
                continue
            if y < 1900 or y > 2030:
                continue
            # Loose artist match against result title field
            result_title = r.get("title", "")
            if artist_matches(result_title, artist):
                years.append(y)
        if years:
            return min(years)

    # --- Strategy 2: any release, take earliest ---
    params["type"] = "release"
    params["per_page"] = 10
    data = _get_json(_build_req(params))
    if data:
        results = data.get("results", [])
        years = []
        for r in results:
            year = r.get("year")
            if not year:
                continue
            try:
                y = int(year)
            except (ValueError, TypeError):
                continue
            if y < 1900 or y > 2030:
                continue
            result_title = r.get("title", "")
            if artist_matches(result_title, artist):
                years.append(y)
        if years:
            return min(years)

    return None


# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    songs = json.load(open(SONGS_PATH))

    # Unique (artist, title) pairs preserving first occurrence order
    seen: dict[str, tuple[str, str]] = {}
    for s in songs:
        k = cache_key(s["artist"], s["title"])
        if k not in seen:
            seen[k] = (s["artist"], s["title"])
    unique_pairs = list(seen.values())

    print(f"Total songs:           {len(songs)}")
    print(f"Unique (artist,title): {len(unique_pairs)}")
    print(f"Rate limit:            {RATE_LIMIT}s/req  ({'with token' if DISCOGS_TOKEN else 'no token'})")

    if DRY_RUN:
        impossible = [
            s for s in songs
            if s.get("release_year") and s.get("air_year")
            and s["release_year"] > s["air_year"]
        ]
        no_year = [s for s in songs if not s.get("release_year")]
        print(f"\nImpossible dates (release > air): {len(impossible)}")
        print(f"No release year:                  {len(no_year)}")
        print(f"\nSample impossible dates:")
        for s in impossible[:15]:
            print(f"  {s['artist']} — {s['title']}")
            print(f"    release_year={s['release_year']}  air_year={s['air_year']}")
        eta_h = len(unique_pairs) * RATE_LIMIT / 3600
        print(f"\n--dry-run: would fetch {len(unique_pairs)} pairs.")
        print(f"ETA at {RATE_LIMIT}s/req: ~{eta_h:.1f} hours")
        return

    # -------------------------------------------------------------------
    # Fetch phase
    # -------------------------------------------------------------------
    if not APPLY_ONLY:
        cache = load_cache()
        to_fetch = [p for p in unique_pairs if cache_key(*p) not in cache]
        cached_count = len(cache)
        total_to_fetch = len(to_fetch)

        print(f"Cached:                {cached_count}")
        print(f"To fetch:              {total_to_fetch}")
        eta_h = total_to_fetch * RATE_LIMIT / 3600
        print(f"ETA:                   ~{eta_h:.1f} hours\n")

        fetched = errors = matched = 0
        start_time = time.time()

        def _save_and_report():
            save_cache(cache)
            elapsed   = time.time() - start_time
            rate      = fetched / elapsed if elapsed > 0 else 0
            remaining = (total_to_fetch - fetched) / rate if rate > 0 else 0
            hit_rate  = matched / fetched * 100 if fetched > 0 else 0
            print(
                f"  [{fetched:5d}/{total_to_fetch}] "
                f"matched={matched} ({hit_rate:.0f}%)  "
                f"errors={errors}  "
                f"elapsed={elapsed/60:.1f}m  "
                f"ETA={remaining/60:.0f}m",
                flush=True,
            )

        try:
            for artist, title in to_fetch:
                k = cache_key(artist, title)
                try:
                    year = fetch_year(artist, title)
                    cache[k] = year
                    fetched += 1
                    if year is not None:
                        matched += 1
                except Exception as exc:
                    errors += 1
                    cache[k] = None
                    print(f"  ERROR {artist!r} / {title!r}: {exc}", flush=True)

                if fetched % SAVE_EVERY == 0:
                    _save_and_report()

                time.sleep(RATE_LIMIT)

        except KeyboardInterrupt:
            print("\nInterrupted — saving checkpoint…", flush=True)
        finally:
            save_cache(cache)
            elapsed = time.time() - start_time
            hit_rate = matched / fetched * 100 if fetched > 0 else 0
            print(
                f"\nFetch done. fetched={fetched}  matched={matched} ({hit_rate:.0f}%)"
                f"  errors={errors}  elapsed={elapsed/60:.1f}m",
                flush=True,
            )
    else:
        cache = load_cache()
        print(f"Cached entries:        {len(cache)}  (--apply-only, skipping fetch)")

    # -------------------------------------------------------------------
    # Apply phase
    # -------------------------------------------------------------------
    print("\nApplying Discogs years…", flush=True)

    cleared = updated = skipped_no_data = skipped_older = 0

    for song in songs:
        artist    = song.get("artist", "")
        title     = song.get("title", "")
        air_year  = song.get("air_year")
        cur_year  = song.get("release_year")

        # Step 1: clear impossible dates (release_year > air_year)
        if cur_year and air_year and cur_year > air_year:
            song["release_year"] = None
            cleared += 1
            cur_year = None

        # Step 2: apply Discogs year if we have one
        k = cache_key(artist, title)
        discogs_year = cache.get(k)

        if not discogs_year:
            skipped_no_data += 1
            continue

        # Sanity: don't use a year newer than the song's air year
        if air_year and discogs_year > air_year:
            skipped_no_data += 1
            continue

        # Only update if Discogs year is earlier (more original) or we had no year
        if cur_year is None or discogs_year < cur_year:
            song["release_year"] = discogs_year
            updated += 1
        else:
            skipped_older += 1

    now_with_year = sum(1 for s in songs if s.get("release_year"))
    print(f"Impossible dates cleared:   {cleared}")
    print(f"Songs updated:              {updated}")
    print(f"Skipped (no Discogs data):  {skipped_no_data}")
    print(f"Skipped (Discogs not earlier): {skipped_older}")
    print(f"Total with release year:    {now_with_year} / {len(songs)}")

    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"Written → {SONGS_PATH}", flush=True)


if __name__ == "__main__":
    main()
