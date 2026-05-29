"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import SongCard from "./SongCard";
import FilterSidebar from "./FilterSidebar";
import StatsView from "./StatsView";

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

type SortBy = "date-played" | "times-played" | "date-released";
type View = "songs" | "artists" | "covers" | "stats";

const PAGE_SIZE = 50;
const MIN_COVER_VERSIONS = 4;

const DECADES: { label: string; lo: number; hi: number }[] = [
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

function normalize(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function Pill({ children, onRemove }: { children: React.ReactNode; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-800 border border-neutral-700 px-3 py-1 text-xs text-white">
      {children}
      <button onClick={onRemove} className="text-neutral-500 hover:text-white transition-colors" aria-label="Remove filter">×</button>
    </span>
  );
}

export default function Explorer() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [query, setQuery] = useState("");
  const [artistFilter, setArtistFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("all");
  const [decadeFilter, setDecadeFilter] = useState<number | null>(null);
  const [releaseYearFilter, setReleaseYearFilter] = useState<number | null>(null);
  const [genreFilters, setGenreFilters] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<SortBy>("times-played");
  const [page, setPage] = useState(1);

  // UI state
  const [view, setView] = useState<View>("songs");
  const [expandedCovers, setExpandedCovers] = useState<Set<string>>(new Set());
  const [randomSong, setRandomSong] = useState<Song | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activePlayId, setActivePlayId] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(false);

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

  // Group artist play counts by normalized key so punctuation/spelling variants
  // ("Dr. Hook", "Dr Hook", "Dr. Hook & The Medicine Show") share the same count.
  const artistCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of songs) {
      const key = normalize(s.artist);
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [songs]);

  // For each normalized artist key, track the shortest raw name as the canonical
  // display/filter value — so clicking any variant sets the filter to the base form
  // that substring-matches all longer variants (e.g. "Dr Hook" matches "Dr. Hook & …").
  const canonicalArtist = useMemo(() => {
    const map: Record<string, string> = {};
    for (const s of songs) {
      const key = normalize(s.artist);
      if (!map[key] || s.artist.length < map[key].length) map[key] = s.artist;
    }
    return map;
  }, [songs]);

  const songPlayCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of songs) {
      const key = `${normalize(s.artist)}|||${normalize(s.title)}`;
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [songs]);

  const uniqueArtists = useMemo(() => Object.keys(artistCounts).length, [artistCounts]);

  const topArtists = useMemo(() => {
    return Object.entries(artistCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 15)
      .map(([key, count]) => ({ artist: canonicalArtist[key] ?? key, count }));
  }, [artistCounts, canonicalArtist]);

  const filtered = useMemo(() => {
    let result = songs;

    if (yearFilter !== "all") {
      result = result.filter((s) => s.air_year === parseInt(yearFilter));
    }
    if (genreFilters.size > 0) {
      result = result.filter((s) => s.genre != null && genreFilters.has(s.genre));
    }
    if (artistFilter.trim()) {
      const af = normalize(artistFilter);
      result = result.filter((s) => normalize(s.artist).includes(af));
    }
    if (releaseYearFilter !== null) {
      result = result.filter((s) => s.release_year === releaseYearFilter);
    } else if (decadeFilter !== null) {
      const decade = DECADES.find((d) => d.lo === decadeFilter);
      if (decade) {
        result = result.filter(
          (s) => s.release_year != null && s.release_year >= decade.lo && s.release_year <= decade.hi
        );
      }
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

    if (sortBy === "date-played") {
      result = [...result].sort((a, b) => (a.show_date ?? "").localeCompare(b.show_date ?? ""));
    } else if (sortBy === "times-played") {
      result = [...result].sort(
        (a, b) =>
          (songPlayCounts[`${normalize(b.artist)}|||${normalize(b.title)}`] ?? 1) -
          (songPlayCounts[`${normalize(a.artist)}|||${normalize(a.title)}`] ?? 1)
      );
    } else if (sortBy === "date-released") {
      result = [...result].sort((a, b) => (a.release_year ?? 9999) - (b.release_year ?? 9999));
    }

    // Deduplicate: show each unique song once — play count badge shows total plays
    const seen = new Set<string>();
    result = result.filter((s) => {
      const key = `${s.artist}|||${s.title}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    return result;
  }, [songs, query, artistFilter, releaseYearFilter, decadeFilter, yearFilter, genreFilters, sortBy, songPlayCounts]);

  // Cover versions: same title, 4+ distinct artists across the full archive
  const coversView = useMemo(() => {
    const groups: Record<string, { title: string; artistKeys: Set<string>; songs: Song[] }> = {};
    for (const s of songs) {
      const key = normalize(s.title);
      if (!groups[key]) groups[key] = { title: s.title, artistKeys: new Set(), songs: [] };
      groups[key].artistKeys.add(normalize(s.artist));
      groups[key].songs.push(s);
    }
    return Object.values(groups)
      .filter(g => g.artistKeys.size >= MIN_COVER_VERSIONS)
      .map(g => {
        // One entry per distinct artist — keep their earliest play
        const byArtist: Record<string, Song> = {};
        for (const s of g.songs) {
          const ak = normalize(s.artist);
          const existing = byArtist[ak];
          if (!existing || (s.air_year ?? 9999) < (existing.air_year ?? 9999)) {
            byArtist[ak] = s;
          }
        }
        const versions = Object.values(byArtist).sort(
          (a, b) => (a.release_year ?? a.air_year ?? 9999) - (b.release_year ?? b.air_year ?? 9999)
        );
        return { title: g.title, count: g.artistKeys.size, versions };
      })
      .sort((a, b) => b.count - a.count);
  }, [songs]);

  // All artists by unique song count, derived from the already-deduplicated filtered list
  const artistsView = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const s of filtered) {
      const key = normalize(s.artist);
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([key, count]) => ({ artist: canonicalArtist[key] ?? key, count }));
  }, [filtered, canonicalArtist]);

  // Deduplicate by normalised artist+title so capitalisation variants
  // (e.g. "Singing a Song is Easy" vs "Singing a Song Is Easy") appear once.
  const deduped = useMemo(() => {
    const seen = new Set<string>();
    return filtered.filter(s => {
      const key = `${normalize(s.artist)}|||${normalize(s.title)}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [filtered]);

  const totalPages = Math.max(1, Math.ceil(deduped.length / PAGE_SIZE));
  const paginated = deduped.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // ── Analytics ────────────────────────────────────────────────────────────────

  // Arrival: fire once on load — referrer hostname + any UTM params in the URL
  useEffect(() => {
    const ref = document.referrer;
    const params = new URLSearchParams(window.location.search);
    const props: Record<string, string> = {};
    if (params.get("utm_source"))   props.utm_source   = params.get("utm_source")!;
    if (params.get("utm_medium"))   props.utm_medium   = params.get("utm_medium")!;
    if (params.get("utm_campaign")) props.utm_campaign = params.get("utm_campaign")!;
    if (ref) {
      try { props.referrer = new URL(ref).hostname; } catch { props.referrer = ref; }
      if (ref.includes("facebook.com"))                     props.source = "facebook";
      else if (ref.includes("reddit.com"))                  props.source = "reddit";
      else if (ref.includes("twitter.com") || ref.includes("x.com")) props.source = "twitter";
      else if (ref.includes("instagram.com"))               props.source = "instagram";
      else if (ref.includes("google.com"))                  props.source = "google";
      else                                                  props.source = "referral";
    } else {
      props.source = params.get("utm_source") ?? "direct";
    }
    window.umami?.track("arrival", props);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search: debounced 800ms, only when query has 2+ characters
  useEffect(() => {
    if (query.trim().length < 2) return;
    const timer = setTimeout(() => {
      window.umami?.track("search", {
        query: query.trim(),
        results: String(deduped.length),
      });
    }, 800);
    return () => clearTimeout(timer);
  }, [query, deduped.length]);

  // ─────────────────────────────────────────────────────────────────────────────

  const activeFilterCount =
    (query ? 1 : 0) +
    (artistFilter ? 1 : 0) +
    (releaseYearFilter !== null ? 1 : 0) +
    (decadeFilter !== null ? 1 : 0) +
    (yearFilter !== "all" ? 1 : 0) +
    genreFilters.size;

  const handleClearAll = useCallback(() => {
    setQuery("");
    setArtistFilter("");
    setReleaseYearFilter(null);
    setDecadeFilter(null);
    setYearFilter("all");
    setGenreFilters(new Set());
    setPage(1);
  }, []);

  const handleArtistClick = useCallback((artist: string) => {
    setArtistFilter(canonicalArtist[normalize(artist)] ?? artist);
    setQuery("");
    setPage(1);
  }, [canonicalArtist]);

  const handleTopArtistClick = useCallback((artist: string) => {
    setView("songs");
    setArtistFilter(canonicalArtist[normalize(artist)] ?? artist);
    setQuery("");
    setPage(1);
  }, [canonicalArtist]);

  const handleGenreClick = useCallback((genre: string) => {
    setGenreFilters((prev) => {
      const next = new Set(prev);
      if (next.has(genre)) next.delete(genre); else next.add(genre);
      return next;
    });
    setPage(1);
  }, []);

  const handleReleaseYearClick = useCallback((year: number) => {
    setReleaseYearFilter(year);
    setDecadeFilter(null);
    setPage(1);
  }, []);

  const handleGenreToggle = useCallback((genre: string) => {
    setGenreFilters((prev) => {
      const next = new Set(prev);
      if (next.has(genre)) {
        next.delete(genre);
      } else {
        next.add(genre);
        window.umami?.track("filter-genre", { genre });
      }
      return next;
    });
    setPage(1);
  }, []);

  const handleDecadeChange = useCallback((lo: number | null) => {
    setDecadeFilter(lo);
    setReleaseYearFilter(null);
    setPage(1);
  }, []);

  const handleSpotifyResult = useCallback((artist: string, title: string, url: string) => {
    setSongs((prev) =>
      prev.map((s) =>
        s.artist === artist && s.title === title ? { ...s, spotify_url: url } : s
      )
    );
  }, []);

  const handleNext = useCallback((currentId: string) => {
    const withLinks = deduped.filter((s) => s.spotify_url);
    if (withLinks.length <= 1) return;
    const idx = withLinks.findIndex((s) => s.id === currentId);
    const next = withLinks[idx === -1 ? 0 : (idx + 1) % withLinks.length];
    setActivePlayId(next.id);
    const allIdx = deduped.findIndex((s) => s.id === next.id);
    if (allIdx >= 0) setPage(Math.floor(allIdx / PAGE_SIZE) + 1);
  }, [deduped]);

  const handleCoversNext = useCallback((currentId: string) => {
    const flat = coversView.flatMap((g) => g.versions).filter((s) => s.spotify_url);
    if (flat.length <= 1) return;
    const idx = flat.findIndex((s) => s.id === currentId);
    const next = flat[idx === -1 ? 0 : (idx + 1) % flat.length];
    setActivePlayId(next.id);
    // Ensure the group containing the next song is expanded
    const group = coversView.find((g) => g.versions.some((s) => s.id === next.id));
    if (group) setExpandedCovers((prev) => new Set([...prev, group.title]));
  }, [coversView]);

  const pickRandom = useCallback(() => {
    const pool = filtered.length > 0 ? filtered : songs;
    setRandomSong(pool[Math.floor(Math.random() * pool.length)]);
  }, [filtered, songs]);


  const sidebarProps = {
    query, onQueryChange: (v: string) => { setQuery(v); setPage(1); },
    artistFilter, onArtistChange: (v: string) => { setArtistFilter(v); setPage(1); },
    yearFilter, onYearChange: (v: string) => { setYearFilter(v); setPage(1); },
    years,
    decadeFilter, onDecadeChange: handleDecadeChange,
    genreFilters, onGenreToggle: handleGenreToggle,
    sortBy, onSortChange: (v: SortBy) => { setSortBy(v); setPage(1); },
    onRandom: pickRandom,
    onClearAll: handleClearAll,
    activeFilterCount,
    topArtists,
    onTopArtistClick: handleTopArtistClick,
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-t-2 border-amber-500 border-b border-b-neutral-800">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                {/* Radio tower icon */}
                <svg className="text-amber-400 shrink-0" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M4.929 2.515a1 1 0 0 0-1.414 1.414L5.05 5.464A9.956 9.956 0 0 0 2 12c0 2.4.847 4.604 2.25 6.33l-1.775 1.775a1 1 0 1 0 1.414 1.414L5.71 19.7A9.956 9.956 0 0 0 12 22a9.956 9.956 0 0 0 6.29-2.3l1.82 1.819a1 1 0 1 0 1.414-1.414L19.75 18.33A9.956 9.956 0 0 0 22 12a9.956 9.956 0 0 0-3.05-7.064l1.535-1.535a1 1 0 0 0-1.414-1.414l-1.64 1.639A9.955 9.955 0 0 0 12 2a9.955 9.955 0 0 0-5.431 1.626L4.93 2.515zM12 4a8 8 0 1 1 0 16A8 8 0 0 1 12 4zm0 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/>
                </svg>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Matinee Idle Archive
                </h1>
              </div>
              <p className="mt-1 text-[11px] text-neutral-500 tracking-widest uppercase">
                Radio New Zealand · Phil O&apos;Brien &amp; Simon Morris · 2005–2026
              </p>
              <a
                href="https://radomski.co.nz/blog/matinee-idle"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1.5 inline-block text-[11px] text-amber-500/70 hover:text-amber-400 transition-colors"
              >
                What&apos;s this all about then? →
              </a>
            </div>
            {!loading && (
              <div className="hidden sm:flex items-center gap-2 shrink-0">
                <span className="bg-neutral-900 border border-neutral-800 rounded-full px-3 py-1 text-xs text-neutral-500">
                  {songs.length.toLocaleString()} plays
                </span>
                <span className="bg-neutral-900 border border-neutral-800 rounded-full px-3 py-1 text-xs text-neutral-500">
                  {uniqueArtists.toLocaleString()} artists
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Body: sidebar + content */}
      <div className="flex-1 flex flex-col lg:flex-row max-w-7xl w-full mx-auto">

        {/* ── Desktop sidebar ── */}
        <aside className="hidden lg:block w-64 shrink-0 border-r border-neutral-800 sticky top-0 h-screen overflow-y-auto sidebar-scroll">
          <FilterSidebar {...sidebarProps} />
        </aside>

        {/* ── Content column ── */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Mobile: search + filter toggle */}
          <div className="lg:hidden border-b border-neutral-800 px-4 py-3 flex gap-2">
            <input
              type="search"
              placeholder="Search artist, title, album…"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1); }}
              className="flex-1 min-w-0 rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-600"
            />
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="shrink-0 flex items-center gap-1.5 rounded-lg bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm text-neutral-400 hover:text-white transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
              Filters
              {activeFilterCount > 0 && (
                <span className="bg-amber-500 text-black text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>

          {/* Mobile filter drawer */}
          <div
            className={`lg:hidden border-b border-neutral-800 overflow-hidden transition-all duration-300 ${
              sidebarOpen ? "max-h-[80vh] overflow-y-auto sidebar-scroll" : "max-h-0"
            }`}
          >
            <FilterSidebar {...sidebarProps} />
            <div className="px-4 pb-4">
              <button
                onClick={() => setSidebarOpen(false)}
                className="w-full rounded-lg border border-neutral-700 py-2 text-sm text-neutral-400 hover:text-white transition-colors"
              >
                Done
              </button>
            </div>
          </div>

          {/* View tabs */}
          {!loading && (
            <div className="flex border-b border-neutral-800 px-1">
              {([
                { id: "songs",   label: `Songs · ${filtered.length.toLocaleString()}` },
                { id: "artists", label: `Artists · ${artistsView.length.toLocaleString()}` },
                { id: "covers",  label: `Covers · ${coversView.length.toLocaleString()}` },
                { id: "stats",   label: "Stats" },
              ] as { id: View; label: string }[]).map(({ id, label }) => (
                <button
                  key={id}
                  onClick={() => { setView(id); setPage(1); }}
                  className={`px-5 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
                    view === id
                      ? "border-amber-500 text-white"
                      : "border-transparent text-neutral-500 hover:text-neutral-300"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          )}

          {/* Active filter pills + result summary */}
          {!loading && view === "songs" && (
            <div className="px-4 pt-3 pb-1 sm:px-6">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  {artistFilter && (
                    <Pill onRemove={() => { setArtistFilter(""); setPage(1); }}>Artist: {artistFilter}</Pill>
                  )}
                  {releaseYearFilter !== null && (
                    <Pill onRemove={() => { setReleaseYearFilter(null); setPage(1); }}>Released {releaseYearFilter}</Pill>
                  )}
                  {decadeFilter !== null && (
                    <Pill onRemove={() => { setDecadeFilter(null); setPage(1); }}>
                      {DECADES.find((d) => d.lo === decadeFilter)?.label ?? decadeFilter}s
                    </Pill>
                  )}
                  {[...genreFilters].map((g) => (
                    <Pill key={g} onRemove={() => { setGenreFilters((prev) => { const n = new Set(prev); n.delete(g); return n; }); setPage(1); }}>
                      {g}
                    </Pill>
                  ))}
                  {totalPages > 1 && (
                    <p className="text-xs text-neutral-600">page {page} of {totalPages}</p>
                  )}
                </div>
                {activeFilterCount > 0 && (
                  <button
                    onClick={handleClearAll}
                    className="text-xs text-neutral-500 hover:text-white transition-colors underline shrink-0"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Random song spotlight */}
          {randomSong && (
            <div className="px-4 sm:px-6 pt-2">
              <div className="rounded-xl border border-amber-700/40 bg-amber-950/20 p-4 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-medium text-amber-500 uppercase tracking-wider mb-1">Random pick</p>
                  <p className="font-semibold text-white">{randomSong.artist} — {randomSong.title}</p>
                  <p className="text-sm text-neutral-400 mt-0.5">
                    {randomSong.air_year}
                    {randomSong.mb_release && ` · ${randomSong.mb_release}`}
                    {randomSong.genre && ` · ${randomSong.genre}`}
                  </p>
                </div>
                <button onClick={() => setRandomSong(null)} className="text-neutral-600 hover:text-white text-lg leading-none transition-colors" aria-label="Dismiss">×</button>
              </div>
            </div>
          )}


          {/* Main content: Songs / Artists / Covers */}
          <main className="flex-1 min-w-0">
            {loading ? (
              <div className="flex items-center justify-center py-32 text-neutral-600">
                <div className="text-center">
                  <div className="inline-block w-6 h-6 border-2 border-neutral-700 border-t-neutral-400 rounded-full animate-spin mb-3" />
                  <p className="text-sm">Loading archive…</p>
                </div>
              </div>
            ) : view === "stats" ? (
              <StatsView
                songs={songs}
                onGenreClick={(genre) => { setGenreFilters(new Set([genre])); setView("songs"); setPage(1); }}
                onArtistClick={handleTopArtistClick}
                onYearClick={(year) => { setYearFilter(year); setView("songs"); setPage(1); }}
                onDecadeClick={(lo) => { handleDecadeChange(lo); setView("songs"); }}
              />
            ) : view === "covers" ? (
              <div className="divide-y divide-neutral-900/60 px-4 sm:px-6 py-2">
                {coversView.map(({ title, count, versions }) => {
                  const isOpen = expandedCovers.has(title);
                  return (
                    <div key={title} className="py-3">
                      {/* Header row — click to expand/collapse */}
                      <button
                        onClick={() => setExpandedCovers(prev => {
                          const next = new Set(prev);
                          if (next.has(title)) next.delete(title); else next.add(title);
                          return next;
                        })}
                        className="w-full flex items-center gap-3 text-left group"
                      >
                        <span className={`text-neutral-600 transition-transform duration-200 shrink-0 ${isOpen ? "rotate-90" : ""}`}>
                          ▶
                        </span>
                        <span className="flex-1 font-semibold text-neutral-100 group-hover:text-white transition-colors">
                          {title}
                        </span>
                        <span className="shrink-0 text-xs font-medium bg-neutral-800 text-neutral-400 rounded-full px-2.5 py-0.5">
                          {count} versions
                        </span>
                      </button>

                      {/* Expandable version list — rendered as full SongCards */}
                      {isOpen && (
                        <div className="mt-2 ml-4 border-l-2 border-neutral-800 pl-2">
                          {versions.map((s) => (
                            <SongCard
                              key={s.id}
                              song={s}
                              artistCount={artistCounts[normalize(s.artist)] ?? 1}
                              playCount={songPlayCounts[`${normalize(s.artist)}|||${normalize(s.title)}`] ?? 1}
                              onArtistClick={(a) => { setView("songs"); handleArtistClick(a); }}
                              onGenreClick={handleGenreClick}
                              onReleaseYearClick={handleReleaseYearClick}
                              onSpotifyResult={handleSpotifyResult}
                              isActive={activePlayId === s.id}
                              onSetActive={() => setActivePlayId(s.id)}
                              onNext={() => handleCoversNext(s.id)}
                              autoPlay={autoPlay}
                              onAutoPlayToggle={() => setAutoPlay(v => !v)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : view === "artists" ? (
              artistsView.length === 0 ? (
                <div className="text-center py-32 text-neutral-600">
                  <p className="text-2xl mb-2">♪</p>
                  <p>No artists match your filters.</p>
                </div>
              ) : (
                <div className="divide-y divide-neutral-900/60">
                  {artistsView.map(({ artist, count }, i) => (
                    <button
                      key={artist}
                      onClick={() => { setView("songs"); handleArtistClick(artist); }}
                      className="w-full flex items-center gap-3 px-4 sm:px-6 py-3 hover:bg-neutral-900 transition-colors text-left group"
                    >
                      <span className="text-xs text-neutral-700 w-8 text-right tabular-nums shrink-0 group-hover:text-neutral-500">
                        {i + 1}
                      </span>
                      <span className="flex-1 text-sm text-neutral-300 group-hover:text-white transition-colors">
                        {artist}
                      </span>
                      <span className="text-xs text-neutral-600 group-hover:text-neutral-400 tabular-nums shrink-0">
                        {count} {count === 1 ? "song" : "songs"}
                      </span>
                    </button>
                  ))}
                </div>
              )
            ) : paginated.length === 0 ? (
              <div className="text-center py-32 text-neutral-600">
                <p className="text-2xl mb-2">♪</p>
                <p>No songs match your search.</p>
              </div>
            ) : (
              <div className="grid gap-1 px-2 py-3 sm:px-4">
                {paginated.map((song) => (
                  <SongCard
                    key={song.id}
                    song={song}
                    artistCount={artistCounts[normalize(song.artist)] ?? 1}
                    playCount={songPlayCounts[`${normalize(song.artist)}|||${normalize(song.title)}`] ?? 1}
                    onArtistClick={handleArtistClick}
                    onGenreClick={handleGenreClick}
                    onReleaseYearClick={handleReleaseYearClick}
                    onSpotifyResult={handleSpotifyResult}
                    isActive={activePlayId === song.id}
                    onSetActive={() => setActivePlayId(song.id)}
                    onNext={() => handleNext(song.id)}
                    autoPlay={autoPlay}
                    onAutoPlayToggle={() => setAutoPlay(v => !v)}
                  />
                ))}
              </div>
            )}
          </main>

          {/* Pagination — songs view only */}
          {!loading && view === "songs" && totalPages > 1 && (
            <div className="border-t border-neutral-800 px-4 py-4 sm:px-6">
              <div className="flex items-center justify-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-sm text-neutral-300 hover:bg-neutral-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  ← Prev
                </button>
                <span className="text-sm text-neutral-500 px-2">{page} / {totalPages}</span>
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
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-neutral-800 px-4 py-4 sm:px-8 text-center text-xs text-neutral-700">
        <a href="https://www.rnz.co.nz" target="_blank" rel="noopener noreferrer" className="hover:text-neutral-500 transition-colors">
          Data sourced from RNZ archives
        </a>{" "}
        &middot; radomski.co.nz
      </footer>
    </div>
  );
}
