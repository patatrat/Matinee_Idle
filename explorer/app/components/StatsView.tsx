"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { GENRE_HEX, FALLBACK_HEX } from "../lib/genres";

declare global {
  interface Window {
    umami?: { track: (event: string, data?: Record<string, unknown>) => void };
  }
}

export interface StatsData {
  totalPlays:        number;
  uniqueArtistCount: number;
  spotifyCount:      number;
  songsPerYear:      { year: string; count: number }[];
  genreBreakdown:    { genre: string; count: number }[];
  releaseDecades:    { label: string; lo: number; count: number }[];
  topSongs:          { label: string; rawArtist: string; count: number }[];
  topArtistStats:    { label: string; count: number }[];
  discoveryLag:      { label: string; count: number }[];
}

interface StatsViewProps {
  stats: StatsData;
  onGenreClick:  (genre: string) => void;
  onArtistClick: (artist: string) => void;
  onYearClick:   (year: string) => void;
  onDecadeClick: (lo: number) => void;
}

const TICK        = { fill: "#737373", fontSize: 11 };
const AXIS_PROPS  = { axisLine: false as const, tickLine: false as const };
const TOOLTIP_PROPS = {
  contentStyle: {
    background: "#171717", border: "1px solid #404040",
    borderRadius: 6, fontSize: 12, color: "#d4d4d4",
  },
  itemStyle:  { color: "#d4d4d4" },
  labelStyle: { color: "#a3a3a3" },
  cursor:     { fill: "rgba(255,255,255,0.04)" },
};

function ChartSection({ title, children, span2 = false }: {
  title: string; children: React.ReactNode; span2?: boolean;
}) {
  return (
    <section className={span2 ? "xl:col-span-2" : ""}>
      <h2 className="text-[10px] uppercase tracking-widest text-neutral-500 font-semibold mb-3">
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function StatsView({ stats, onGenreClick, onArtistClick, onYearClick, onDecadeClick }: StatsViewProps) {
  const { totalPlays, uniqueArtistCount, spotifyCount,
          songsPerYear, genreBreakdown, releaseDecades,
          topSongs, topArtistStats, discoveryLag } = stats;

  return (
    <div className="p-4 sm:p-6 space-y-8">
      {/* Headline stat pills */}
      <div className="flex flex-wrap gap-3">
        {[
          { label: "Total plays",    value: totalPlays.toLocaleString() },
          { label: "Unique artists", value: uniqueArtistCount.toLocaleString() },
          { label: "Seasons",        value: "22  (2005–2026)" },
          { label: "Spotify links",  value: spotifyCount.toLocaleString() },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl border border-neutral-800 bg-neutral-900/60 px-4 py-3 min-w-[120px]">
            <p className="text-[10px] uppercase tracking-widest text-neutral-500 mb-0.5">{label}</p>
            <p className="text-xl font-bold text-white tabular-nums">{value}</p>
          </div>
        ))}
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">

        {/* 1. Songs per year */}
        <ChartSection title="Songs played per season">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={songsPerYear} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
              <XAxis dataKey="year" tick={TICK} {...AXIS_PROPS} interval={1} />
              <YAxis tick={TICK} {...AXIS_PROPS} width={40} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="plays" fill="#f59e0b" radius={[2, 2, 0, 0]}
                cursor="pointer" onClick={(d) => { const year = (d as unknown as { year: string }).year; window.umami?.track("chart-interaction", { chart: "songs-per-year", value: year }); onYearClick(year); }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        {/* 2. Release decade */}
        <ChartSection title="Release decade of songs played">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={releaseDecades} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
              <XAxis dataKey="label" tick={TICK} {...AXIS_PROPS} />
              <YAxis tick={TICK} {...AXIS_PROPS} width={40} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="songs" fill="#a3a3a3" radius={[2, 2, 0, 0]}
                cursor="pointer" onClick={(d) => { const lo = (d as unknown as { lo: number }).lo; window.umami?.track("chart-interaction", { chart: "release-decade", value: String(lo) }); onDecadeClick(lo); }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        {/* 3. Discovery lag */}
        <ChartSection title="Discovery lag — how old were songs when played?">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={discoveryLag} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
              <XAxis dataKey="label" tick={{ ...TICK, fontSize: 10 }} {...AXIS_PROPS} />
              <YAxis tick={TICK} {...AXIS_PROPS} width={40} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="songs" fill="#818cf8" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        {/* 4. Genre breakdown */}
        <ChartSection title="Plays by genre">
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={genreBreakdown} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 0 }}>
              <XAxis type="number" tick={TICK} {...AXIS_PROPS} />
              <YAxis type="category" dataKey="genre" tick={{ ...TICK, fontSize: 10 }} {...AXIS_PROPS} width={100} interval={0} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="songs" radius={[0, 2, 2, 0]}
                cursor="pointer" onClick={(d) => { const genre = (d as unknown as { genre: string }).genre; window.umami?.track("chart-interaction", { chart: "genre-breakdown", value: genre }); onGenreClick(genre); }}>
                {genreBreakdown.map(({ genre }) => (
                  <Cell key={genre} fill={GENRE_HEX[genre] ?? FALLBACK_HEX} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        {/* 5. Top 20 artists */}
        <ChartSection title="Top 20 most-featured artists">
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={topArtistStats} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 0 }}>
              <XAxis type="number" tick={TICK} {...AXIS_PROPS} />
              <YAxis type="category" dataKey="label" tick={{ ...TICK, fontSize: 10 }} {...AXIS_PROPS} width={120} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="plays" fill="#f59e0b" radius={[0, 2, 2, 0]}
                cursor="pointer" onClick={(d) => { const label = (d as unknown as { label: string }).label; window.umami?.track("chart-interaction", { chart: "top-artists", value: label }); onArtistClick(label); }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

        {/* 6. Top 20 songs */}
        <ChartSection title="Top 20 most-played songs">
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={topSongs} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 0 }}>
              <XAxis type="number" tick={TICK} {...AXIS_PROPS} />
              <YAxis type="category" dataKey="label" tick={{ ...TICK, fontSize: 9 }} {...AXIS_PROPS} width={160} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="plays" fill="#f59e0b" radius={[0, 2, 2, 0]}
                cursor="pointer" onClick={(d) => { const rawArtist = (d as unknown as { rawArtist: string }).rawArtist; window.umami?.track("chart-interaction", { chart: "top-songs", value: rawArtist }); onArtistClick(rawArtist); }} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>

      </div>
    </div>
  );
}
