"use client";

import { useState, useEffect } from "react";
import { Song } from "./Explorer";

function formatAirDate(song: Song): string {
  if (song.broadcast_date) {
    return new Date(song.broadcast_date + "T00:00:00").toLocaleDateString(
      "en-NZ",
      { day: "numeric", month: "short", year: "numeric" }
    );
  }
  const match = song.show_date.match(
    /(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(.+)/i
  );
  if (match) return match[1];
  return song.show_date.replace(/^Matinee Idle for\s*/i, "");
}

function Count({ n, title }: { n: number; title: string }) {
  if (n <= 1) return null;
  return (
    <span title={title} className="inline-block rounded px-1.5 py-0.5 text-[10px] font-medium bg-neutral-800 text-neutral-500 leading-none select-none">
      {n}
    </span>
  );
}

function cacheKey(artist: string, title: string) {
  return `matinee-spotify:${artist.toLowerCase()}|||${title.toLowerCase()}`;
}

type SpotifyState = "idle" | "loading" | "found" | "not_found";

export default function SongCard({
  song,
  artistCount,
  playCount,
  onArtistClick,
  onGenreClick,
  onReleaseYearClick,
  onSpotifyResult,
}: {
  song: Song;
  artistCount: number;
  playCount: number;
  onArtistClick: (artist: string) => void;
  onGenreClick: (genre: string) => void;
  onReleaseYearClick: (year: number) => void;
  onSpotifyResult: (artist: string, title: string, url: string) => void;
}) {
  const [spotifyState, setSpotifyState] = useState<SpotifyState>(
    song.spotify_url ? "found" : "idle"
  );

  // Pre-populate from localStorage on mount
  useEffect(() => {
    if (song.spotify_url) return;
    const cached = localStorage.getItem(cacheKey(song.artist, song.title));
    if (cached) {
      onSpotifyResult(song.artist, song.title, cached);
      setSpotifyState("found");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync state when song.spotify_url updates from parent
  useEffect(() => {
    if (song.spotify_url) setSpotifyState("found");
  }, [song.spotify_url]);

  async function handleSpotifyClick() {
    // Already have URL — open it
    if (song.spotify_url) {
      window.open(song.spotify_url, "_blank", "noopener,noreferrer");
      return;
    }

    // Check localStorage
    const cached = localStorage.getItem(cacheKey(song.artist, song.title));
    if (cached) {
      window.open(cached, "_blank", "noopener,noreferrer");
      return;
    }

    // Fetch from API
    setSpotifyState("loading");
    try {
      const params = new URLSearchParams({ artist: song.artist, title: song.title });
      const resp = await fetch(`/api/spotify?${params}`);
      if (!resp.ok) {
        setSpotifyState("not_found");
        return;
      }
      const data = await resp.json();
      const url: string = data.spotify_url;
      localStorage.setItem(cacheKey(song.artist, song.title), url);
      onSpotifyResult(song.artist, song.title, url);
      setSpotifyState("found");
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      setSpotifyState("not_found");
    }
  }

  const spotifyTitle =
    spotifyState === "loading" ? "Searching Spotify…" :
    spotifyState === "not_found" ? "Not found on Spotify" :
    "Open in Spotify";

  const spotifyColor =
    spotifyState === "found" ? "text-green-400" :
    spotifyState === "not_found" ? "text-neutral-700 cursor-not-allowed" :
    spotifyState === "loading" ? "text-neutral-600" :
    "text-neutral-600 hover:text-green-400";

  return (
    <div className="group flex items-start gap-4 rounded-lg px-4 py-3 hover:bg-neutral-900 transition-colors">
      {/* Year badge */}
      <div className="shrink-0 w-10 text-center mt-0.5">
        <span className="text-xs font-mono text-neutral-600 group-hover:text-neutral-500 transition-colors">
          {song.air_year ?? "—"}
        </span>
      </div>

      {/* Main info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => onArtistClick(song.artist)}
            className="font-semibold text-white text-sm leading-snug hover:text-neutral-300 hover:underline transition-colors text-left"
          >
            {song.artist}
          </button>
          <Count n={artistCount} title={`${artistCount} songs by this artist`} />
          <span className="text-neutral-500 text-xs">—</span>
          <span className="text-neutral-300 text-sm leading-snug">
            {song.title}
          </span>
          <Count n={playCount} title={`Played ${playCount} times on the show`} />
        </div>
        <div className="mt-0.5 flex items-center gap-2 flex-wrap text-xs text-neutral-600">
          <span>Played {formatAirDate(song)}</span>
          {song.release_year && (
            <>
              <span>·</span>
              <button
                onClick={() => onReleaseYearClick(song.release_year!)}
                className="hover:text-neutral-400 hover:underline transition-colors"
              >
                Released {song.release_year}
              </button>
            </>
          )}
          {song.mb_release && (
            <>
              <span>·</span>
              <span className="italic">{song.mb_release}</span>
            </>
          )}
          {song.genre && (
            <>
              <span>·</span>
              <button
                onClick={() => onGenreClick(song.genre!)}
                className="hover:text-neutral-400 hover:underline transition-colors"
              >
                {song.genre}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Spotify button */}
      <button
        onClick={handleSpotifyClick}
        disabled={spotifyState === "loading" || spotifyState === "not_found"}
        className={`shrink-0 transition-colors opacity-0 group-hover:opacity-100 ${spotifyColor}`}
        aria-label={spotifyTitle}
        title={spotifyTitle}
      >
        {spotifyState === "loading" ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="animate-spin">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="40 20" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
          </svg>
        )}
      </button>
    </div>
  );
}
