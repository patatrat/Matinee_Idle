"use client";

import { GENRE_CONFIG, SORTED_GENRES } from "../lib/genres";

type SortBy = "date-played" | "times-played" | "date-released";

const DECADES = [
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

interface FilterSidebarProps {
  query: string;
  onQueryChange: (v: string) => void;
  artistFilter: string;
  onArtistChange: (v: string) => void;
  yearFilter: string;
  onYearChange: (v: string) => void;
  years: number[];
  decadeFilter: number | null;
  onDecadeChange: (lo: number | null) => void;
  genreFilters: Set<string>;
  onGenreToggle: (genre: string) => void;
  sortBy: SortBy;
  onSortChange: (v: SortBy) => void;
  onRandom: () => void;
  onClearAll: () => void;
  activeFilterCount: number;
  topArtists: { artist: string; count: number }[];
  onTopArtistClick: (artist: string) => void;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] uppercase tracking-widest text-neutral-600 font-semibold mb-2 mt-5 first:mt-0">
      {children}
    </p>
  );
}

export default function FilterSidebar({
  query, onQueryChange,
  artistFilter, onArtistChange,
  yearFilter, onYearChange, years,
  decadeFilter, onDecadeChange,
  genreFilters, onGenreToggle,
  sortBy, onSortChange,
  onRandom, onClearAll,
  activeFilterCount,
  topArtists, onTopArtistClick,
}: FilterSidebarProps) {
  const SORT_OPTIONS: { value: SortBy; label: string }[] = [
    { value: "date-played",   label: "Date played"  },
    { value: "times-played",  label: "Times played" },
    { value: "date-released", label: "Date released"},
  ];

  return (
    <div className="flex flex-col gap-0 px-4 py-5">
      {/* Search */}
      <SectionLabel>Search</SectionLabel>
      <input
        type="search"
        placeholder="Artist, title, album…"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        className="w-full rounded-lg bg-neutral-900 border border-neutral-800 px-3 py-2 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-600 focus:ring-1 focus:ring-neutral-600"
      />

      {/* Artist */}
      <SectionLabel>Artist</SectionLabel>
      <div className="relative">
        <input
          type="text"
          placeholder="Filter by artist…"
          value={artistFilter}
          onChange={(e) => onArtistChange(e.target.value)}
          className="w-full rounded-lg bg-neutral-900 border border-neutral-800 px-3 py-2 pr-7 text-sm text-white placeholder-neutral-600 focus:outline-none focus:border-neutral-600 focus:ring-1 focus:ring-neutral-600"
        />
        {artistFilter && (
          <button
            onClick={() => onArtistChange("")}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white text-sm leading-none"
            aria-label="Clear artist filter"
          >
            ×
          </button>
        )}
      </div>

      {/* Sort */}
      <SectionLabel>Sort by</SectionLabel>
      <div className="flex flex-col gap-1">
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onSortChange(opt.value)}
            className="flex items-center gap-2 text-sm text-left hover:text-white transition-colors"
          >
            <span className={`w-2 h-2 rounded-full border flex-shrink-0 ${
              sortBy === opt.value
                ? "bg-amber-400 border-amber-400"
                : "border-neutral-600"
            }`} />
            <span className={sortBy === opt.value ? "text-white" : "text-neutral-500"}>
              {opt.label}
            </span>
          </button>
        ))}
      </div>

      {/* Year played */}
      <SectionLabel>Year played</SectionLabel>
      <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto sidebar-scroll">
        <button
          onClick={() => onYearChange("all")}
          className={`rounded px-2 py-0.5 text-xs transition-colors ${
            yearFilter === "all"
              ? "bg-neutral-700 text-white"
              : "text-neutral-500 hover:text-neutral-300"
          }`}
        >
          All
        </button>
        {years.map((y) => (
          <button
            key={y}
            onClick={() => onYearChange(String(y))}
            className={`rounded px-2 py-0.5 text-xs transition-colors ${
              yearFilter === String(y)
                ? "bg-neutral-700 text-white"
                : "text-neutral-500 hover:text-neutral-300"
            }`}
          >
            {y}
          </button>
        ))}
      </div>

      {/* Decade (release year) */}
      <SectionLabel>Release decade</SectionLabel>
      <div className="flex flex-wrap gap-1">
        {DECADES.map((d) => (
          <button
            key={d.lo}
            onClick={() => onDecadeChange(decadeFilter === d.lo ? null : d.lo)}
            className={`rounded px-2 py-0.5 text-xs transition-colors ${
              decadeFilter === d.lo
                ? "bg-neutral-700 text-white"
                : "text-neutral-500 hover:text-neutral-300"
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      {/* Genre */}
      <SectionLabel>Genre</SectionLabel>
      <div className="flex flex-wrap gap-1">
        {SORTED_GENRES.map((genre) => {
          const cfg = GENRE_CONFIG[genre];
          const active = genreFilters.has(genre);
          return (
            <button
              key={genre}
              onClick={() => onGenreToggle(genre)}
              className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs transition-colors ${
                active
                  ? "bg-neutral-700 text-white ring-1 ring-neutral-500"
                  : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
              {genre}
            </button>
          );
        })}
      </div>

      {/* Top Artists */}
      <SectionLabel>Top artists</SectionLabel>
      <div className="flex flex-col gap-0.5">
        {topArtists.map(({ artist, count }) => (
          <button
            key={artist}
            onClick={() => onTopArtistClick(artist)}
            className={`flex items-center justify-between rounded px-2 py-1 text-xs text-left transition-colors group ${
              artistFilter === artist
                ? "bg-neutral-800 text-white"
                : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900"
            }`}
          >
            <span className="truncate">{artist}</span>
            <span className="ml-2 shrink-0 text-neutral-700 group-hover:text-neutral-500">{count}</span>
          </button>
        ))}
      </div>

      {/* Actions */}
      <div className="mt-6 flex flex-col gap-2">
        <button
          onClick={onRandom}
          className="w-full rounded-lg border border-neutral-800 bg-neutral-900 py-2 text-sm text-neutral-400 hover:bg-neutral-800 hover:text-white transition-colors"
        >
          ⚄ Random song
        </button>
        {activeFilterCount > 0 && (
          <button
            onClick={onClearAll}
            className="w-full rounded-lg border border-neutral-800 py-2 text-xs text-neutral-600 hover:text-neutral-400 transition-colors"
          >
            Clear all filters ({activeFilterCount})
          </button>
        )}
      </div>
    </div>
  );
}
