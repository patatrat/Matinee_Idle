# Matinee Idle Song Explorer

**Project Status:** Complete (data pipeline done, explorer live)
**Last Updated:** June 2026
**Hosted on:** radomski.co.nz (Vercel)

---

## Project Summary

An interactive data explorer for 21 years of Radio New Zealand's Matinee Idle (2005–2026), hosted by Phil O'Brien and Simon Morris. The complete RNZ archive of songs has been scraped, enriched with metadata, and made browsable via a Next.js web app.

**Dataset:** 15,411 songs · 5,471 unique artists · 100% genre coverage

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

## Listener analytics (Umami on Neon)

### Where the data lives
- **Neon project:** `shiny-sunset-93833202` (named `umami-analytics`), region ap-southeast-2
- **Matinee Idle website_id:** `65225d81-5bcd-43f3-8f8c-f72ad5c48d50`
- Standard Umami v2 schema: `website_event` (one row per event) joined to `event_data` (one row per event property) on `event_data.website_event_id = website_event.event_id`

### Events tracked (see Explorer.tsx, SongCard.tsx, StatsView.tsx)
| Event | Properties |
|-------|-----------|
| `song-play` | artist, title, genre, release_year, air_year |
| `search` | query text |
| `filter-genre` | genre |
| `filter-applied` | type (decade/year/sort), value |
| `chart-interaction` | chart name, clicked value |
| `spotify-lookup` | "artist – title" query (on-demand lookups for songs without a stored URI) |
| `arrival` | landing context |

### Double-counting correction (IMPORTANT for any play-count query)
- Before commit `b16d316` (deployed **2026-06-02 23:09 UTC**), manually-clicked plays fired `song-play` **twice** (click handler + `isActive` effect). Auto-advance plays fired once — so pre-fix data is NOT uniformly 2x and cannot be halved.
- **Correct fix:** drop any `song-play` repeating the same session + artist + title within **2 seconds** of the previous one. Empirically removes 400/862 pre-fix events and 1/35 post-fix (a client on stale cached JS). Always apply this dedup.

### How to re-run the analysis
1. `node analytics/first_page.js` — regenerates the app's default first page (top 50 by radio play count, replicating Explorer.tsx normalisation exactly, including its normalize-vs-normalizeArtistKey sort-lookup quirk). Writes `/tmp/first_page.json` — only needs re-running if `songs.json` or the default sort changes.
2. Run `analytics/song_plays_report.sql` against the Neon DB (via Neon MCP `run_sql` or console). It dedupes double-counts, normalises artist/title variants, tags each song as on/off the default first page, and reports plays + distinct listeners per song. The first-page key list is inlined in the SQL (regenerate from step 1 if stale).
- Key analytical distinction: plays of **first-page songs are expected** (they're what visitors see on load); plays of **everything else are genuine exploration** — that's the interesting signal.
- "Listeners" = distinct Umami sessions, not unique people.

### Findings snapshot (as of 2026-06-12, data from 2026-05-17 onward)
- 897 raw song-play events → **496 genuine plays** after dedup
- **367 plays (74%) were first-page songs** (42 of the top 50 played at least once). Top: *Cousin Mosquito* 80 plays / 64 listeners, *Snake Farm* 45/37, *Singing a Song Is Easy* 29/24, *The Shag (Is Totally Cool)* 20/17, *Stand Tall* 16/9
- **129 plays across 103 distinct songs were off-first-page discovery** (47 sessions)
- Top discovered: Butthole Surfers *The Annoying Song* (5 plays, 5 separate listeners — the only off-page song found independently by many), Dana Lyons *Cows with Guns* (4), William Shatner *Common People* (3 sessions found it under 3 artist spellings)
- **Covers view drives exploration:** discovered list is full of cover clusters — four *Louie Louie*s, two *House of the Rising Sun*s, two *Stairway to Heaven*s, two *Wuthering Heights*, two *Sukiyaki*s, Eilert Pilarm's Elvis covers
- **Artist rabbit holes:** single sessions played 4 Burton Cummings deep cuts, 3 10cc album tracks, 5 obscure Beach Boys songs, back-to-back Lonnie Mack

### Future blog/investigation ideas
- **Search queries** (`search` event): what people look for — and which searches find nothing (gap between audience memory and the archive)
- **Spotify-lookup failures:** songs people wanted to hear that aren't on Spotify (includes Simon Morris's own uncatalogued songs)
- **Listening taste vs radio programming:** compare genre/decade distribution of *played* songs (props on `song-play`) against the dataset's distribution — do visitors gravitate to the comedy/novelty songs or the 60s/70s deep cuts?
- **Filter & chart behaviour** (`filter-genre`, `filter-applied`, `chart-interaction`): which genres/decades people deliberately explore; whether Stats charts act as a discovery entry point
- **Traffic timing vs broadcasts:** Matinee Idle airs on public holidays — do visits/plays spike around shows? (`website_event` pageviews + session timestamps)
- **Depth of sessions:** plays-per-session distribution; the one-song bouncers vs the 10+ song explorers
- **Cousin Mosquito virality:** 64 distinct sessions played it — where did they come from (referrers on `session` table)?

---

## Data quality notes

- Most-played song: *Cousin Mosquito* by Congresswoman Malinda Jackson Parker (16 plays), found under 4 different name spellings
- 62% of artists (3,371) appeared exactly once
- Oldest song: Fred Astaire — *Puttin' on the Ritz* (1930)
- Simon Morris played his own songs on his own show multiple times; these are uncatalogued in any database
