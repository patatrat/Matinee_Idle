import type { NextRequest } from "next/server";

const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID ?? "";
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET ?? "";

let token = "";
let tokenExpiry = 0;

async function getToken(): Promise<string> {
  if (token && Date.now() < tokenExpiry - 60_000) {
    console.log("[spotify] reusing cached token");
    return token;
  }
  console.log("[spotify] fetching new token");
  const creds = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
  const resp = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${creds}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: "grant_type=client_credentials",
  });
  if (!resp.ok) {
    const body = await resp.text();
    console.error(`[spotify] token fetch failed: ${resp.status} ${body}`);
    throw new Error(`token fetch failed: ${resp.status}`);
  }
  const data = await resp.json();
  token = data.access_token;
  tokenExpiry = Date.now() + data.expires_in * 1000;
  console.log(`[spotify] token obtained, expires in ${data.expires_in}s`);
  return token;
}

function normalize(s: string): string {
  return s
    .toLowerCase()
    .replace(/\(.*?\)|\[.*?\]/g, "")
    .replace(/feat\.?.*$/i, "")
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function similarity(a: string, b: string): number {
  const ta = new Set(normalize(a).split(" ").filter(Boolean));
  const tb = new Set(normalize(b).split(" ").filter(Boolean));
  if (!ta.size || !tb.size) return 0;
  const intersection = [...ta].filter((w) => tb.has(w)).length;
  return intersection / Math.max(ta.size, tb.size);
}

interface SpotifyTrack {
  external_urls: { spotify: string };
  artists: { name: string }[];
  name: string;
}

class RateLimitError extends Error {
  retryAfter: number;
  constructor(retryAfter: number) {
    super(`rate limited, retry after ${retryAfter}s`);
    this.retryAfter = retryAfter;
  }
}

async function searchSpotify(
  artist: string,
  title: string
): Promise<string | null> {
  const tok = await getToken();
  const headers = { Authorization: `Bearer ${tok}` };

  const queries = [
    `artist:${artist} track:${title}`,
    `${artist} ${title}`,
  ];

  for (const q of queries) {
    const params = new URLSearchParams({ q, type: "track", limit: "5" });
    const url = `https://api.spotify.com/v1/search?${params}`;
    console.log(`[spotify] searching: ${q}`);
    const resp = await fetch(url, { headers });

    if (resp.status === 429) {
      const retryAfter = parseInt(resp.headers.get("Retry-After") ?? "5", 10);
      console.warn(`[spotify] rate limited, Retry-After: ${retryAfter}s`);
      throw new RateLimitError(retryAfter);
    }

    if (!resp.ok) {
      const body = await resp.text();
      console.error(`[spotify] search failed: ${resp.status} ${body}`);
      throw new Error(`search failed: ${resp.status}`);
    }

    const data = await resp.json();
    const tracks: SpotifyTrack[] = data?.tracks?.items ?? [];
    console.log(`[spotify] got ${tracks.length} results for query: ${q}`);

    if (!tracks.length) continue;

    let best: { score: number; url: string } | null = null;
    for (const track of tracks) {
      const artistSim = Math.max(
        ...track.artists.map((a) => similarity(artist, a.name))
      );
      const titleSim = similarity(title, track.name);
      const score = artistSim * 0.5 + titleSim * 0.5;
      console.log(
        `[spotify]   candidate: "${track.artists.map((a) => a.name).join(", ")}" — "${track.name}" score=${score.toFixed(2)}`
      );
      if (!best || score > best.score) {
        best = { score, url: track.external_urls.spotify };
      }
    }

    if (best && best.score >= 0.5) {
      console.log(`[spotify] matched with score=${best.score.toFixed(2)}: ${best.url}`);
      return best.url;
    }
    console.log(`[spotify] best score below threshold for query: ${q}`);
  }

  console.log(`[spotify] no match found for "${artist}" — "${title}"`);
  return null;
}

export async function GET(request: NextRequest) {
  const artist = request.nextUrl.searchParams.get("artist") ?? "";
  const title = request.nextUrl.searchParams.get("title") ?? "";

  console.log(`[spotify] lookup: artist="${artist}" title="${title}"`);

  if (!artist || !title) {
    return Response.json({ error: "artist and title required" }, { status: 400 });
  }

  try {
    const url = await searchSpotify(artist, title);
    if (!url) {
      return Response.json({ error: "not found" }, { status: 404 });
    }
    return Response.json({ spotify_url: url });
  } catch (err) {
    if (err instanceof RateLimitError) {
      return Response.json(
        { error: "rate_limited", retryAfter: err.retryAfter },
        { status: 429 }
      );
    }
    console.error("[spotify] unexpected error:", err);
    return Response.json({ error: "search failed" }, { status: 500 });
  }
}
