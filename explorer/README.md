# Matinee Idle Explorer

Next.js web app for browsing the Matinee Idle song archive. Deployed at [radomski.co.nz](https://radomski.co.nz).

## Local development

```bash
cp .env.local.example .env.local
# Add your Spotify API credentials (https://developer.spotify.com/dashboard)
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment variables

| Variable | Description |
|----------|-------------|
| `SPOTIFY_CLIENT_ID` | Spotify app client ID (for on-demand track lookup) |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret |

## Data

The dataset lives at `public/songs.json` — a static JSON file of 15,411 enriched songs. No database is required at runtime. The file is committed to the repo and served as a static asset.

## Stack

- **Next.js 16** (App Router)
- **Tailwind CSS**
- **Recharts** (Stats view)
- **Vercel** (deployment)
