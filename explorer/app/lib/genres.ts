export interface GenreConfig {
  bar: string;
  dot: string;
  pill: string;
}

export const GENRE_CONFIG: Record<string, GenreConfig> = {
  "rock":             { bar: "bg-red-500",     dot: "bg-red-500",     pill: "bg-red-950 text-red-300"         },
  "classic rock":     { bar: "bg-orange-500",  dot: "bg-orange-500",  pill: "bg-orange-950 text-orange-300"   },
  "soul":             { bar: "bg-amber-500",   dot: "bg-amber-500",   pill: "bg-amber-950 text-amber-300"     },
  "pop":              { bar: "bg-pink-500",    dot: "bg-pink-500",    pill: "bg-pink-950 text-pink-300"       },
  "country":          { bar: "bg-yellow-600",  dot: "bg-yellow-600",  pill: "bg-yellow-950 text-yellow-300"   },
  "new wave":         { bar: "bg-cyan-500",    dot: "bg-cyan-500",    pill: "bg-cyan-950 text-cyan-300"       },
  "folk":             { bar: "bg-lime-600",    dot: "bg-lime-600",    pill: "bg-lime-950 text-lime-300"       },
  "jazz":             { bar: "bg-violet-500",  dot: "bg-violet-500",  pill: "bg-violet-950 text-violet-300"   },
  "blues":            { bar: "bg-blue-600",    dot: "bg-blue-600",    pill: "bg-blue-950 text-blue-300"       },
  "indie":            { bar: "bg-emerald-500", dot: "bg-emerald-500", pill: "bg-emerald-950 text-emerald-300" },
  "comedy":           { bar: "bg-yellow-400",  dot: "bg-yellow-400",  pill: "bg-yellow-950 text-yellow-300"   },
  "rockabilly":       { bar: "bg-orange-600",  dot: "bg-orange-600",  pill: "bg-orange-950 text-orange-300"   },
  "progressive rock": { bar: "bg-purple-500",  dot: "bg-purple-500",  pill: "bg-purple-950 text-purple-300"   },
  "funk":             { bar: "bg-fuchsia-500", dot: "bg-fuchsia-500", pill: "bg-fuchsia-950 text-fuchsia-300" },
  "punk":             { bar: "bg-rose-600",    dot: "bg-rose-600",    pill: "bg-rose-950 text-rose-300"       },
  "electronic":       { bar: "bg-sky-400",     dot: "bg-sky-400",     pill: "bg-sky-950 text-sky-300"         },
  "alternative":      { bar: "bg-teal-500",    dot: "bg-teal-500",    pill: "bg-teal-950 text-teal-300"       },
  "reggae":           { bar: "bg-green-600",   dot: "bg-green-600",   pill: "bg-green-950 text-green-300"     },
  "bluegrass":        { bar: "bg-lime-700",    dot: "bg-lime-700",    pill: "bg-lime-950 text-lime-300"       },
  "disco":            { bar: "bg-fuchsia-400", dot: "bg-fuchsia-400", pill: "bg-fuchsia-950 text-fuchsia-300" },
  "metal":            { bar: "bg-red-800",     dot: "bg-red-800",     pill: "bg-red-950 text-red-400"         },
  "hip-hop":          { bar: "bg-amber-400",   dot: "bg-amber-400",   pill: "bg-amber-950 text-amber-300"     },
  "world":            { bar: "bg-cyan-600",    dot: "bg-cyan-600",    pill: "bg-cyan-950 text-cyan-300"       },
  "classical":        { bar: "bg-stone-400",   dot: "bg-stone-400",   pill: "bg-stone-900 text-stone-300"     },
  "soundtrack":       { bar: "bg-indigo-500",  dot: "bg-indigo-500",  pill: "bg-indigo-950 text-indigo-300"   },
};

export const FALLBACK_BAR = "bg-neutral-800";

export const SORTED_GENRES = Object.keys(GENRE_CONFIG).sort();

export const GENRE_HEX: Record<string, string> = {
  "rock":             "#ef4444",
  "classic rock":     "#f97316",
  "soul":             "#f59e0b",
  "pop":              "#ec4899",
  "country":          "#ca8a04",
  "new wave":         "#06b6d4",
  "folk":             "#65a30d",
  "jazz":             "#8b5cf6",
  "blues":            "#2563eb",
  "indie":            "#10b981",
  "comedy":           "#facc15",
  "rockabilly":       "#ea580c",
  "progressive rock": "#a855f7",
  "funk":             "#d946ef",
  "punk":             "#e11d48",
  "electronic":       "#38bdf8",
  "alternative":      "#14b8a6",
  "reggae":           "#16a34a",
  "bluegrass":        "#4d7c0f",
  "disco":            "#e879f9",
  "metal":            "#991b1b",
  "hip-hop":          "#fbbf24",
  "world":            "#0891b2",
  "classical":        "#a8a29e",
  "soundtrack":       "#6366f1",
};

export const FALLBACK_HEX = "#404040";
