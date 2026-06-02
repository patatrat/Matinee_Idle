/**
 * Pre-computes all Stats tab aggregations from songs.json and writes stats.json.
 * Run automatically as a prebuild step — Vercel regenerates on every deploy.
 * The dataset is fixed (show ended), so output is deterministic.
 */

import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const songs = JSON.parse(readFileSync(resolve(__dirname, "../public/songs.json"), "utf8"));

function normalize(s) {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizeArtistKey(name) {
  let s = name.replace(/\b(feat\.?|ft\.?|featuring|with)\s+/gi, " ");
  s = s.replace(/\s+(&|and|\+)\s+/gi, " ");
  return normalize(s);
}

function trunc(s, n) {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

// ── Headline stats ────────────────────────────────────────────────────────────
const totalPlays      = songs.length;
const spotifyCount    = songs.filter(s => s.spotify_url).length;
const uniqueArtistCount = new Set(songs.map(s => normalizeArtistKey(s.artist))).size;

// ── Songs per broadcast year ──────────────────────────────────────────────────
const _yearCounts = {};
for (const s of songs) {
  if (s.air_year != null) _yearCounts[s.air_year] = (_yearCounts[s.air_year] ?? 0) + 1;
}
const songsPerYear = Object.entries(_yearCounts)
  .map(([year, count]) => ({ year, count }))
  .sort((a, b) => Number(a.year) - Number(b.year));

// ── Genre breakdown ───────────────────────────────────────────────────────────
const _genreCounts = {};
for (const s of songs) {
  const g = s.genre ?? "Unknown";
  _genreCounts[g] = (_genreCounts[g] ?? 0) + 1;
}
const genreBreakdown = Object.entries(_genreCounts)
  .map(([genre, count]) => ({ genre, count }))
  .sort((a, b) => b.count - a.count);

// ── Release decades ───────────────────────────────────────────────────────────
const DECADE_BINS = [
  { label: "Pre-50s", lo: 0,    hi: 1949 },
  { label: "50s",     lo: 1950, hi: 1959 },
  { label: "60s",     lo: 1960, hi: 1969 },
  { label: "70s",     lo: 1970, hi: 1979 },
  { label: "80s",     lo: 1980, hi: 1989 },
  { label: "90s",     lo: 1990, hi: 1999 },
  { label: "00s",     lo: 2000, hi: 2009 },
  { label: "10s",     lo: 2010, hi: 2019 },
  { label: "20s+",    lo: 2020, hi: 9999 },
];
const releaseDecades = DECADE_BINS.map(({ label, lo, hi }) => ({
  label, lo,
  count: songs.filter(s => s.release_year != null && s.release_year >= lo && s.release_year <= hi).length,
}));

// ── Top 20 songs (normalised dedup, same logic as Explorer) ──────────────────
const _songCounts = {};
const _songDisplay = {};
for (const s of songs) {
  const key = `${normalizeArtistKey(s.artist)}|||${normalize(s.title)}`;
  _songCounts[key] = (_songCounts[key] ?? 0) + 1;
  if (!_songDisplay[key]) _songDisplay[key] = { artist: s.artist, title: s.title };
}
const topSongs = Object.entries(_songCounts)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .map(([key, count]) => {
    const { artist, title } = _songDisplay[key];
    return { label: trunc(`${artist} — ${title}`, 40), rawArtist: artist, count };
  });

// ── Top 20 artists ────────────────────────────────────────────────────────────
const _artistCounts = {};
const _artistNames  = {};
for (const s of songs) {
  const key = normalizeArtistKey(s.artist);
  _artistCounts[key] = (_artistCounts[key] ?? 0) + 1;
  if (!_artistNames[key] || s.artist.length < _artistNames[key].length) _artistNames[key] = s.artist;
}
const topArtistStats = Object.entries(_artistCounts)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .map(([key, count]) => ({ label: _artistNames[key] ?? key, count }));

// ── Discovery lag ─────────────────────────────────────────────────────────────
const LAG_BINS = [
  { label: "Pre-release", lo: -9999, hi: -1  },
  { label: "Same year",   lo: 0,     hi: 0   },
  { label: "1–5 yrs",     lo: 1,     hi: 5   },
  { label: "6–10 yrs",    lo: 6,     hi: 10  },
  { label: "11–20 yrs",   lo: 11,    hi: 20  },
  { label: "21–30 yrs",   lo: 21,    hi: 30  },
  { label: "31–40 yrs",   lo: 31,    hi: 40  },
  { label: "41–50 yrs",   lo: 41,    hi: 50  },
  { label: "50+ yrs",     lo: 51,    hi: 9999 },
];
const discoveryLag = LAG_BINS.map(({ label, lo, hi }) => ({
  label,
  count: songs.filter(s => {
    if (s.air_year == null || s.release_year == null) return false;
    const lag = s.air_year - s.release_year;
    return lag >= lo && lag <= hi;
  }).length,
}));

// ── Write output ──────────────────────────────────────────────────────────────
const stats = {
  totalPlays, uniqueArtistCount, spotifyCount,
  songsPerYear, genreBreakdown, releaseDecades,
  topSongs, topArtistStats, discoveryLag,
};

const out = resolve(__dirname, "../public/stats.json");
writeFileSync(out, JSON.stringify(stats));
console.log(`✓ stats.json written — ${(JSON.stringify(stats).length / 1024).toFixed(1)} KB`);
