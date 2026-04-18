#!/usr/bin/env python3
"""
Maps the raw Last.fm genre tags to a clean canonical genre list.
Run after enrich_genres_lastfm.py. Reads/writes songs_enriched.json.
"""

import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

CANONICAL = {
    "rock", "classic rock", "soul", "pop", "country", "new wave", "folk",
    "jazz", "blues", "indie", "comedy", "rockabilly", "progressive rock",
    "funk", "punk", "electronic", "alternative", "reggae", "bluegrass",
    "disco", "metal", "hip-hop", "world", "classical", "soundtrack",
}

# Explicit tag → canonical mapping (longest/most specific match wins)
MAPPING = {
    # rock family
    "rock":              "rock",
    "hard rock":         "rock",
    "art rock":          "rock",
    "stoner rock":       "rock",
    "garage rock":       "rock",
    "garage":            "rock",
    "pub rock":          "rock",
    "surf rock":         "rock",
    "surf":              "rock",
    "southern rock":     "rock",
    "soft rock":         "rock",
    "piano rock":        "rock",
    "pop rock":          "rock",
    "pop/rock":          "rock",
    "rock and roll":     "rock",
    "rock n roll":       "rock",
    "rock'n'roll":       "rock",
    "rock & roll":       "rock",
    "beat":              "rock",
    "oldies":            "rock",
    "british invasion":  "rock",
    "mod":               "rock",
    "skiffle":           "rock",
    "hot rod":           "rock",
    "glam":              "rock",
    "glam rock":         "rock",

    # classic rock
    "classic rock":      "classic rock",
    "aor":               "classic rock",
    "arena rock":        "classic rock",

    # progressive rock
    "progressive rock":  "progressive rock",
    "prog rock":         "progressive rock",
    "progressive":       "progressive rock",
    "space rock":        "progressive rock",
    "jazz rock":         "progressive rock",
    "jazz-rock":         "progressive rock",
    "krautrock":         "progressive rock",
    "post-rock":         "progressive rock",
    "psychedelic rock":  "progressive rock",
    "psychedelic":       "progressive rock",
    "psych":             "progressive rock",

    # blues
    "blues":             "blues",
    "blues rock":        "blues",
    "country blues":     "blues",
    "rhythm and blues":  "blues",
    "delta blues":       "blues",
    "swamp pop":         "blues",

    # soul
    "soul":              "soul",
    "northern soul":     "soul",
    "motown":            "soul",
    "country soul":      "soul",
    "r&b":               "soul",
    "rnb":               "soul",
    "rhythm and blues":  "soul",

    # pop
    "pop":               "pop",
    "chamber pop":       "pop",
    "sunshine pop":      "pop",
    "baroque pop":       "pop",
    "art pop":           "pop",
    "dream pop":         "pop",
    "bubblegum":         "pop",
    "teen pop":          "pop",
    "easy listening":    "pop",
    "lounge":            "pop",
    "exotica":           "pop",
    "easy":              "pop",
    "mellow":            "pop",
    "early pop":         "pop",
    "general pop":       "pop",
    "instrumental pop":  "pop",
    "doo wop":           "pop",
    "doo-wop":           "pop",
    "doowop":            "pop",

    # country
    "country":           "country",
    "alt-country":       "country",
    "alternative country": "country",
    "country rock":      "country",
    "country pop":       "country",
    "country gospel":    "country",
    "new country":       "country",
    "outlaw country":    "country",
    "classic country":   "country",
    "western":           "country",
    "western swing":     "country",
    "tex-mex":           "country",
    "americana":         "country",
    "bluegrass":         "bluegrass",
    "zydeco":            "country",
    "cajun":             "country",
    "yodel":             "country",
    "scrumpy and western": "country",

    # folk
    "folk":              "folk",
    "folk rock":         "folk",
    "folk pop":          "folk",
    "indie folk":        "folk",
    "english folk":      "folk",
    "anti-folk":         "folk",
    "celtic":            "folk",
    "celtic rock":       "folk",
    "irish":             "folk",
    "scottish":          "folk",
    "acoustic":          "folk",
    "singer-songwriter": "folk",
    "sea shanty":        "folk",
    "psychedelic folk":  "folk",

    # jazz
    "jazz":              "jazz",
    "swing":             "jazz",
    "bebop":             "jazz",
    "gypsy jazz":        "jazz",
    "smooth jazz":       "jazz",
    "vocal jazz":        "jazz",
    "acid jazz":         "jazz",
    "jazz piano":        "jazz",
    "jazz fusion":       "jazz",
    "nu jazz":           "jazz",
    "latin jazz":        "jazz",
    "free jazz":         "jazz",
    "dixieland":         "jazz",
    "ragtime":           "jazz",
    "cabaret":           "jazz",
    "big band":          "jazz",
    "bossa nova":        "jazz",
    "chanson":           "jazz",
    "chanson francaise": "jazz",
    "gospel":            "soul",

    # new wave
    "new wave":          "new wave",
    "synthpop":          "new wave",
    "post-punk":         "new wave",
    "electropop":        "new wave",
    "synth-pop":         "new wave",
    "ebm":               "new wave",
    "minimal synth":     "new wave",
    "synthwave":         "new wave",
    "new romantic":      "new wave",

    # punk
    "punk":              "punk",
    "punk rock":         "punk",
    "proto-punk":        "punk",
    "hardcore punk":     "punk",
    "post-hardcore":     "punk",
    "melodic hardcore":  "punk",
    "hardcore":          "punk",
    "oi":                "punk",
    "glam punk":         "punk",
    "horror punk":       "punk",
    "celtic punk":       "punk",
    "ska punk":          "punk",
    "thrashcore":        "punk",
    "screamo":           "punk",
    "no wave":           "punk",

    # metal
    "metal":             "metal",
    "heavy metal":       "metal",
    "thrash metal":      "metal",
    "black metal":       "metal",
    "death metal":       "metal",
    "progressive metal": "metal",
    "power metal":       "metal",
    "symphonic metal":   "metal",
    "industrial metal":  "metal",
    "groove metal":      "metal",
    "folk metal":        "metal",
    "nu metal":          "metal",
    "sludge":            "metal",
    "grindcore":         "metal",
    "alternative metal": "metal",
    "post-metal":        "metal",

    # electronic
    "electronic":        "electronic",
    "techno":            "electronic",
    "house":             "electronic",
    "ambient":           "electronic",
    "trip-hop":          "electronic",
    "chillout":          "electronic",
    "chill":             "electronic",
    "trance":            "electronic",
    "dance":             "electronic",
    "electronic dance":  "electronic",
    "drum n bass":       "electronic",
    "dubstep":           "electronic",
    "grime":             "electronic",
    "ebm":               "electronic",
    "industrial":        "electronic",
    "lo-fi":             "electronic",
    "shoegaze":          "electronic",
    "noise rock":        "electronic",
    "psytrance":         "electronic",
    "eurodance":         "electronic",
    "eurobeat":          "electronic",
    "electro":           "electronic",
    "electro-swing":     "jazz",
    "reggaeton":         "electronic",
    "k-pop":             "pop",
    "j-pop":             "pop",

    # hip-hop
    "hip-hop":           "hip-hop",
    "hip hop":           "hip-hop",
    "rap":               "hip-hop",
    "christian rap":     "hip-hop",
    "nerdcore":          "hip-hop",
    "new zealand hip-hop": "hip-hop",
    "grime":             "hip-hop",

    # indie / alternative
    "indie":             "indie",
    "indie rock":        "indie",
    "indie pop":         "indie",
    "bedroom pop":       "indie",
    "twee":              "indie",
    "lo-fi":             "indie",
    "alternative":       "alternative",
    "alternative rock":  "alternative",
    "britpop":           "alternative",
    "grunge":            "alternative",
    "madchester":        "alternative",
    "shoegazing":        "alternative",
    "paisley underground": "alternative",
    "grunge":            "alternative",
    "dream pop":         "indie",

    # reggae
    "reggae":            "reggae",
    "ska":               "reggae",
    "dub":               "reggae",
    "rocksteady":        "reggae",
    "dancehall":         "reggae",
    "skinhead reggae":   "reggae",
    "early reggae":      "reggae",
    "mento":             "reggae",
    "calypso":           "world",

    # disco
    "disco":             "disco",
    "funk":              "funk",
    "funk rock":         "funk",
    "northern soul":     "soul",

    # world
    "world":             "world",
    "world music":       "world",
    "latin":             "world",
    "afrobeat":          "world",
    "african":           "world",
    "bossa nova":        "jazz",
    "samba":             "world",
    "salsa":             "world",
    "mambo":             "world",
    "tango":             "world",
    "polka":             "world",
    "qawwali":           "world",
    "mariachi":          "world",
    "chutney":           "world",
    "calypso":           "world",
    "ye-ye":             "world",
    "opera":             "classical",
    "exotica":           "world",

    # classical
    "classical":         "classical",
    "orchestral":        "classical",
    "baroque":           "classical",
    "early music":       "classical",
    "classical guitar":  "classical",

    # comedy
    "comedy":            "comedy",
    "comedian":          "comedy",
    "stand-up":          "comedy",
    "humor":             "comedy",
    "novelty":           "comedy",
    "parody":            "comedy",
    "satire":            "comedy",
    "outsider":          "comedy",

    # rockabilly
    "rockabilly":        "rockabilly",
    "psychobilly":       "rockabilly",
    "neo-rockabilly":    "rockabilly",
    "neo-swing":         "rockabilly",

    # soundtrack
    "soundtrack":        "soundtrack",
    "soundtracks":       "soundtrack",
    "musical":           "soundtrack",
    "broadway":          "soundtrack",
    "disney":            "soundtrack",
    "musical theater":   "soundtrack",
    "score":             "soundtrack",
    "film score":        "soundtrack",
}

# Tags to clear entirely — not mappable to any genre
CLEAR = {
    "good voice", "impossible for liberals to deal with", "the", "female",
    "guitar", "drums", "cello", "violin", "saxophone", "ukulele", "piano",
    "brass", "accordian", "home collection", "legen-wait for it-dary",
    "liszaj radio", "thegreatgigintheskyvoice", "funk_add_to_lidarr_batch_16",
    "need to rate", "want to see live", "music i might like", "do przesluchania",
    "my top songs", "guilty pleasures", "perfect", "theme time radio hour",
    "lesser known yet streamable artists", "spotify", "star trek", "fallout 3",
    "mamma mia the movie", "sweeney todd", "south park", "zodiac", "karneval",
    "wsum 91.7 fm madison", "radio caroline", "the voice", "fluxus",
    "fleetwood mac", "the beatles", "roger whittaker", "dr. hook",
    "barbara streisand", "jackson family", "taylor family singers",
    "jack jersey", "heintje", "australian-crawl", "susan boyle",
    "the forest rangers", "the vitamin b12", "slim and slam",
    "kate nash is a legend", "girly man", "rare sad boy", "pussycat",
    "scumbag politicians", "smash your child against a wall",
    "grooving mot rolling", "shambolic", "entschleunigen",
    "new zealandic", "kiwi", "gumboots", "wisconsin", "minneapolis",
    "san francisco", "manchester", "new orleans", "united states",
    "united kingdom", "england", "the netherlands", "spain", "france",
    "italy", "finland", "dutch", "danish", "dansk", "finnish",
    "greek", "serbian", "russian", "polish", "hungarian", "icelandic",
    "korean", "samoan", "spanish", "portuguese", "nordic", "irish",
    "spoken word", "poetry", "speech", "audiobook", "song-poem", "filk",
    "duets", "a cappella", "instrumental", "guitar virtuoso", "acoustic",
    "instrumental", "remix", "mashup", "crossover", "party",
    "christian", "christian rock",
    "children", "kid music", "kids",
    "christmas", "spa music", "new age", "ambient",
    "music", "music video", "independent", "merge", "ilg", "ruk",
    "niche", "queer", "hipster", "opm", "motown",
    "experimental", "avant-garde", "avantgarde pop", "noise rock",
    "free jazz", "no wave",
}


def normalize(genre: str) -> str | None:
    if not genre:
        return None
    g = genre.lower().strip()
    # Already canonical
    if g in CANONICAL:
        return g
    # Explicit clear
    if g in CLEAR:
        return None
    # Explicit mapping
    if g in MAPPING:
        return MAPPING[g]
    # Keyword fallbacks
    if "hip hop" in g or "hip-hop" in g or " rap" in g:
        return "hip-hop"
    if "metal" in g:
        return "metal"
    if "punk" in g:
        return "punk"
    if "jazz" in g:
        return "jazz"
    if "blues" in g:
        return "blues"
    if "folk" in g:
        return "folk"
    if "country" in g:
        return "country"
    if "classical" in g or "orchestr" in g:
        return "classical"
    if "reggae" in g or "ska" in g:
        return "reggae"
    if "soul" in g:
        return "soul"
    if "funk" in g:
        return "funk"
    if "disco" in g:
        return "disco"
    if "electronic" in g or "techno" in g or "synth" in g or "electro" in g:
        return "electronic"
    if "rock" in g:
        return "rock"
    if "pop" in g:
        return "pop"
    if "comedy" in g or "humor" in g or "humour" in g:
        return "comedy"
    if "world" in g or "latin" in g:
        return "world"
    if "soundtrack" in g or "musical" in g or "broadway" in g:
        return "soundtrack"
    # Unmappable — clear it
    return None


def main():
    for fname in ["songs_enriched.json", "explorer/public/songs.json"]:
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            print(f"Skipping {fname} (not found)")
            continue

        songs = json.load(open(path))
        changed = cleared = 0
        for s in songs:
            old = s.get("genre")
            new = normalize(old)
            if new != old:
                s["genre"] = new
                if new is None:
                    cleared += 1
                else:
                    changed += 1

        with open(path, "w") as f:
            json.dump(songs, f, separators=(",", ":"))

        from collections import Counter
        genres = Counter(s["genre"] for s in songs if s.get("genre"))
        print(f"\n{fname}")
        print(f"  Remapped: {changed}  Cleared: {cleared}  Total with genre: {sum(genres.values())}")
        print(f"  Canonical genres used ({len(genres)}):")
        for g, c in sorted(genres.items(), key=lambda x: -x[1]):
            print(f"    {c:5d}  {g}")


if __name__ == "__main__":
    main()
