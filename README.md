# Matinee Idle Archive

An interactive data explorer for 21 years of Radio New Zealand's legendary summer music show (2005–2026), hosted by Phil O'Brien and Simon Morris.

**Live site:**[Matinee Idle](https://matineeidle.radomski.co.nz/)
**Blog post** [radomski.co.nz](https://radomski.co.nz/blog/matinee-idle/)

---

## What this is

Matinee Idle was a summer fill-in show on RNZ National that ran for 21 years, playing rare, obscure, divisive, and forgotten songs. This project scrapes the complete RNZ archive, enriches it with metadata from Spotify, Last.fm, MusicBrainz, and Discogs, and makes it browsable.

**Dataset:** 15,411 songs · 5,722 unique artists · 100% genre coverage

---

## Repository layout

```
/
├── explorer/                  # Next.js web app (deployed to Vercel)
│   ├── app/
│   │   ├── components/        # Explorer, SongCard, FilterSidebar, StatsView
│   │   ├── api/spotify/       # Server-side Spotify lookup route
│   │   └── layout.tsx / page.tsx
│   └── public/songs.json      # Full enriched dataset (source of truth)
│
├── enrich_spotify.py          # Spotify URI + popularity enrichment
├── enrich_spotify_metadata.py # Spotify release year + genre backfill
├── enrich_genres_lastfm.py    # Last.fm genre enrichment
├── enrich_genres_mb.py        # MusicBrainz genre enrichment
├── enrich_genres_missing.py   # Final pass: artist inference + DeepSeek classification
├── enrich_release_years_discogs.py  # Discogs release year enrichment
├── fix_release_years.py       # MusicBrainz first-release-date fix
├── normalize_genres.py        # Canonical genre mapping
├── extract_songs.py           # RNZ archive scraper
│
├── .github/workflows/         # All enrichment workflows (manual trigger only)
└── blog-post-draft.md         # Blog post draft for publication
```

---

## Data enrichment pipeline

Enrichment is complete. All scripts are kept for reference; workflows are set to manual-trigger only.

| Source | Fields enriched |
|--------|----------------|
| Spotify | URI, popularity, preview URL, release year |
| Last.fm | Genre tags, play counts |
| MusicBrainz | Release year (first-release-date) |
| Discogs | Release year |
| DeepSeek AI | Genre classification for remaining ~2,300 unmatched songs |

---

## Running the explorer locally

```bash
cd explorer
cp .env.local.example .env.local
# fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Deployment

Deployed via Vercel. Set the following environment variables in the Vercel dashboard:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

The dataset (`explorer/public/songs.json`) is static — no database required at runtime.

---

## Data notes

- **Genre coverage:** 100% (15,411/15,411 songs)
- **Release year coverage:** ~83% (12,830/15,411 songs) — very obscure or undated recordings account for the gap
- **Artist name normalisation:** 140+ inconsistencies cleaned (e.g. "BIlly Bragg", "Dr Hook" vs "Dr. Hook")
- Songs without Spotify matches are flagged; the on-demand lookup API handles these at browse-time
