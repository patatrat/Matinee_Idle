#!/usr/bin/env python3
"""
Fetch release_year from Spotify for songs that have a spotify_url but no release_year.
Uses GET /tracks/{id} (individual endpoint — batch endpoint requires elevated access).

For genre enrichment of "unmatched" songs, use enrich_genres_missing.py instead,
which uses Last.fm and doesn't hit Spotify's artist endpoint rate limits.

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

HERE       = os.path.dirname(os.path.abspath(__file__))
SONGS_PATH = os.path.join(HERE, "explorer/public/songs.json")
SONGS_BACK = SONGS_PATH + ".bak"

CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID",     "f3bcd797aeaa4a50bcb6132366835d64")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "30e26fd9d30844d08b94dced12fe380d")

RATE_LIMIT    = 0.6    # seconds between API calls
MAX_WAIT      = 300    # abort if Retry-After exceeds this (save progress and exit)
SAVE_EVERY    = 250    # checkpoint to disk every N songs
DRY_RUN       = "--dry-run" in sys.argv


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


def spotify_get(path: str) -> dict | None:
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
                    print(f"  Rate limited with Retry-After={retry_after}s (>{MAX_WAIT}s cap) — saving and exiting")
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


def save(songs: list) -> None:
    shutil.copy(SONGS_PATH, SONGS_BACK)
    with open(SONGS_PATH, "w") as f:
        json.dump(songs, f, separators=(",", ":"))


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    songs = json.load(open(SONGS_PATH))
    by_id = {s["id"]: s for s in songs}

    targets = [(s["id"], track_id_from_url(s["spotify_url"]))
               for s in songs
               if s.get("spotify_url") and not s.get("release_year")]
    targets = [(sid, tid) for sid, tid in targets if tid]

    print(f"Songs missing release_year with a Spotify URL: {len(targets)}")

    if DRY_RUN:
        print("Dry run — exiting.")
        return

    year_updates = 0
    print(f"Fetching track data ({len(targets)} songs, ~{len(targets)*RATE_LIMIT/60:.0f} min) …")

    for i, (song_id, track_id) in enumerate(targets):
        try:
            track = spotify_get(f"/tracks/{track_id}")
        except SystemExit:
            print(f"  Saving progress at song {i+1} before exit …")
            save(songs)
            print(f"  Saved. +{year_updates} release years so far.")
            raise

        if track:
            yr = release_year_from_date(track.get("album", {}).get("release_date", ""))
            if yr:
                by_id[song_id]["release_year"] = yr
                year_updates += 1

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(targets)} — +{year_updates} years filled")

        if (i + 1) % SAVE_EVERY == 0:
            save(songs)
            print(f"  Checkpoint saved at {i+1} songs")

        time.sleep(RATE_LIMIT)

    save(songs)
    print(f"\nDone. release_year filled: {year_updates} / {len(targets)}")


if __name__ == "__main__":
    main()
