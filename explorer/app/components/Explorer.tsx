"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import SongCard from "./SongCard";

export interface Song {
  id: string;
  artist: string;
  title: string;
  show_date: string;
  broadcast_date: string | null;
  spotify_popularity: number | null;
  spotify_preview_url: string | null;
  spotify_url?: string;
  mb_release: string | null;
  genre: string | null;
  enrich_status: string;
  air_year: number | null;
  release_year: number | null;
}

const PAGE_SIZE = 50;
const ALL_YEARS = "all";
const ALL_GENRES = "all";

function normalize(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export default function Explorer() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [artistFilter, setArtistFilter] = useState<string>("");
  const [yearFilter, setYearFilter] = useState<string>(ALL_YEARS);
  const [genreFilter, setGenreFilter] = useState<string>(ALL_GENRES);
  const [page, setPage] = useState(1);
  const [randomSong, setRandomSong] = useState<Song | null>(null);

  useEffect(() => {
    fetch("/songs.json")
      .then((r) => r.json())
      .then((data: Song[]) => {
        setSongs(data);
        setLoading(false);
      });
  }, []);

  const years = useMemo(() => {
    const s = new Set(songs.map((s) => s.air_year).filter(Boolean) as number[]);
    return Array.from(s).sort((a, b) => a - b);
  }, [songs]);

  const genres = useMemo(() => {
    const s = new Set(songs.map((s) => s.genre).filter(Boolean) as string[]);
    return Array.from(s).sort();
  }, [songs]);

  const filtered = useMemo(() => {
    let result = songs;

    if (yearFilter !== ALL_YEARS) {
      result = result.filter((s) => s.air_year === parseInt(yearFilter));
    }

    if (genreFilter !== ALL_GENRES) {
      result = result.filter((s) => s.genre === genreFilter);
    }

    if (artistFilter) {
      result = result.filter((s) => s.artist === artistFilter);
    }

    if (query.trim()) {
      const q = normalize(query);
      result = result.filter(
        (s) =>
          normalize(s.artist).includes(q) ||
          normalize(s.title).includes(q) ||
          (s.mb_release && normalize(s.mb_release).includes(q))
      );
    }

    return result;
  }, [songs, query, artistFilter, yearFilter, genreFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleFilterChange = useCallback(
    (setter: (v: string) => void) => (v: string) => {
      setter(v);
      setPage(1);
    },
    []
  );

  const pickRandom = () => {
    const pool = filtered.length > 0 ? filtered : songs;
    setRandomSong(pool[Math.floor(Math.random() * pool.length)]);
  };

  const handleArtistClick = useCallback((artist: string) => {
    setArtistFilter(artist);
    setQuery("");
    setPage(1);
  }, []);

  const activeFilters =
    (query ? 1 : 0) +
    (artistFilter ? 1 : 0) +
    (yearFilter !== ALL_YEARS ? 1 : 0) +
    (genreFilter !== ALL_GENRES ? 1 : 0);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-neutral-800 px-4 py-6 sm:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                Matinee Idle Archive
              </h1>
              <p className="mt-1 text-sm text-neutral-400">
                21 years of Radio New Zealand's legendary summer music show
                &mdash; hosted by Phil O'Brien &amp; Simon Morris
              </p>
            </div>
            {!loading && (
              <p className="text-sm text-neutral-500 shrink-0">
                {songs.length.toLocaleString()} songs &middot; 2005–2026
              </p>
            )}
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="border-b border-neutral-800 px-4 py-4 sm:px-8 bg-neutral-900/50">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <input
            type="search"
            placeholder="Search artist, title, album…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            className="flex-1 min-w-0 rounded-lg bg-neutral-800 border border-neutral-700 px-4 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500 focus:ring-1 focus:ring-neutral-500"
          />

          {/* Year played */}
          <select
            value={yearFilter}
            onChange={(e) => handleFilterChange(setYearFilter)(e.target.value)}
            className="rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm text-white focus:outline-none focus:border-neutral-500 cursor-pointer"
          >
            <option value={ALL_YEARS}>Year played (all)</option>
            {years.map((y) => (
              <option key={y} value={y}>
                Played in {y}
              </option>
            ))}
          </select>

          {/* Genre */}
          <select
            value={genreFilter}
            onChange={(e) => handleFilterChange(setGenreFilter)(e.target.value)}
            className="rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm text-white focus:outline-none focus:border-neutral-500 cursor-pointer"
          >
            <option value={ALL_GENRES}>All genres</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>

          {/* Random */}
          <button
            onClick={pickRandom}
            className="rounded-lg bg-neutral-800 border border-neutral-700 px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors whitespace-nowrap"
          >
            ⚄ Random
          </button>
        </div>
      </div>

      {/* Results summary */}
      {!loading && (
        <div className="px-4 py-2 sm:px-8">
          <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-wrap">
              {artistFilter && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-800 border border-neutral-700 px-3 py-1 text-xs text-white">
                  {artistFilter}
                  <button
                    onClick={() => { setArtistFilter(""); setPage(1); }}
                    className="text-neutral-500 hover:text-white transition-colors"
                    aria-label="Remove artist filter"
                  >×</button>
                </span>
              )}
              <p className="text-xs text-neutral-500">
                {activeFilters > 0 ? (
                  <>
                    <span className="text-neutral-300">
                      {filtered.length.toLocaleString()}
                    </span>{" "}
                    result{filtered.length !== 1 ? "s" : ""}
                    {totalPages > 1 && <> &middot; page {page} of {totalPages}</>}
                  </>
                ) : (
                  <>Showing {paginated.length} of {songs.length.toLocaleString()} songs</>
                )}
              </p>
            </div>
            {activeFilters > 0 && (
              <button
                onClick={() => {
                  setQuery("");
                  setArtistFilter("");
                  setYearFilter(ALL_YEARS);
                  setGenreFilter(ALL_GENRES);
                  setPage(1);
                }}
                className="text-xs text-neutral-500 hover:text-white transition-colors underline shrink-0"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Random song spotlight */}
      {randomSong && (
        <div className="px-4 sm:px-8 pt-2">
          <div className="max-w-6xl mx-auto">
            <div className="rounded-xl border border-amber-700/40 bg-amber-950/20 p-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium text-amber-500 uppercase tracking-wider mb-1">
                  Random pick
                </p>
                <p className="font-semibold text-white">
                  {randomSong.artist} — {randomSong.title}
                </p>
                <p className="text-sm text-neutral-400 mt-0.5">
                  {randomSong.air_year}
                  {randomSong.mb_release && ` · ${randomSong.mb_release}`}
                  {randomSong.genre && ` · ${randomSong.genre}`}
                </p>
              </div>
              <button
                onClick={() => setRandomSong(null)}
                className="text-neutral-600 hover:text-white text-lg leading-none transition-colors"
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 px-4 py-4 sm:px-8">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="flex items-center justify-center py-32 text-neutral-600">
              <div className="text-center">
                <div className="inline-block w-6 h-6 border-2 border-neutral-700 border-t-neutral-400 rounded-full animate-spin mb-3" />
                <p className="text-sm">Loading archive…</p>
              </div>
            </div>
          ) : paginated.length === 0 ? (
            <div className="text-center py-32 text-neutral-600">
              <p className="text-2xl mb-2">♪</p>
              <p>No songs match your search.</p>
            </div>
          ) : (
            <div className="grid gap-2">
              {paginated.map((song) => (
                <SongCard key={song.id} song={song} onArtistClick={handleArtistClick} />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="border-t border-neutral-800 px-4 py-4 sm:px-8">
          <div className="max-w-6xl mx-auto flex items-center justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-sm text-neutral-300 hover:bg-neutral-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            <span className="text-sm text-neutral-500 px-2">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-sm text-neutral-300 hover:bg-neutral-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-neutral-800 px-4 py-4 sm:px-8 text-center text-xs text-neutral-700">
        <a
          href="https://www.rnz.co.nz"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-neutral-500 transition-colors"
        >
          Data sourced from RNZ archives
        </a>{" "}
        &middot; radomski.co.nz
      </footer>
    </div>
  );
}
