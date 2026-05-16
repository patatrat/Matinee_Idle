# Twenty-One Years of Weird, Wonderful Music — and What the Data Says

## A love letter to Matinee Idle, a cult radio show, and the rabbit hole it sent me down

Around eighteen and a half years ago, I started a new job as a business analyst. I started in mid-December and was thrown straight into a full-on project. Because I had no annual leave and plenty of work to get on with, I was back at my desk after the Christmas/New Year break very quickly.

Those first weeks of early January can be a lonely business in an office. This was before we all had Spotify on our phones or could stream music on work devices — so I brought in a little radio and tuned into RNZ National.

What I found, on those quiet summer afternoons, was something magical.

A radio show where two guys — Phil O'Brien and Simon Morris — just played whatever they wanted. And I mean *whatever*. They played the most amazing and sometimes the most objectively ridiculous songs. They had themes, and played songs with sometimes the most tenuous connection to whatever their theme was. They laughed. They joked. They made fun of songs and each other. They had a genuine and deep respect for the idea that sometimes the best songs are the strange, unusual ones — the ones that fell through the cracks, or that most of the world has forgotten. They egged each other on and tried to one-up each other with what they could find and play.

I was hooked. And I wasn't alone — this "fill-in" radio show gathered something of a national cult following. I would look forward to the summer break and long weekends, and tune in for the afternoon.

And then this year, after 21 years of glorious madness, they wrapped up.

What they left behind was a gap in my holidays, a gap on the airwaves and, after a bit of digging, **[INSERT: X archive pages]** on the RNZ website listing every single song they played across two decades.

I was intrigued. I wanted to go back and relisten to some of those gems. I wanted to know what the most popular song they ever played was, or their most-featured artist, or their favourite genre or decade. I wanted to relive some of the cover versions they would often end each show with.

So, in the spirit of my other *high effort, low value* projects, I decided to do something about it.

---

## Step One: Getting the Data

First, I scraped the RNZ archive and pulled out all the songs. And then I tried to make sense of what I had.

With 18 years of shows in the archive, the data was all over the place. Band names had misspellings and inconsistencies — because when a human being types tens of thousands of entries over two decades, things drift. I found 140 distinct inconsistencies in artist names alone. Dr Hook vs Dr. Hook. Devo vs DEVO. Half Man Half Biscuit vs Half Man, Half Biscuit. The Shangri-Las vs The Shangri-las. And my personal favourite: Billy Bragg appearing as "BIlly Bragg" — capital I where it shouldn't be — which must have been an autocorrect that snuck through and persisted for years.

Beyond the naming chaos, the data was sparse. There was no information about when songs were released, what genre they were, how popular the artist was, or really anything beyond the artist name, the song title, and the date it aired.

I spent months trying to fill in those gaps. I used the Spotify API, Last.fm, MusicBrainz, and Discogs to enrich the dataset with release years, genres, and popularity metrics. I hit a wall. After a massive amount of effort, I could only get about 75% of the songs sorted. The remaining quarter — roughly 3,700 songs — simply couldn't be matched to anything in any database.

I hit a wall and just... left it.

---

## Step Two: Coming Back to It

But, in the last few months, I decided to pick it back up. With better tools, more patience, and a lot of help from Claude, I pushed through the enrichment pipeline, normalised the genre tags, and finally had something I could actually analyse.

The result: **15,411 songs**, **6,122 unique artists**, and 18 years of one of the best radio programmes New Zealand ever produced, captured in a database.

Here's what the numbers say.

---

## The Most-Played Song: Cousin Mosquito

Here's where the data delivers its first twist — and also a perfect illustration of the data quality problems I dealt with.

The most-played song across the entire archive is *Cousin Mosquito* by Congresswoman Malinda Jackson Parker. Played **16 times** in total.

But here's the thing: I almost missed it. The song appears in the dataset under four different artist name spellings:

- `Congresswoman Malinda Jackson Parker`
- `Congress-Woman Malinda Jackson Parker`
- `Congresswoman Malinda Jackson-Parker`
- `Congresswoman Melinda Jackson Parker` *(Melinda, not Malinda)*

And split across two titles: *Cousin Mosquito* and *Cousin Mosquito #1*.

A naive count treats each variant as a separate artist. Grouped correctly: 16 plays. The most loved song in the entire archive, and it was hiding in plain sight behind four slightly different spellings of the same name.

In second place: *Snake Farm* by Ray Wylie Hubbard with a clean 12 plays. In third: *This Pullover* by Jess Conrad with 11. If you don't know either of those songs, go find them immediately. I'll wait.

---

## The Artists: A Hall of Fame and a Hall of One-Timers

The most-featured artists across the full archive:

| Rank | Artist | Plays |
|------|--------|-------|
| 1 | The Beach Boys | 84 |
| 2 | The Beatles | 78 |
| 3 | Sparks | 69 |
| 4 | The Kinks | 68 |
| 4 | The Rolling Stones | 68 |
| 4 | Harry Nilsson | 68 |
| 7 | The Divine Comedy | 65 |
| 8 | Half Man Half Biscuit | 64 |
| 9 | The Move | 57 |
| 10 | Devo | 56 |

The Beach Boys edging out The Beatles by six plays feels about right for this show. But Sparks at number three — ahead of the Stones — is quintessential Matinee Idle. And the presence of Half Man Half Biscuit and The Move in the top ten tells you everything about the show's sensibility.

What's equally striking is what's *underneath* that top ten. Of the 6,122 unique artists in the dataset, **4,083 of them — 66% — appeared exactly once**. One song. One slot. One chance to be heard. The whole ethos of the show in a single statistic.

---

## The Time Machine

The show was famous for playing *old* stuff. Not just "this 90s classic" old — genuinely old. The data bears this out.

The oldest song in the dataset was recorded in **1937**: *Onyx Hop* by Frankie Newton and His Uptown Serenaders, aired 82 years after it was recorded.

Close behind: the Light Crust Doughboys' 1938 recording of a song called *Pussy, Pussy, Pussy*, which aired in 2022 — an 84-year gap between recording and broadcast. I cannot tell you whether Phil or Simon played that one, but I would bet money on there being a story attached.

The release decade breakdown tells its own story:

| Decade | Share of songs |
|--------|---------------|
| 2000s | 30.4% |
| 1990s | 23.7% |
| 2010s | 22.2% |
| 1980s | 8.0% |
| 2020s | 7.0% |
| Pre-1950 | 0.4% |

The 2000s dominating makes sense — it was when the show launched and the hosts were in their prime music-collecting years. But the 1990s and 2010s holding their own suggests the show kept refreshing, not just recycling.

---

## The Genres: More Rock, More Soul, More Weird

When we could pin down a genre (about 75% of the dataset), the landscape looked like this:

**Rock** (2,314), **Pop** (1,668), **Classic Rock** (1,637), **Soul** (1,131), **Folk** (1,008), **Country** (976), **Jazz** (879), **New Wave** (812)...

And then, further down the list: **Comedy** (650 songs). That's not a side note — 650 songs where the joke is at least partly the point. That's a cornerstone of what the show was.

Alongside that: Rockabilly (367), Electronic (308), and a scattering of genres that don't really have a name because only a handful of people in the world would claim to be fans.

---

## The 24% We Couldn't Match

Here's where the data gets honest.

Almost a quarter of all songs in the archive — 3,740 of them — couldn't be fully matched to any music database. No complete Spotify record. No clean MusicBrainz entry. They exist in the RNZ archive, in my dataset, and that's mostly it.

Some of these are collaboration entries that databases don't handle well. Some are cover versions by artists so obscure that even Discogs doesn't know they exist. Some are one-off novelty recordings or live rarities.

And then there are the cases that tell you exactly what kind of show this was.

*Father Ted ft. Father Dougal — My Lovely Horse*. A song performed by fictional characters from a sitcom. Databases don't quite know what to do with it.

*William Shatner & Joe Jackson — Common People*. This is real. It exists. William Shatner did a spoken word cover of the Pulp classic with Joe Jackson playing alongside him. It is exactly as strange as it sounds, and of course Matinee Idle played it.

*Coby Smulders & Nicole Scherzinger — Two Beavers Are Better Than One*. From a Canadian children's show. No database has it. Of course it was played.

And then, buried in the list: **Simon Morris — Walking in Guildford**. And *Simon Morris — Boom Boom*. And *Simon Morris — The Hobbit*. And several more.

Simon Morris, one of the two hosts, apparently played his own songs on his own show. Multiple times. These recordings are essentially invisible to any music database because he is not a catalogued recording artist in any formal sense. He just played his own stuff. On radio. That he co-hosted. I find this completely delightful.

Those 3,740 unmatched songs might be the most Matinee Idle data point of all. If you could easily find a song in a database, it was probably too easy for Phil and Simon to have bothered with.

---

## What's Next

The data is clean, the database is running, and I've built an explorer so you can dig through all of it yourself. Search by artist, year, genre, or decade — or filter specifically by "unmatched" to browse the songs that defeated every automated tool I threw at them.

If you were a Matinee Idle listener, I hope this brings back some memories. If you weren't — well, now you have 15,411 songs to work through. Start with Cousin Mosquito.

---

*The Matinee Idle archive explorer is at radomski.co.nz. More soon.*

---

> **Note before publishing:** Fill in the RNZ archive page count — the scraper pulled from a database backup so the raw page count isn't stored in the code. Check the RNZ archive directly and drop the number into the first section.
