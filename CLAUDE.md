# Matinee Idle Song Explorer

**Project Status:** In Progress  
**Last Updated:** April 2026  
**Hosted on:** radomski.co.nz  
**Database:** Supabase (currently paused, 2/2 free tier slots occupied)

---

## Project Vision

A interactive data explorer celebrating 21 years of "Matinee Idle," Radio New Zealand's legendary summer music show (2005-2026). The show, hosted by Phil O'Brien and Simon Morris, featured rare, obscure, divisive, and forgotten musical gems that either delighted or polarized listeners.

This project transforms the complete archive of songs played across 21 summers into an explorable dataset, enabling music discovery, analysis, and storytelling about the show's cultural impact.

### Key Features
- **Data Explorer:** Interactive search and browse interface for all songs played
- **Chat Query Interface:** Natural language questions about the dataset (e.g., "What songs were played in 2015?", "Show me all punk tracks")
- **Infographic & Stats:** Blog post with surprising insights, trends, and patterns from the dataset

---

## What's Done

### 1. Archive Scraper ✓
- Built web scraper to extract complete song list from RNZ archive
- Successfully captured all songs across 21 years of the show
- Data includes: artist, song title, and original air date

### 2. Supabase Database ✓
- Created PostgreSQL schema with songs table
- Initial load: full song archive (exact count: to be confirmed)
- Database currently **paused** (free tier limit: 2 active databases)

### 3. Data Enrichment ✓ (80% complete)
- Enriched song metadata using public APIs:
  - **Spotify API:** album year, genres, popularity metrics
  - **Last.fm API:** play counts, listener statistics
  - **MusicBrainz:** standardized IDs, release years
- Coverage: ~80% of songs successfully matched and enriched
- Missing/unmatched songs: primarily very obscure artists or regional releases

**Enriched fields include:**
- Release year / Album year
- Genre tags (primary and secondary)
- Artist bio summary
- Spotify URI (for integration)
- Album artwork URL
- Play counts / popularity metrics
- Last.fm tags (user-generated genre/mood tags)

### 4. Current Data Health
- **Total songs:** ~[INSERT COUNT]
- **Enrichment rate:** 80% (metadata matched)
- **Data quality:** Good (validated and deduplicated)
- **Known gaps:** Very early recordings (1950s), regional/non-English releases

---

## What Needs Building

### Phase 1: Web Explorer Interface (Frontend)

**Goal:** Interactive, responsive web UI for exploring the song database

#### 1.1 Search & Filter
- [ ] **Full-text search** (artist name, song title, album)
- [ ] **Filter by date range:** Year/season sliders
- [ ] **Filter by genre:** Multi-select genre tags
- [ ] **Filter by era:** Predefined eras (70s, 80s, 90s, 2000s, etc.)
- [ ] **Combine filters:** AND/OR logic for multiple criteria
- [ ] **Save searches:** Bookmark favorite searches

#### 1.2 Song Card Display
- [ ] Song title + artist (prominent)
- [ ] Album artwork (Spotify/MusicBrainz source)
- [ ] Air date on Matinee Idle
- [ ] Release year + genre tags
- [ ] Quick stats: Spotify popularity, play counts
- [ ] **"Play on Spotify"** button (if Spotify URI available)
- [ ] **"Read more"** link to expanded song details

#### 1.3 Browse & Discover
- [ ] **Timeline view:** Visual calendar/timeline of songs by year
- [ ] **Genre explorer:** Show top songs per genre
- [ ] **Most played artists:** Leaderboard of artists featured most
- [ ] **"Random song"** button for serendipitous discovery
- [ ] **Featured collections:** Curated playlists (e.g., "Overlooked gems," "One-hit wonders")

#### 1.4 Song Detail Page
- [ ] Full metadata display
- [ ] Play count trends over time (if available)
- [ ] Listener demographics (Last.fm insights)
- [ ] Spotify link + embed player
- [ ] Related songs (same artist, genre, or era)
- [ ] Comments section (optional: allow listeners to share memories)

#### 1.5 Responsive Design
- [ ] Mobile-first design
- [ ] Tablet layout optimization
- [ ] Dark mode support
- [ ] Accessibility (WCAG AA)

**Tech Stack Suggestion:**
- Frontend: Next.js + React
- Styling: Tailwind CSS or custom CSS
- Data fetching: SWR or React Query (for caching)
- API layer: Next.js API routes
- Component library: Headless UI or Shadcn/UI

---

### Phase 2: Chat Query Interface

**Goal:** Allow users to ask natural language questions about the dataset

#### 2.1 Chat Widget
- [ ] Chat input field + message history
- [ ] Streaming response capability (if using Claude API)
- [ ] Clear chat / new conversation button
- [ ] Loading indicators + error states

#### 2.2 Query Types to Support
```
Examples:
- "What songs were played in summer 2012?"
- "Show me all punk and new wave songs"
- "Which songs have the highest Spotify play counts?"
- "What was the most-featured artist?"
- "How many songs per year were played on average?"
- "Find songs from the 1960s that were played"
- "Show me songs by Phil O'Brien's favourite artists"
```

#### 2.3 Implementation Approach
**Option A: Claude-powered (recommended)**
- Use Claude API with system prompt + song data context
- Pass relevant song data from Supabase as context
- Claude generates natural responses + can suggest follow-up queries
- Pros: Conversational, creative, handles ambiguous questions
- Cons: API costs, context window limitations

**Option B: Structured Query Builder**
- Parse user intent → build SQL/API queries
- Return formatted results + optional follow-ups
- Pros: Cheaper, faster, more predictable
- Cons: Less natural, harder to expand

#### 2.4 Data Context Strategy
- Pre-compute aggregate stats (yearly counts, top artists, genre distribution)
- Cache these in Redis or static JSON
- Feed small, relevant subsets to Claude per query
- Never send full dataset to avoid token waste

---

### Phase 3: Infographic & Blog Post

**Goal:** Create a visually engaging story about the dataset

#### 3.1 Stats to Highlight
- [ ] Total songs played across 21 years
- [ ] Most-featured artist (by play count)
- [ ] Rarest/most obscure songs (lowest play counts)
- [ ] Genre distribution trends over time
- [ ] "Discovery rate": songs that went on to become popular post-broadcast
- [ ] Longest gap between song release and Matinee Idle play
- [ ] Regional/international breakdown of artists
- [ ] Evolution: earliest songs vs. latest songs played

#### 3.2 Visual Elements
- [ ] Animated timeline of songs by year
- [ ] Genre pie chart / stacked area chart
- [ ] Top 10 artists bar chart
- [ ] Word cloud of genres / artist origins
- [ ] Heatmap: songs played per month (seasonality)
- [ ] Notable "sleepers": songs played early, became hits later

#### 3.3 Narrative Structure
1. **Hook:** "21 years, thousands of songs, one legendary show"
2. **By the numbers:** Key stats + visuals
3. **The hits & misses:** Most/least played songs
4. **Genre safari:** How the show's musical taste evolved
5. **Discovery stories:** Did the show predict hit songs?
6. **Call to action:** "Explore the full dataset" link to explorer

#### 3.4 Blog Post Meta
- [ ] SEO optimized title & description
- [ ] Social sharing metadata (OG tags)
- [ ] Author bio & "written with Claude" credit
- [ ] Related posts (e.g., "The Matinee Idle Legacy")

**Tech Stack Suggestion:**
- Blog platform: Markdown (published via radomski.co.nz)
- Visualizations: D3.js, Chart.js, or Recharts
- Infographic design: Figma (export as SVG/PNG)

---

## Technical Architecture

### Database Schema

```sql
-- Songs table
CREATE TABLE songs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(500) NOT NULL,
  artist VARCHAR(255) NOT NULL,
  
  -- Air date
  air_date DATE NOT NULL,
  air_year INTEGER NOT NULL,
  air_season VARCHAR(20), -- "summer", "easter", "anzac"
  
  -- Enriched metadata
  release_year INTEGER,
  genres TEXT[] DEFAULT ARRAY[]::TEXT[],
  primary_genre VARCHAR(100),
  
  -- External IDs
  spotify_id VARCHAR(100),
  spotify_uri VARCHAR(255),
  musicbrainz_id VARCHAR(100),
  lastfm_mbid VARCHAR(100),
  
  -- Metadata
  album_title VARCHAR(500),
  album_art_url TEXT,
  artist_image_url TEXT,
  
  -- Stats
  spotify_popularity INTEGER,
  spotify_play_count BIGINT,
  lastfm_play_count INTEGER,
  lastfm_listeners INTEGER,
  
  -- Data quality
  enriched BOOLEAN DEFAULT FALSE,
  enriched_at TIMESTAMP,
  enrichment_source VARCHAR(100),
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_songs_artist ON songs(artist);
CREATE INDEX idx_songs_title ON songs(title);
CREATE INDEX idx_songs_air_date ON songs(air_date);
CREATE INDEX idx_songs_air_year ON songs(air_year);
CREATE INDEX idx_songs_genres ON songs USING GIN(genres);
CREATE INDEX idx_songs_release_year ON songs(release_year);
```

### API Endpoints (Next.js API Routes)

```
GET /api/songs
  - Query params: search, artist, genre, year, limit, offset
  - Returns: paginated song list

GET /api/songs/:id
  - Returns: full song details

GET /api/stats
  - Returns: aggregate stats (top artists, genres, timeline)

POST /api/chat
  - Body: { message: string, history: [] }
  - Returns: { response: string, suggestions: [] }

GET /api/search/autocomplete
  - Query: q (artist or song title)
  - Returns: suggestions
```

### Database State
- **Currently:** Paused (free tier limit)
- **To resume:** Drop one of canyoubeatwellington or robopat
- **Backup strategy:** Export as CSV/JSON before resuming

---

## Implementation Roadmap

### Week 1-2: Setup & Data
- [ ] Resume Supabase database (pause a different project)
- [ ] Verify data integrity + run final enrichment pass
- [ ] Create API layer (Next.js routes)
- [ ] Set up data caching strategy

### Week 3-4: Explorer UI (MVP)
- [ ] Build search + filter interface
- [ ] Implement song cards + display
- [ ] Create basic browse views (timeline, artists, genres)
- [ ] Mobile responsive design
- [ ] Deploy to radomski.co.nz

### Week 5-6: Polish & Features
- [ ] Song detail pages
- [ ] Spotify embed integration
- [ ] Random song discovery
- [ ] Save/bookmark searches
- [ ] Dark mode

### Week 7-8: Chat Interface
- [ ] Set up Claude API integration
- [ ] Build chat component
- [ ] Test common queries
- [ ] Error handling + fallbacks

### Week 9-10: Infographic & Blog
- [ ] Gather stats + create visualizations
- [ ] Write blog narrative
- [ ] Design infographic
- [ ] Publish blog post

### Week 11+: Polish & Launch
- [ ] User testing + feedback
- [ ] SEO optimization
- [ ] Analytics setup
- [ ] Public launch + promotion

---

## Known Challenges & Solutions

### 1. Supabase Slot Limitation
- **Problem:** Only 2 free databases; this is paused
- **Solution:** Migrate to paid tier ($10/month) or drop another project
- **Alternative:** Host on cheaper Postgres provider (render.com, railway.app)

### 2. Enrichment Gaps (80% coverage)
- **Problem:** Some songs can't be matched to Spotify/MusicBrainz
- **Solution:** 
  - Manual curation for high-profile missing songs
  - User-submitted corrections
  - Fallback to Wikipedia/IMDB for artist bios

### 3. Chat Query Reliability
- **Problem:** Claude might generate incorrect SQL or make up data
- **Solution:**
  - Pre-compute all aggregates + queries
  - Use system prompt to limit responses to "true" queries only
  - Show a "confidence" indicator if answer is speculative
  - Include source data in response

### 4. Performance at Scale
- **Problem:** If dataset grows large, search could be slow
- **Solution:**
  - PostgreSQL full-text search (already supported)
  - Denormalize common aggregates
  - Cache results in Redis
  - Consider Algolia/Meilisearch if needed

### 5. Mobile UX
- **Problem:** Lots of data to display on small screens
- **Solution:**
  - Progressive disclosure (summary → detail)
  - Horizontal scrolling for charts
  - Bottom sheets for filters
  - Test on real devices

---

## Inspiration & References

### Design Inspiration
- **Spotify Data Hub:** spotify.com/openplaylist (visual design)
- **Last.fm Charts:** charts.last.fm (data presentation)
- **Every Noise at Once:** everynoise.com (genre visualization)
- **Rate Your Music:** rateyourmusic.com (music database UX)

### Technical References
- Next.js data fetching: nextjs.org/docs/basic-features/data-fetching
- Supabase docs: supabase.com/docs
- Claude API: anthropic.com/docs
- Spotify Web API: developer.spotify.com
- D3.js: d3js.org

### Articles/Stories
- The Matinee Idle story: https://www.rnz.co.nz/life/culture/matinee-idle-co-hosts-phil-o-brien-and-simon-morris-sign-off
- Phil O'Brien on the show's impact & listener community

---

## Future Ideas (Post-MVP)

- [ ] **User playlists:** Export to Spotify
- [ ] **Listener community:** Comments, ratings, shared lists
- [ ] **Audio timeline:** Embed clips from the show
- [ ] **Artist spotlights:** Deep dives into featured artists' careers
- [ ] **Monthly challenges:** "Listen to one song from Matinee Idle"
- [ ] **Merch:** T-shirts, mugs with song data art
- [ ] **Podcast:** Interview artists from the archive
- [ ] **API:** Public endpoint for other developers to build with

---

## Questions to Answer Before Building

1. **Data ownership:** Do you have explicit permission to republish the song list?
2. **Spotify integration:** Will you embed players or link to Spotify?
3. **Target audience:** Existing Matinee Idle fans or music discovery audience?
4. **Monetization:** Free forever, or ads/Patreon support?
5. **Update frequency:** One-time archive or ongoing if the show returns?

---

## Notes for Next Session

- [ ] Check exact song count in database
- [ ] Review which songs have enrichment gaps
- [ ] Decide on Supabase alternative (paid tier or migrate)
- [ ] Sketch wireframes for explorer UI
- [ ] List top 10 stats to highlight in infographic
- [ ] Create project board (GitHub/Linear) for tracking

---

**Created:** April 2026  
**By:** radomski.co.nz  
**With assistance from:** Claude
