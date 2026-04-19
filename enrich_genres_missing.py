#!/usr/bin/env python3
"""
Three-pass genre enrichment for songs still missing a genre label.

Pass 1 — Artist inference:
    For each ungenred song, look at all songs by the same artist
    (normalized key) that already have a genre. Assign the most common
    genre found. Single data point is enough for very obscure artists.

Pass 2 — Last.fm artist.getTopTags:
    Re-query Last.fm for still-ungenred songs using relaxed thresholds
    (any tag count, vs the original min_count=10). Caches per-artist
    results to lastfm_missing_cache.json. Skips artists already cached.

Pass 3 — Claude Haiku batch classification:
    For songs still without genre after passes 1 and 2, send batches of
    50 to Claude Haiku to classify from the canonical genre list.
    Requires ANTHROPIC_API_KEY env var; skipped automatically if not set.

Writes directly to explorer/public/songs.json (backs up to .bak first).

Usage:
    python3 enrich_genres_missing.py              # all passes
    python3 enrich_genres_missing.py --dry-run    # counts only, no writes
    python3 enrich_genres_missing.py --skip-lastfm --skip-claude
    python3 enrich_genres_missing.py --skip-claude
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

HERE          = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH    = os.path.join(HERE, "explorer/public/songs.json")
SONGS_BACKUP  = SONGS_PATH + ".bak"
CACHE_PATH    = os.path.join(HERE, "lastfm_missing_cache.json")
LASTFM_KEY    = os.environ.get("LASTFM_API_KEY", "68aae586eac1ab54f7cf77fa6ca9f9a7")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DRY_RUN      = "--dry-run"     in sys.argv
SKIP_LASTFM  = "--skip-lastfm" in sys.argv
SKIP_CLAUDE  = "--skip-claude" in sys.argv
RATE_LIMIT   = 0.27   # ~3.7 req/sec, comfortably under Last.fm's 5/sec
CLAUDE_BATCH = 50

# ── Genre constants ───────────────────────────────────────────────────────────

CANONICAL = {
    "rock", "classic rock", "soul", "pop", "country", "new wave", "folk",
    "jazz", "blues", "indie", "comedy", "rockabilly", "progressive rock",
    "funk", "punk", "electronic", "alternative", "reggae", "bluegrass",
    "disco", "metal", "hip-hop", "world", "classical", "soundtrack",
}

# Raw tag → canonical genre (mirrors normalize_genres.py)
MAPPING: dict[str, str] = {
    # rock family
    "hard rock": "rock", "art rock": "rock", "garage rock": "rock",
    "garage": "rock", "pub rock": "rock", "surf rock": "rock", "surf": "rock",
    "southern rock": "rock", "soft rock": "rock", "piano rock": "rock",
    "pop rock": "rock", "pop/rock": "rock", "rock and roll": "rock",
    "rock n roll": "rock", "rock'n'roll": "rock", "rock & roll": "rock",
    "beat": "rock", "oldies": "rock", "british invasion": "rock", "mod": "rock",
    "skiffle": "rock", "glam": "rock", "glam rock": "rock",
    # classic rock
    "aor": "classic rock", "arena rock": "classic rock",
    # progressive rock
    "prog rock": "progressive rock", "progressive": "progressive rock",
    "space rock": "progressive rock", "jazz rock": "progressive rock",
    "jazz-rock": "progressive rock", "krautrock": "progressive rock",
    "post-rock": "progressive rock", "psychedelic rock": "progressive rock",
    "psychedelic": "progressive rock", "psych": "progressive rock",
    # blues
    "blues rock": "blues", "country blues": "blues",
    "rhythm and blues": "blues", "delta blues": "blues", "swamp pop": "blues",
    # soul
    "northern soul": "soul", "motown": "soul", "country soul": "soul",
    "r&b": "soul", "rnb": "soul", "gospel": "soul",
    # pop
    "chamber pop": "pop", "sunshine pop": "pop", "baroque pop": "pop",
    "art pop": "pop", "dream pop": "pop", "bubblegum": "pop",
    "teen pop": "pop", "easy listening": "pop", "lounge": "pop",
    "easy": "pop", "doo wop": "pop", "doo-wop": "pop", "doowop": "pop",
    "k-pop": "pop", "j-pop": "pop",
    # country
    "alt-country": "country", "alternative country": "country",
    "country rock": "country", "country pop": "country",
    "outlaw country": "country", "classic country": "country",
    "western": "country", "western swing": "country", "tex-mex": "country",
    "americana": "country", "zydeco": "country", "cajun": "country",
    "yodel": "country",
    # folk
    "folk rock": "folk", "folk pop": "folk", "indie folk": "folk",
    "english folk": "folk", "anti-folk": "folk", "celtic": "folk",
    "celtic rock": "folk", "irish": "folk", "singer-songwriter": "folk",
    "sea shanty": "folk", "psychedelic folk": "folk",
    "acoustic": "folk",
    # jazz
    "swing": "jazz", "bebop": "jazz", "gypsy jazz": "jazz",
    "smooth jazz": "jazz", "vocal jazz": "jazz", "acid jazz": "jazz",
    "jazz fusion": "jazz", "latin jazz": "jazz", "dixieland": "jazz",
    "ragtime": "jazz", "cabaret": "jazz", "big band": "jazz",
    "bossa nova": "jazz", "chanson": "jazz", "electro-swing": "jazz",
    # new wave
    "synthpop": "new wave", "post-punk": "new wave", "electropop": "new wave",
    "synth-pop": "new wave", "synthwave": "new wave", "new romantic": "new wave",
    "ebm": "new wave",
    # punk
    "punk rock": "punk", "proto-punk": "punk", "hardcore punk": "punk",
    "post-hardcore": "punk", "hardcore": "punk", "oi": "punk",
    "ska punk": "punk", "screamo": "punk", "celtic punk": "punk",
    "no wave": "punk",
    # metal
    "heavy metal": "metal", "thrash metal": "metal", "black metal": "metal",
    "death metal": "metal", "progressive metal": "metal", "power metal": "metal",
    "nu metal": "metal", "grindcore": "metal", "alternative metal": "metal",
    "doom metal": "metal", "folk metal": "metal", "sludge": "metal",
    # electronic
    "techno": "electronic", "house": "electronic", "ambient": "electronic",
    "trip-hop": "electronic", "chillout": "electronic", "trance": "electronic",
    "dance": "electronic", "drum n bass": "electronic", "dubstep": "electronic",
    "industrial": "electronic", "shoegaze": "electronic", "electro": "electronic",
    "eurodance": "electronic", "lo-fi": "electronic",
    # hip-hop
    "hip hop": "hip-hop", "rap": "hip-hop", "grime": "hip-hop",
    "nerdcore": "hip-hop",
    # indie / alternative
    "indie rock": "indie", "indie pop": "indie", "bedroom pop": "indie",
    "twee": "indie", "alternative rock": "alternative", "britpop": "alternative",
    "grunge": "alternative", "shoegazing": "alternative",
    # reggae
    "ska": "reggae", "dub": "reggae", "rocksteady": "reggae",
    "dancehall": "reggae", "skinhead reggae": "reggae", "mento": "reggae",
    "early reggae": "reggae", "calypso": "world",
    # disco / funk
    "funk rock": "funk",
    # world
    "world music": "world", "latin": "world", "afrobeat": "world",
    "african": "world", "samba": "world", "salsa": "world",
    "mambo": "world", "tango": "world", "polka": "world", "mariachi": "world",
    "ye-ye": "world", "qawwali": "world",
    # classical
    "orchestral": "classical", "baroque": "classical", "opera": "classical",
    "early music": "classical", "classical guitar": "classical",
    # comedy
    "comedian": "comedy", "novelty": "comedy", "parody": "comedy",
    "satire": "comedy", "humor": "comedy", "stand-up": "comedy",
    # rockabilly
    "psychobilly": "rockabilly", "neo-rockabilly": "rockabilly",
    "neo-swing": "rockabilly",
    # soundtrack
    "soundtracks": "soundtrack", "musical": "soundtrack",
    "broadway": "soundtrack", "disney": "soundtrack",
    "musical theater": "soundtrack", "film score": "soundtrack",
    "score": "soundtrack",
    # bluegrass (already canonical, just mapping variants)
    "bluegrass": "bluegrass",
}

# Tags to skip — not genre information
SKIP = {
    "seen live", "favorites", "favourite", "love", "awesome", "beautiful",
    "classic", "best", "great", "good", "all time favorites",
    "40s", "50s", "60s", "60's", "70s", "70's", "80s", "90s",
    "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s",
    "2000s", "2010s",
    "new zealand", "australia", "uk", "usa", "american", "british",
    "canadian", "australian", "german", "french", "swedish",
    "heard on matinee idle", "rnz", "radio nz",
    "spoken word", "poetry", "speech", "christmas", "new age",
    "instrumental", "music", "independent", "experimental",
}


def tag_to_genre(raw: str) -> str | None:
    t = raw.lower().strip()
    if t in CANONICAL:
        return t
    if t in SKIP:
        return None
    if t in MAPPING:
        return MAPPING[t]
    # Keyword fallbacks (order matters — more specific first)
    pairs = [
        ("hip hop", "hip-hop"), ("hip-hop", "hip-hop"), (" rap", "hip-hop"),
        ("metal", "metal"), ("punk", "punk"), ("jazz", "jazz"),
        ("blues", "blues"), ("folk", "folk"), ("country", "country"),
        ("classical", "classical"), ("orchestr", "classical"),
        ("reggae", "reggae"), ("ska", "reggae"),
        ("soul", "soul"), ("funk", "funk"), ("disco", "disco"),
        ("electronic", "electronic"), ("techno", "electronic"),
        ("synth", "new wave"), ("electro", "electronic"),
        ("rock", "rock"), ("pop", "pop"),
        ("comedy", "comedy"), ("humou", "comedy"), ("humor", "comedy"),
        ("world", "world"), ("latin", "world"),
        ("soundtrack", "soundtrack"), ("musical", "soundtrack"),
        ("broadway", "soundtrack"),
    ]
    for kw, genre in pairs:
        if kw in t:
            return genre
    return None


def normalize_artist(name: str) -> str:
    """Aggressive normalize — matches Explorer.tsx behaviour."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ── Pass 1: Artist-level inference ───────────────────────────────────────────

def pass1_artist_inference(songs: list) -> int:
    # Build genre frequency per normalized artist from the existing genred songs
    artist_genres: dict[str, Counter] = {}
    for s in songs:
        if s.get("genre"):
            key = normalize_artist(s["artist"])
            artist_genres.setdefault(key, Counter())[s["genre"]] += 1

    assigned = 0
    for s in songs:
        if s.get("genre"):
            continue
        key = normalize_artist(s["artist"])
        counts = artist_genres.get(key)
        if not counts:
            continue
        s["genre"] = counts.most_common(1)[0][0]
        assigned += 1
    return assigned


# ── Pass 2: Last.fm artist.getTopTags (relaxed thresholds) ───────────────────

def _fetch_artist_tags(artist: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": LASTFM_KEY,
        "format": "json",
        "autocorrect": 1,
    })
    req = urllib.request.Request(
        f"https://ws.audioscrobbler.com/2.0/?{params}",
        headers={"User-Agent": "MatineeIdleArchive/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return []
        raise
    if "error" in data:
        return []
    tags = data.get("toptags", {}).get("tag", [])
    return tags if isinstance(tags, list) else [tags]


def _best_genre_from_tags(tags: list[dict]) -> str | None:
    for tag in tags:
        genre = tag_to_genre(tag.get("name", ""))
        if genre:
            return genre
    return None


def pass2_lastfm(songs: list) -> int:
    cache: dict[str, str | None] = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            cache = json.load(f)

    # Collect unique artists still needing genre that aren't cached yet
    need: list[str] = []
    seen_keys: set[str] = set()
    for s in songs:
        if s.get("genre"):
            continue
        key = s["artist"].lower().strip()
        if key not in cache and key not in seen_keys:
            need.append(s["artist"])
            seen_keys.add(key)

    print(f"  Last.fm: {len(need)} unique artists to query "
          f"({len(cache)} already cached)")

    if DRY_RUN:
        mins = int(len(need) * RATE_LIMIT / 60)
        print(f"  (dry-run) ETA ~{mins} min at {1/RATE_LIMIT:.1f} req/sec")
        return 0

    fetched = 0
    for artist in need:
        key = artist.lower().strip()
        try:
            tags = _fetch_artist_tags(artist)
            cache[key] = _best_genre_from_tags(tags)
            fetched += 1
            if fetched % 100 == 0:
                found = sum(1 for v in cache.values() if v)
                pct = 100 * found / len(cache) if cache else 0
                print(f"    [{fetched:4d}/{len(need)}]  {found} genres found ({pct:.0f}% hit rate)")
                with open(CACHE_PATH, "w") as f:
                    json.dump(cache, f)
        except Exception as e:
            cache[key] = None
            print(f"    ERROR {artist!r}: {e}")
            time.sleep(RATE_LIMIT * 4)
        time.sleep(RATE_LIMIT)

    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)
    print(f"  Last.fm done: {fetched} new queries")

    assigned = 0
    for s in songs:
        if s.get("genre"):
            continue
        genre = cache.get(s["artist"].lower().strip())
        if genre:
            s["genre"] = genre
            assigned += 1
    return assigned


# ── Pass 3: Claude Haiku batch classification ─────────────────────────────────

_GENRE_LIST = ", ".join(sorted(CANONICAL))
_SYSTEM = (
    f"You are a music genre classifier. Classify each song into exactly one of "
    f"these genres: {_GENRE_LIST}.\n\n"
    "Respond with ONLY a valid JSON array of genre strings, one per song in the "
    "same order as the input. No markdown, no explanation."
)


def _claude_batch(batch: list[dict]) -> list[str | None]:
    items = [
        {
            "artist": s["artist"],
            "title": s["title"],
            "year": s.get("release_year") or s.get("air_year"),
        }
        for s in batch
    ]
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "system": _SYSTEM,
        "messages": [
            {"role": "user", "content": f"Classify these {len(items)} songs:\n{json.dumps(items, ensure_ascii=False)}"}
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
    text = data["content"][0]["text"].strip()
    # Strip any markdown fences Claude might add despite instructions
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    raw = json.loads(text)
    return [
        (g.lower().strip() if g and g.lower().strip() in CANONICAL else None)
        for g in raw
    ]


def pass3_claude(songs: list) -> int:
    ungenred = [s for s in songs if not s.get("genre")]
    total = len(ungenred)
    print(f"  Claude: {total} songs  →  {(total + CLAUDE_BATCH - 1) // CLAUDE_BATCH} batches")

    if DRY_RUN:
        return 0
    if not total:
        return 0

    assigned = errors = 0
    for i in range(0, total, CLAUDE_BATCH):
        batch = ungenred[i : i + CLAUDE_BATCH]
        try:
            genres = _claude_batch(batch)
            for song, genre in zip(batch, genres):
                if genre:
                    song["genre"] = genre
                    assigned += 1
            done = min(i + CLAUDE_BATCH, total)
            print(f"  [{done:4d}/{total}]  batch done  ({assigned} assigned so far)")
            time.sleep(0.5)
        except Exception as e:
            errors += 1
            print(f"  ERROR batch {i}–{i + len(batch)}: {e}")
            time.sleep(5)

    if errors:
        print(f"  {errors} batch error(s) — those songs stay ungenred")
    return assigned


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Reading {SONGS_PATH}")
    with open(SONGS_PATH) as f:
        songs = json.load(f)

    before = sum(1 for s in songs if s.get("genre"))
    missing_before = len(songs) - before
    print(f"Songs total: {len(songs)}  |  with genre: {before}  |  missing: {missing_before}\n")

    if not DRY_RUN:
        with open(SONGS_BACKUP, "w") as f:
            json.dump(songs, f, separators=(",", ":"))
        print(f"Backup → {SONGS_BACKUP}\n")

    # ── Pass 1 ──────────────────────────────────────────────────────────────
    print("── Pass 1: Artist inference ──────────────────────────────────────")
    p1 = pass1_artist_inference(songs)
    after1 = sum(1 for s in songs if s.get("genre"))
    print(f"  Assigned: {p1}  |  have genre: {after1}  |  still missing: {len(songs) - after1}\n")

    # ── Pass 2 ──────────────────────────────────────────────────────────────
    if SKIP_LASTFM:
        print("── Pass 2: Last.fm ─ SKIPPED ─────────────────────────────────────\n")
        p2 = 0
    else:
        print("── Pass 2: Last.fm artist.getTopTags ─────────────────────────────")
        p2 = pass2_lastfm(songs)
        after2 = sum(1 for s in songs if s.get("genre"))
        print(f"  Assigned: {p2}  |  have genre: {after2}  |  still missing: {len(songs) - after2}\n")

    # ── Pass 3 ──────────────────────────────────────────────────────────────
    if SKIP_CLAUDE or not ANTHROPIC_KEY:
        label = "SKIPPED" if SKIP_CLAUDE else "no ANTHROPIC_API_KEY"
        print(f"── Pass 3: Claude ─ {label} ──────────────────────────────────────\n")
        p3 = 0
    else:
        print("── Pass 3: Claude Haiku batch classification ─────────────────────")
        p3 = pass3_claude(songs)
        after3 = sum(1 for s in songs if s.get("genre"))
        print(f"  Assigned: {p3}  |  have genre: {after3}  |  still missing: {len(songs) - after3}\n")

    # ── Summary ─────────────────────────────────────────────────────────────
    after = sum(1 for s in songs if s.get("genre"))
    print("── Summary ───────────────────────────────────────────────────────")
    print(f"  Pass 1 (artist inference) : {p1:5d}")
    print(f"  Pass 2 (Last.fm)          : {p2:5d}")
    print(f"  Pass 3 (Claude)           : {p3:5d}")
    print(f"  Total assigned            : {p1 + p2 + p3:5d}")
    print(f"  Before → After: {before} → {after}  |  still missing: {len(songs) - after}")

    if DRY_RUN:
        print("\n--dry-run: no files written.")
        return

    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))
    print(f"\nWritten to {SONGS_PATH}")


if __name__ == "__main__":
    main()
