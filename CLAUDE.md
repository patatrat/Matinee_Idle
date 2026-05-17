# Matinee Idle Song Explorer

**Project Status:** Complete (data pipeline done, explorer live)
**Last Updated:** May 2026
**Hosted on:** radomski.co.nz (Vercel)

---

## Project Summary

An interactive data explorer for 21 years of Radio New Zealand's Matinee Idle (2005–2026), hosted by Phil O'Brien and Simon Morris. The complete RNZ archive of songs has been scraped, enriched with metadata, and made browsable via a Next.js web app.

**Dataset:** 15,411 songs · 5,722 unique artists · 100% genre coverage

---

## What's Done

### Data pipeline (complete)
- Scraped full RNZ archive (artist, title, air date)
- Normalised 140+ artist name inconsistencies
- Enriched via Spotify, Last.fm, MusicBrainz, Discogs
- Final genre classification via DeepSeek AI for ~2,300 unmatched songs
- **Genre coverage: 100%** — all 15,411 songs have a genre
- **Release year coverage: ~83%** — very obscure/undated recordings account for the gap
- All enrichment workflows are set to manual-trigger only (enrichment is complete)

### Web explorer (live at radomski.co.nz)
- Full-text search by artist and title
- Filter by genre, decade, release year, air year
- Sort by times played, date played, date released
- Song cards with Spotify embed/preview
- Artists view (ranked by times played)
- Covers view (same song, 4+ distinct artists)
- Stats view with charts (genre distribution, top artists, timeline)
- Random song discovery
- Amber radio tower favicon, dark theme
- Umami analytics

### Blog post
- Draft at `blog-post-draft.md` — ready to publish

---

## Architecture

### Data
- **Source of truth:** `explorer/public/songs.json` — static JSON, committed to repo
- No database required at runtime
- Supabase was used during development but is no longer needed

### Frontend (`explorer/`)
- Next.js 16 App Router
- Tailwind CSS
- Recharts (stats charts)
- Spotify on-demand lookup via `/api/spotify` server route
- Static site — all data loaded from `public/songs.json` at runtime

### Key files
```
explorer/app/components/Explorer.tsx    # Main app component (~660 lines)
explorer/app/components/SongCard.tsx    # Song card with Spotify embed
explorer/app/components/FilterSidebar.tsx
explorer/app/components/StatsView.tsx
explorer/app/api/spotify/route.ts       # Server-side Spotify lookup
explorer/app/layout.tsx                 # Metadata, analytics
explorer/app/icon.svg                   # Amber radio tower favicon
explorer/public/songs.json             # Full dataset
```

### Environment variables (Vercel)
- `SPOTIFY_CLIENT_ID` — Spotify app credentials for on-demand lookup
- `SPOTIFY_CLIENT_SECRET`

---

## Enrichment scripts (reference only — pipeline complete)

| Script | Purpose |
|--------|---------|
| `extract_songs.py` | Scrape RNZ archive |
| `enrich_spotify.py` | Spotify URI + popularity |
| `enrich_spotify_metadata.py` | Spotify release year + genre backfill |
| `enrich_genres_lastfm.py` | Last.fm genre tags |
| `enrich_genres_mb.py` | MusicBrainz genre |
| `enrich_genres_missing.py` | Artist inference + DeepSeek AI classification |
| `enrich_release_years_discogs.py` | Discogs release years |
| `fix_release_years.py` | MusicBrainz first-release-date fix |
| `normalize_genres.py` | Canonical genre mapping (25 genres) |

### Canonical genres (25 total)
rock, classic rock, soul, pop, country, new wave, folk, jazz, blues, indie,
comedy, rockabilly, progressive rock, funk, punk, electronic, alternative,
reggae, bluegrass, disco, metal, hip-hop, world, classical, soundtrack

---

## GitHub Actions (all manual-trigger only)

| Workflow | Purpose |
|----------|---------|
| `enrich-spotify-daily.yml` | Spotify enrichment (cron removed — complete) |
| `enrich-spotify-metadata.yml` | Spotify metadata backfill |
| `enrich-release-years-discogs.yml` | Discogs release years |
| `fix-release-years.yml` | MusicBrainz release year fix |

---

## Data quality notes

- Most-played song: *Cousin Mosquito* by Congresswoman Malinda Jackson Parker (16 plays), found under 4 different name spellings
- 63% of artists (3,620) appeared exactly once
- Oldest song: Fred Astaire — *Puttin' on the Ritz* (1930)
- Simon Morris played his own songs on his own show multiple times; these are uncatalogued in any database
