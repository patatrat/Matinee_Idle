import type { NextRequest } from "next/server";

const CLIENT_ID = "f3bcd797aeaa4a50bcb6132366835d64";
const CLIENT_SECRET = "30e26fd9d30844d08b94dced12fe380d";

let token = "";
let tokenExpiry = 0;

async function getToken(): Promise<string> {
  if (token && Date.now() < tokenExpiry - 60_000) return token;
  const creds = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
  const resp = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      Authorization: `Basic ${creds}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: "grant_type=client_credentials",
  });
  const data = await resp.json();
  token = data.access_token;
  tokenExpiry = Date.now() + data.expires_in * 1000;
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
    const resp = await fetch(
      `https://api.spotify.com/v1/search?${params}`,
      { headers }
    );
    if (!resp.ok) continue;
    const data = await resp.json();
    const tracks: SpotifyTrack[] = data?.tracks?.items ?? [];
    if (!tracks.length) continue;

    // Pick best match by token overlap
    let best: { score: number; url: string } | null = null;
    for (const track of tracks) {
      const artistSim = Math.max(
        ...track.artists.map((a) => similarity(artist, a.name))
      );
      const titleSim = similarity(title, track.name);
      const score = artistSim * 0.5 + titleSim * 0.5;
      if (!best || score > best.score) {
        best = { score, url: track.external_urls.spotify };
      }
    }
    if (best && best.score >= 0.5) return best.url;
  }

  return null;
}

export async function GET(request: NextRequest) {
  const artist = request.nextUrl.searchParams.get("artist") ?? "";
  const title = request.nextUrl.searchParams.get("title") ?? "";

  if (!artist || !title) {
    return Response.json({ error: "artist and title required" }, { status: 400 });
  }

  try {
    const url = await searchSpotify(artist, title);
    if (!url) {
      return Response.json({ error: "not found" }, { status: 404 });
    }
    return Response.json({ spotify_url: url });
  } catch {
    return Response.json({ error: "search failed" }, { status: 500 });
  }
}
