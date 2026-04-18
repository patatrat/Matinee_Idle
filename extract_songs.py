import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

COLUMNS = [
    "show_date", "artist", "title", "broadcast_date",
    "spotify_track_id", "spotify_artist_id", "spotify_match_confidence",
    "spotify_popularity", "spotify_preview_url",
    "mb_recording_id", "mb_work_id", "mb_release_year", "mb_match_confidence",
    "id", "mbid", "mb_title", "mb_artist", "mb_release",
    "enriched", "genre", "release_date", "confidence_score",
    "enrich_status", "enrich_error", "enriched_at", "enrichment_status"
]

KEEP = {
    "id", "artist", "title", "broadcast_date", "show_date",
    "spotify_track_id", "spotify_popularity", "spotify_preview_url",
    "mb_release_year", "mb_release", "genre", "release_date",
    "enrich_status"
}

def parse_val(v):
    if v == r"\N":
        return None
    if v == "t":
        return True
    if v == "f":
        return False
    return v

songs = []
in_copy = False

backups = [f for f in os.listdir(HERE) if f.endswith(".backup.gz")]
if not backups:
    sys.exit(f"ERROR: no .backup.gz file found in {HERE}")
backup_path = os.path.join(HERE, sorted(backups)[-1])
print(f"Using backup: {backup_path}", file=sys.stderr)

with gzip.open(backup_path, "rt", encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("COPY public.songs "):
            in_copy = True
            continue
        if in_copy:
            if line.strip() == "\\.":
                break
            parts = line.rstrip("\n").split("\t")
            row = {COLUMNS[i]: parse_val(parts[i]) for i in range(len(COLUMNS)) if COLUMNS[i] in KEEP}

            # extract year from broadcast_date or show_date
            if row.get("broadcast_date"):
                row["air_year"] = int(row["broadcast_date"][:4])
            else:
                m = re.search(r"\b(20\d{2})\b", row.get("show_date", ""))
                row["air_year"] = int(m.group(1)) if m else None

            # extract release year from release_date if mb_release_year missing
            if not row.get("mb_release_year") and row.get("release_date"):
                row["release_year"] = int(row["release_date"][:4])
            elif row.get("mb_release_year"):
                row["release_year"] = int(row["mb_release_year"])
            else:
                row["release_year"] = None

            # clean up redundant fields
            row.pop("mb_release_year", None)
            row.pop("release_date", None)

            # spotify url from track id
            if row.get("spotify_track_id"):
                row["spotify_url"] = f"https://open.spotify.com/track/{row['spotify_track_id']}"
            row.pop("spotify_track_id", None)

            songs.append(row)

songs.sort(key=lambda s: (s.get("broadcast_date") or "", s.get("id", 0)))

print(f"Extracted {len(songs)} songs", file=sys.stderr)

out_path = os.path.join(HERE, "songs.json")
with open(out_path, "w") as f:
    json.dump(songs, f, separators=(",", ":"))

size = len(json.dumps(songs, separators=(",", ":")))
print(f"JSON size: {size/1024/1024:.1f} MB", file=sys.stderr)
print(f"Written to {out_path}", file=sys.stderr)
