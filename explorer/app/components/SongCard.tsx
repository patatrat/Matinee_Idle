"use client";

import { useState, useEffect, useRef } from "react";
import { Song } from "./Explorer";
import { GENRE_CONFIG, FALLBACK_BAR } from "../lib/genres";

declare global {
  interface Window {
    umami?: { track: (event: string, data?: Record<string, unknown>) => void };
  }
}

// Split a credited artist into individual names for separate clickable links.
// Returns the original single-item array when no collaboration markers are found.
function splitArtistParts(name: string): string[] {
  const cleaned = name.replace(/\s*\([^)]*\)/g, "").trim();
  let parts = cleaned.split(/\s*(?:feat\.?|ft\.?|featuring)\s*/i);
  parts = parts.flatMap(p => p.split(/\s+with\s+/i));
  parts = parts.flatMap(p => p.split(/\s*&\s*/));
  parts = parts.flatMap(p =>
    p.split(/\s+and\s+(?!(?:the|a|an|his|her|their|de|le|la|los|el|all|friends|more|others)\b)/i)
  );
  const result = parts.map(p => p.trim()).filter(p => p.length >= 4 && /[a-zA-Z]/.test(p));
  return result.length > 1 ? result : [name];
}

function trackPlay(song: Song) {
  const props: Record<string, string> = {
    artist: song.artist,
    title: song.title,
  };
  if (song.genre) props.genre = song.genre;
  if (song.release_year) props.release_year = String(song.release_year);
  if (song.air_year) props.air_year = String(song.air_year);
  window.umami?.track("song-play", props);
}

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
      ×{n}
    </span>
  );
}

function cacheKey(artist: string, title: string) {
  return `matinee-spotify:${artist.toLowerCase()}|||${title.toLowerCase()}`;
}

type SpotifyState = "idle" | "loading" | "found" | "not_found" | "error";

export default function SongCard({
  song,
  artistCount,
  playCount,
  onArtistClick,
  onGenreClick,
  onReleaseYearClick,
  onSpotifyResult,
  isActive = false,
  onSetActive,
  onNext,
  autoPlay = false,
  onAutoPlayToggle,
}: {
  song: Song;
  artistCount: number;
  playCount: number;
  onArtistClick: (artist: string) => void;
  onGenreClick: (genre: string) => void;
  onReleaseYearClick: (year: number) => void;
  onSpotifyResult: (artist: string, title: string, url: string) => void;
  isActive?: boolean;
  onSetActive?: () => void;
  onNext?: () => void;
  autoPlay?: boolean;
  onAutoPlayToggle?: () => void;
}) {
  const [spotifyState, setSpotifyState] = useState<SpotifyState>(
    song.spotify_url ? "found" : "idle"
  );
  const [showEmbed, setShowEmbed] = useState(false);
  const [autoStarted, setAutoStarted] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  // Prevents double-firing: manual click tracks play then sets this true so
  // the isActive effect (which fires immediately after) knows to skip.
  const didTrackRef = useRef(false);

  useEffect(() => {
    if (song.spotify_url) return;
    const cached = localStorage.getItem(cacheKey(song.artist, song.title));
    if (cached) {
      onSpotifyResult(song.artist, song.title, cached);
      setSpotifyState("found");
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (song.spotify_url) setSpotifyState("found");
  }, [song.spotify_url]);

  // When this card becomes active (via auto-advance), open embed with autoplay;
  // when it loses active, close the embed.
  useEffect(() => {
    if (isActive && song.spotify_url) {
      setAutoStarted(autoPlay);
      setShowEmbed(true);
      // Only track if the manual click path didn't already do it
      if (!didTrackRef.current) trackPlay(song);
      didTrackRef.current = false;
    } else if (!isActive) {
      setAutoStarted(false);
      setShowEmbed(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // Listen for Spotify embed postMessage events to detect track end for auto-play
  useEffect(() => {
    if (!showEmbed || !trackId || !onNext || !autoPlay) return;

    let nearEnd = false;

    function handleMessage(event: MessageEvent) {
      if (event.origin !== "https://open.spotify.com") return;
      let data: { type?: string; payload?: { duration?: number; position?: number; isPaused?: boolean } };
      try {
        data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      } catch { return; }
      if (data?.type !== "playback_update") return;

      const { duration, position, isPaused } = data.payload ?? {};
      if (!duration || position == null) return;

      // Flag when we're in the last 3 seconds
      if (position >= duration - 3000) nearEnd = true;

      // Track ended: was near end and now paused (either at end or after position reset)
      if (nearEnd && isPaused && (position < 1500 || position >= duration - 500)) {
        nearEnd = false;
        onNext!();
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [showEmbed, song.spotify_url, autoPlay, onNext]);

  function handleIframeLoad() {
    if (!autoStarted || !iframeRef.current?.contentWindow) return;
    // Wait for the embed to authenticate the user's Spotify session before
    // sending the play command. autoplay=1 in the URL fires before auth
    // completes and falls back to 30s preview even for Premium users.
    // 1500ms is enough for the embed JS to load and complete auth on most connections.
    setTimeout(() => {
      iframeRef.current?.contentWindow?.postMessage({ command: "play" }, "https://open.spotify.com");
    }, 1500);
  }

  function openSpotifySearch() {
    const q = encodeURIComponent(`${song.artist} ${song.title}`);
    window.open(`https://open.spotify.com/search/${q}`, "_blank", "noopener,noreferrer");
  }

  async function handleSpotifyClick() {
    if (spotifyState === "loading") return;

    if (song.spotify_url) {
      const next = !showEmbed;
      setAutoStarted(false); // manual click — don't autostart
      setShowEmbed(next);
      if (next) {
        didTrackRef.current = true;
        trackPlay(song);
        onSetActive?.();
      }
      return;
    }

    const cached = localStorage.getItem(cacheKey(song.artist, song.title));
    if (cached) {
      window.open(cached, "_blank", "noopener,noreferrer");
      return;
    }

    setSpotifyState("loading");
    window.umami?.track("spotify-lookup", { query: `${song.artist} – ${song.title}` });
    try {
      const params = new URLSearchParams({ artist: song.artist, title: song.title });
      const resp = await fetch(`/api/spotify?${params}`);
      if (resp.status === 404) {
        setSpotifyState("not_found");
        return;
      }
      if (!resp.ok) {
        openSpotifySearch();
        setSpotifyState("error");
        return;
      }
      const data = await resp.json();
      const url: string = data.spotify_url;
      localStorage.setItem(cacheKey(song.artist, song.title), url);
      onSpotifyResult(song.artist, song.title, url);
      setSpotifyState("found");
      setShowEmbed(true);
      didTrackRef.current = true;
      trackPlay(song);
      onSetActive?.();
    } catch {
      openSpotifySearch();
      setSpotifyState("error");
    }
  }

  const genreBar = song.genre ? (GENRE_CONFIG[song.genre]?.bar ?? FALLBACK_BAR) : FALLBACK_BAR;
  const genrePill = song.genre ? GENRE_CONFIG[song.genre]?.pill : undefined;

  const spotifyTitle =
    spotifyState === "loading"   ? "Searching Spotify…" :
    spotifyState === "not_found" ? "Not found on Spotify" :
    spotifyState === "error"     ? "Search failed — click to retry" :
    song.spotify_url             ? (showEmbed ? "Hide player" : "Show player") :
    "Find on Spotify";

  const spotifyIconColor =
    spotifyState === "found"     ? "text-green-400 hover:text-green-300" :
    spotifyState === "not_found" ? "text-neutral-700 cursor-not-allowed" :
    spotifyState === "loading"   ? "text-neutral-600" :
    spotifyState === "error"     ? "text-amber-500 hover:text-amber-400" :
    "text-neutral-500 hover:text-green-400";

  const trackId = song.spotify_url?.split("/track/")[1]?.split("?")[0];

  return (
    <div className={`group flex gap-3 rounded-xl px-3 py-3 transition-colors ${
      isActive ? "bg-neutral-800/80" : "hover:bg-neutral-900"
    }`}>
      {/* Genre colour bar */}
      <div className={`w-1 self-stretch rounded-full shrink-0 ${genreBar} opacity-70 group-hover:opacity-100 transition-opacity`} />

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Row 1: Artist(s) + count badge — collaborations split into individual links */}
        <div className="flex items-center gap-1 flex-wrap">
          {splitArtistParts(song.artist).map((part, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <span className="text-neutral-700 select-none">·</span>}
              <button
                onClick={() => onArtistClick(part)}
                className="text-sm font-semibold text-neutral-400 hover:text-neutral-200 hover:underline transition-colors text-left leading-snug"
              >
                {part}
              </button>
            </span>
          ))}
          <Count n={artistCount} title={`${artistCount} songs by this artist`} />
        </div>

        {/* Row 2: Title + Spotify icon (inline) + play count */}
        <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
          <button
            onClick={handleSpotifyClick}
            title={spotifyTitle}
            className="text-base font-medium text-neutral-100 hover:underline text-left leading-snug"
          >
            {song.title}
          </button>
          <button
            onClick={handleSpotifyClick}
            disabled={spotifyState === "loading" || spotifyState === "not_found"}
            className={`shrink-0 transition-colors ${spotifyIconColor}`}
            aria-label={spotifyTitle}
            title={spotifyTitle}
          >
            {spotifyState === "loading" ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="animate-spin">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="40 20" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
              </svg>
            )}
          </button>
          <Count n={playCount} title={`Played ${playCount} times on the show`} />
        </div>

        {/* Row 3: Metadata */}
        <div className="mt-1 flex items-center gap-2 flex-wrap text-xs text-neutral-600">
          {song.mb_release && (
            <span className="italic">{song.mb_release}</span>
          )}
          {song.release_year && (
            <>
              {song.mb_release && <span>·</span>}
              <button
                onClick={() => onReleaseYearClick(song.release_year!)}
                className="hover:text-neutral-400 hover:underline transition-colors"
              >
                {song.release_year}
              </button>
            </>
          )}
          {song.genre && genrePill && (
            <>
              <span>·</span>
              <button
                onClick={() => onGenreClick(song.genre!)}
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium leading-none transition-opacity hover:opacity-80 ${genrePill}`}
              >
                {song.genre}
              </button>
            </>
          )}
        </div>

        {/* Spotify embed */}
        {showEmbed && trackId && (
          <div className="mt-2 space-y-1.5">
            <iframe
              ref={iframeRef}
              onLoad={handleIframeLoad}
              src={`https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0`}
              width="100%"
              height="80"
              frameBorder="0"
              allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
              loading="eager"
              className="rounded-lg"
            />
            <div className="flex items-center gap-3 px-0.5">
              {onNext && (
                <button
                  onClick={onNext}
                  className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 18V6l12 6-12 6zm14-12v12h2V6h-2z"/>
                  </svg>
                  Next track
                </button>
              )}
              {onAutoPlayToggle && (
                <button
                  onClick={onAutoPlayToggle}
                  title={autoPlay ? "Auto-play on — click to turn off" : "Auto-play off — click to turn on"}
                  className={`flex items-center gap-1.5 text-xs transition-colors ${
                    autoPlay ? "text-green-400 hover:text-green-300" : "text-neutral-600 hover:text-neutral-400"
                  }`}
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                  Auto-play {autoPlay ? "on" : "off"}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
