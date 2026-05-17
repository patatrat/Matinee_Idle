# Twenty-One Years of Weird, Wonderful Music — and What the Data Says

## A love letter to Matinee Idle, a cult radio show, and the rabbit hole it sent me down

Around eighteen and a half years ago, I started a new job as a business analyst. I started in mid-December and was thrown straight into a full-on project. Because I had no annual leave and plenty of work to get on with, I was back at my desk after the Christmas/New Year break very quickly.

Those first weeks of early January can be a lonely business in an office. This was before we all had Spotify on our phones or could stream music on work devices — so I brought in a little radio and tuned into RNZ National.

What I found, on those quiet summer afternoons, was something magical.

A radio show where two guys — Phil O'Brien and Simon Morris — just played whatever they wanted. And I mean *whatever*. They played the most amazing and sometimes the most objectively ridiculous songs. They had themes, and played songs with sometimes the most tenuous connection to whatever their theme was. They laughed. They joked. They made fun of songs and each other. They had a genuine and deep respect for the idea that sometimes the best songs are the strange, unusual ones — the ones that fell through the cracks, or that most of the world has forgotten. They egged each other on and tried to one-up each other with what they could find and play.

I was hooked. And I wasn't alone — this "fill-in" radio show gathered something of a national cult following. I would look forward to the summer break and long weekends, and tune in for the afternoon.

And then this year, after 21 years of glorious madness, they wrapped up.

What they left behind was a gap in my holidays, a gap on the airwaves and, after a bit of digging, a complete archive on the RNZ website listing every single song they played across two decades.

I was intrigued. I wanted to go back and relisten to some of those gems. I wanted to know what the most popular song they ever played was, or their most-featured artist, or their favourite genre or decade. I wanted to relive some of the cover versions they would often end each show with.

So, in the spirit of my other *high effort, low value* projects, I decided to do something about it.

---

## Step One: Getting the Data

First, I scraped the RNZ archive and pulled out all the songs. And then I tried to make sense of what I had.

With 21 years of shows in the archive, the data was all over the place. Band names had misspellings and inconsistencies — because when a human being types tens of thousands of entries over two decades, things drift. I found 140 distinct inconsistencies in artist names alone. Dr Hook vs Dr. Hook. Devo vs DEVO. Half Man Half Biscuit vs Half Man, Half Biscuit. The Shangri-Las vs The Shangri-las. And my personal favourite: Billy Bragg appearing as "BIlly Bragg" — capital I where it shouldn't be — which must have been an autocorrect that snuck through and persisted for years.

Beyond the naming chaos, the data was sparse. There was no information about when songs were released, what genre they were, how popular the artist was, or really anything beyond the artist name, the song title, and the date it aired.

I spent months trying to fill in those gaps. I used the Spotify API, Last.fm, MusicBrainz, and Discogs to enrich the dataset with release years, genres, and popularity metrics. I made real progress — but a long tail of songs simply couldn't be matched to anything in any database. The remaining gaps I eventually closed using an AI classification pass, working through each unresolved song by artist name and title alone and assigning it to the nearest genre from a canonical list.

The result: **15,411 songs**, **5,722 unique artists**, and 21 years of one of the best radio programmes New Zealand ever produced, captured in a single dataset.

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

In second place: *Snake Farm* by Ray Wylie Hubbard with a clean 12 plays. Third is a tie — *My World* by Cupid's Inspiration and *This Pullover* by Jess Conrad, both with 11. If you don't know any of those songs, go find them immediately. I'll wait.

---

## The Artists: A Hall of Fame and a Hall of One-Timers

The most-featured artists across the full archive:

| Rank | Artist | Plays |
|------|--------|-------|
| 1 | The Beach Boys | 85 |
| 2 | The Beatles | 79 |
| 3= | Harry Nilsson | 69 |
| 3= | Sparks | 69 |
| 5 | The Kinks | 68 |
| 6 | The Rolling Stones | 67 |
| 7 | Half Man Half Biscuit | 65 |
| 8 | The Divine Comedy | 64 |
| 9 | Devo | 57 |
| 10 | Burton Cummings | 55 |

The Beach Boys edging out The Beatles by six plays feels about right for this show. But Sparks and Harry Nilsson tied at third — ahead of the Stones — is quintessential Matinee Idle. And the presence of Half Man Half Biscuit and Burton Cummings in the top ten tells you everything about the show's sensibility.

What's equally striking is what's *underneath* that top ten. Of the 5,722 unique artists in the dataset, **3,620 of them — 63% — appeared exactly once**. One song. One slot. One chance to be heard. The whole ethos of the show in a single statistic.

---

## The Time Machine

The show was famous for playing *old* stuff. Not just "this 90s classic" old — genuinely old. The data bears this out.

The oldest song in the dataset is from **1930**: *Puttin' on the Ritz* by Fred Astaire, which aired 91 years after it was recorded. Close behind: Leola Manning's *Satan's Is Busy in Knoxville* (also 1930) and a 1931 recording of *Dream a Little Dream of Me* by Ozzie Nelson — the original, decades before Mama Cass made it famous.

The decade breakdown tells its own story:

| Decade | Share of songs |
|--------|---------------|
| 1970s | 15.5% |
| 2000s | 14.5% |
| 1960s | 14.4% |
| 1990s | 12.0% |
| 1980s | 11.9% |
| 2010s | 9.9% |
| 1950s | 2.9% |
| 2020s | 1.7% |
| Pre-1950 | 0.6% |

What strikes me most is how flat this distribution is. The 1960s, 1970s, and 2000s are all within a percentage point of each other. This wasn't a show that got stuck in one era — it ranged across the full century of recorded music with roughly equal enthusiasm for all of it. The 1950s and pre-war recordings are the tail, but even there, 444 songs from the 1950s is not a footnote.

---

## The Genres

With 100% genre coverage across all 15,411 songs — achieved through a combination of Spotify, Last.fm, MusicBrainz, Discogs, and a final AI classification pass for the songs that defeated every database — the full picture looks like this:

**Rock** (2,227), **Pop** (1,680), **Classic Rock** (1,650), **Soul** (1,106), **Folk** (1,004), **Country** (998), **Jazz** (890), **New Wave** (786)...

And then, further down the list: **Comedy** (734 songs). That's not a side note — 734 songs where the joke is at least partly the point. That's a cornerstone of what the show was.

Alongside that: Blues (588), Indie (623), Progressive Rock (519), Rockabilly (378). And at the bottom end, 55 songs classified as Classical — which feels low until you remember this was a pop music show, and even getting to 55 means someone was deliberately reaching.

The genre that probably surprises people most is Comedy at nearly 5% of the entire archive. That's not novelty songs sneaking in — that's a deliberate editorial commitment to songs that make you laugh. It's one of the things that made the show impossible to replicate.

---

## The Songs Databases Don't Know

Here's where the data gets interesting in a different way.

Some of these songs exist in the RNZ archive and more or less nowhere else. No Spotify record. No clean MusicBrainz entry. No Discogs listing. They were played on a summer afternoon radio show in New Zealand, and that's the full extent of their documented existence.

Some of these are collaboration entries that databases don't handle well. Some are cover versions by artists so obscure that even specialist databases don't know they exist. Some are one-off novelty recordings or live rarities.

And then there are the cases that tell you exactly what kind of show this was.

*Father Ted ft. Father Dougal — My Lovely Horse*. A song performed by fictional characters from a sitcom. Databases don't quite know what to do with it.

*William Shatner & Joe Jackson — Common People*. This is real. It exists. William Shatner did a spoken word cover of the Pulp classic with Joe Jackson playing alongside him. It is exactly as strange as it sounds, and of course Matinee Idle played it.

*Coby Smulders & Nicole Scherzinger — Two Beavers Are Better Than One*. From a Canadian children's show. No database has it. Of course it was played.

And then, buried in the list: **Simon Morris — Walking in Guildford**. And *Simon Morris — Boom Boom*. And *Simon Morris — The Hobbit*. And several more.

Simon Morris, one of the two hosts, apparently played his own songs on his own show. Multiple times. These recordings are essentially invisible to any music database because he is not a catalogued recording artist in any formal sense. He just played his own stuff. On radio. That he co-hosted. I find this completely delightful.

These are, in a sense, the most Matinee Idle songs in the entire archive. If you could easily find a song in a database, it was probably too easy for Phil and Simon to have bothered with.

---

## What's Next

The data is clean, the genre is assigned for every single song, and I've built an explorer so you can dig through all of it yourself. Search by artist, year, genre, or decade — or just hit the random button and see what comes up.

If you were a Matinee Idle listener, I hope this brings back some memories. If you weren't — well, now you have 15,411 songs to work through. Start with Cousin Mosquito.

---

*The Matinee Idle archive explorer is at radomski.co.nz. More soon.*
