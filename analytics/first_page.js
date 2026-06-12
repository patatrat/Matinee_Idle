// Replicates Explorer.tsx default view: sort by times-played, exact dedup,
// then normalized dedup, first PAGE_SIZE entries.
const fs = require("fs");
const songs = JSON.parse(fs.readFileSync("/Users/patrickradomski/projects/Matinee_Idle/explorer/public/songs.json", "utf8"));

const PAGE_SIZE = 50;
const normalize = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
const normalizeArtistKey = (name) =>
  normalize(
    name
      .replace(/\b(feat\.?|ft\.?|featuring|with)\s+/gi, " ")
      .replace(/\s+(&|and|\+)\s+/gi, " ")
  );

const list = Array.isArray(songs) ? songs : songs.songs;

// songPlayCounts: keyed normalizeArtistKey(artist)|||normalize(title)
const counts = {};
for (const s of list) {
  const key = `${normalizeArtistKey(s.artist)}|||${normalize(s.title)}`;
  counts[key] = (counts[key] ?? 0) + 1;
}

// times-played sort — NOTE: lookup uses normalize(artist), not normalizeArtistKey
let result = [...list].sort(
  (a, b) =>
    (counts[`${normalize(b.artist)}|||${normalize(b.title)}`] ?? 1) -
    (counts[`${normalize(a.artist)}|||${normalize(a.title)}`] ?? 1)
);

// exact dedup
let seen = new Set();
result = result.filter((s) => {
  const key = `${s.artist}|||${s.title}`;
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});

// normalized dedup (deduped memo)
seen = new Set();
result = result.filter((s) => {
  const key = `${normalizeArtistKey(s.artist)}|||${normalizeArtistKey(s.title)}`;
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});

const firstPage = result.slice(0, PAGE_SIZE).map((s) => ({
  artist: s.artist,
  title: s.title,
  key: `${normalizeArtistKey(s.artist)}|||${normalizeArtistKey(s.title)}`,
  radio_plays: counts[`${normalizeArtistKey(s.artist)}|||${normalize(s.title)}`],
}));

fs.writeFileSync("/tmp/first_page.json", JSON.stringify(firstPage, null, 2));
console.log(firstPage.map((s, i) => `${i + 1}. ${s.artist} — ${s.title} (${s.radio_plays})`).join("\n"));
