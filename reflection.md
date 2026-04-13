# Reflection: Profile Comparisons and What They Reveal

## High-Energy Pop vs. Chill Lofi

These two profiles are the clearest opposites in the catalog. The High-Energy Pop user wants pop, happy, energy 0.85. The Chill Lofi user wants lofi, focused, energy 0.40. Their top results — Sunrise City and Focus Flow — are completely different songs, and that is exactly right.

What makes this comparison interesting is *why* they differ so cleanly. It is not just one feature pointing in different directions — it is three: genre, mood, and energy all push opposite directions at the same time. Sunrise City has energy 0.82, which is almost perfectly matched to 0.85. Focus Flow has energy 0.40, which is an exact match for the lofi user. If you ran only the energy check with no genre or mood, you would still get the right answer for both. That is a sign of a well-designed profile — the preferences are redundant in the right way.

The lofi user also cares about instrumentalness (target 0.88). Focus Flow has instrumentalness 0.89 — nearly a perfect match. For a study session profile, that matters a lot because instrumental music does not compete with thinking. The pop user sets instrumentalness to 0.00, which is the opposite: they want vocals. This single field alone would separate the two songs even if every other preference were the same.

---

## High-Energy Pop vs. Deep Intense Rock

These two profiles look similar on the surface — both want high energy (0.85 and 0.91) and neither wants acoustic sound. But their top results are completely different: Sunrise City for pop, Storm Runner for rock.

The difference comes from genre and mood. Sunrise City is pop, happy. Storm Runner is rock, intense. When the pop user scores Storm Runner, it earns energy proximity points — Storm Runner has energy 0.91, close enough to the target of 0.85 — but it earns zero genre points (rock != pop) and zero mood points (intense != happy). That is 3.0 points left on the table. Sunrise City, which matches genre AND mood, wins by a wide margin.

This comparison shows that the categorical checks (genre and mood) do most of the heavy lifting in the algorithm. Energy proximity can push a song up or down within its tier, but it cannot rescue a song that fails the genre and mood filters. A rock song will almost never top a pop user's list, no matter how perfectly its energy matches.

---

## Why Gym Hero Keeps Showing Up for Happy Pop Listeners

This is the most important thing I learned during testing.

The High-Energy Pop profile wants pop, happy, energy 0.85. The top result is Sunrise City (pop, happy, energy 0.82) — that is correct. But the #2 result is consistently Gym Hero (pop, intense, energy 0.93), not Rooftop Lights (indie pop, happy, energy 0.76).

Gym Hero's mood is "intense." The user wants "happy." Those are different moods. So why does Gym Hero keep appearing ahead of a song that actually matches the user's mood?

The answer is that the system only rewards matches — it never punishes mismatches. When Gym Hero is scored against the happy pop user:
- Genre match (pop == pop): +1.0 points
- Mood match: **zero points** — intense does not equal happy, so it gets nothing
- Energy proximity: energy 0.93 vs. target 0.85 — difference of 0.08, so ratio = 0.92, points = 3.0 × 0.92 = **+2.76 points**

When Rooftop Lights is scored:
- Genre match (indie pop != pop): **zero points**
- Mood match (happy == happy): +2.0 points
- Energy proximity: energy 0.76 vs. target 0.85 — difference of 0.09, so ratio = 0.91, points = 3.0 × 0.91 = **+2.73 points**

Gym Hero earns 1.0 (genre) + 2.76 (energy) = 3.76 on just those two features. Rooftop Lights earns 2.0 (mood) + 2.73 (energy) = 4.73. With the final weights (genre=1.0), Rooftop Lights actually wins — and that is the correct result.

But with the original genre weight of 3.0, Gym Hero would earn 3.0 (genre) + energy proximity, which overwhelms the mood match from Rooftop Lights. That is the fix I made: reducing genre weight from 3.0 to 1.0 so that mood and energy together can outweigh a genre match with the wrong mood.

The broader lesson: a system that only gives points for matches, never penalties for mismatches, will always favor songs that score well on heavily weighted features — even if those songs are wrong for the user in another way the system cannot express.

---

## Standard Profiles vs. Adversarial Profiles

The three standard profiles (pop, lofi, rock) all returned results that matched musical intuition. The top song in each case was the obvious correct answer: Sunrise City, Focus Flow, Storm Runner. These profiles worked because the catalog has at least one song that matches well on every dimension — genre, mood, and energy all point to the same song.

The adversarial profiles were designed to break that. Here is what happened:

**Conflicting Energy + Sad Mood (blues, sad, energy 0.90):** No song in the catalog is both sad and high-energy. The only sad song is 3 AM Diner (blues, sad, energy 0.44). The system returned it as #1, but its score was only 6.79 — noticeably lower than the standard profiles. 3 AM Diner earned the genre and mood points but lost badly on energy (target 0.90, actual 0.44 — a gap of 0.46 on a weight of 3.0, which costs about 1.38 points). The system cannot satisfy both preferences at once and does not tell the user that. It just quietly returns the best compromise.

**Ghost Genre (metal):** Metal does not exist in the catalog. Every song scores zero genre points. The system fell back on mood (intense) and energy (0.95) and returned Storm Runner (rock, intense) as #1. Storm Runner is a reasonable backup, but the user asked for metal. The system never warned them that their primary preference was completely ignored.

**Impossible Combo (EDM + fully instrumental):** The user wanted electronic music (acousticness 0.02) that has no vocals (instrumentalness 1.0). In practice, electronic songs in the catalog tend to have vocals, and instrumental songs tend to be acoustic (lofi, classical). Drop Zone (EDM, euphoric) was the top result with a score of 8.71, but it only has instrumentalness 0.72 — not 1.0. The system returned the closest available song without flagging that the combination does not exist.

**Middle of Everything (all preferences at 0.5, no genre):** This is the most revealing edge case. When every preference is set to the midpoint, no song is significantly better or worse than any other. The top 5 results spanned a range of only 0.14 points (5.16 to 5.02). The system returns Gravel Road Home as #1 for no musically meaningful reason — it just happened to be slightly closer to 0.5 on more features. This shows the system has nothing useful to say when the user has not told it enough about their taste.

---

## What This Taught Me About Real Recommenders

The most surprising insight was how much the catalog size matters. With 18 songs, giving genre a heavy weight creates a situation where one or two songs dominate every profile. Reducing the genre weight did not make the system worse — it actually made recommendations more accurate, because it gave mood and energy room to breathe.

Real apps like Spotify likely use a high genre weight too, but they have thousands of songs per genre to choose from. The genre filter does not produce one result — it narrows down to hundreds, and then mood, energy, and other features make the real distinctions. With 18 songs, genre filtering produces one or two results, and the rest of the recommendations are filler.

The ghost genre problem — where the system silently ignores an unmet preference — is probably the most dangerous bias in a real product. A user who asks for metal and gets rock might not realize their preference was never honored. They might assume the system understood them and adjust their self-perception accordingly. That is a real form of feedback loop bias: the user learns to ask for rock because the system keeps giving them rock, even though what they actually wanted was metal.

---

## Challenge 1: What Adding Advanced Features Revealed

Adding five new features — popularity, release_decade, detail_mood, liveness, and loudness — changed what the system could express, but also exposed something unexpected: more features do not automatically make recommendations better.

The decade scoring rule was the most interesting. With the Y2K Jazz profile (preferred_decade=2000), Coffee Shop Stories (jazz, 2000) earned full decade points (+1.0) and a detail_mood match (+1.5 for "nostalgic"), pushing its total score to 12.28 out of 13.0. That felt right — the profile was asking for exactly that song. But the second result (Gravel Road Home, country) made it to #2 purely because it shares the 2000s era and a "nostalgic" detail_mood. The system found a pattern that was real in the data but musically wrong for the user.

The popularity feature had a subtler effect. Setting `target_popularity=30` (underground preference) penalized Gym Hero (popularity=81) by 0.26 points. That is a small penalty relative to the energy and genre weights — small enough that a mainstream song can still dominate if its genre and energy are right. The feature shifts the ranking slightly but does not override the core scoring. That is probably the right balance.

The lesson from Challenge 1: adding features helps when the user specifies them. When the user does not specify them (the features are `None`), they contribute nothing — which means the advanced features are invisible to existing profiles. That is a good design choice for backward compatibility, but it means the catalog's new richness is only accessible to users who know to ask for it.

---

## Challenge 2: What Scoring Modes Revealed

The Strategy pattern — four interchangeable scoring modes, each a weight-override dict merged at score time — was the cleanest piece of engineering in the project.

Running the High-Energy Pop profile under all four modes made the trade-offs visible in a way that was impossible to see from a single run:

- `genre_first` immediately pushed Gym Hero back to #2 (genre dominates over mood)
- `mood_first` surfaced all three "happy" mood songs in the top 3, regardless of genre
- `energy_focused` ranked by intensity alone — Gym Hero (0.93) and Storm Runner (0.91) both climbed because their energy was nearest to 0.85, even though their moods were wrong
- `discovery` (genre=0) surfaced reggae and ambient songs that would never appear under genre filtering

The most important thing the mode comparison revealed is that there is no universally correct weighting. The "right" recommendation depends entirely on what the user values most. A user who says "I want pop" and means it strictly is best served by `genre_first`. A user who says "I want something euphoric" without caring about genre is best served by `mood_first`. The same preference dictionary produces completely different results under different modes — which is a feature, not a bug.

---

## Challenge 3: What Diversity Enforcement Revealed

The LoRoom problem was the clearest failure mode in the original system. Without any diversity check, the Chill Lofi profile returned Focus Flow, Midnight Coding, and Library Rain — all three were LoRoom songs. The system was technically correct (all three are high-scoring lofi tracks) but musically wrong (no one wants their study playlist to be one artist on repeat).

The greedy re-ranking fix worked well. With `artist_penalty=0.5`, the second LoRoom song's effective score dropped from 6.84 to 3.42 — below Coffee Shop Stories (5.62) and Spacewalk Thoughts (5.38). The top 5 with diversity ON spans jazz, ambient, lofi (Paper Lanterns, not LoRoom), and classical. That is a genuinely more useful list.

But the fix also revealed something subtle: the diversity penalty does not know anything about music. It is just arithmetic on artist names and genre strings. It breaks up the LoRoom monopoly, but it could also break up a legitimate cluster. If a user asks for blues and the catalog had five great blues songs by the same artist, the diversity penalty would push the second through fifth songs down — even if they were exactly what the user wanted. The penalty treats repetition as always bad, which is not always true.

The lesson: diversity enforcement improves the average case but can hurt the specific case. The right value for `artist_penalty` depends on the catalog size and the user's intent — and right now, both are fixed rather than learned.

---

## Challenge 4: What the Visual Table Revealed

Building the tabulate grid summary was the simplest of the four challenges technically, but it revealed something important about how output format affects understanding.

The plain `print_recommendations` output was already readable — it showed each song with a score bar and a bullet list of reasons. But the table format made something visible that the plain output obscured: **score gaps**. When you see five songs stacked in a grid with their score bars side by side, it is immediately obvious when #1 has a score of 8.86 and #2 has a score of 5.62. In the plain output, those scores are separated by several lines of reasons — the gap is harder to feel.

The reasons column in the table also made the diversity penalty transparent in a new way. Seeing `* diversity penalty applied (raw=6.72)` as the last reason line in the same cell as the scoring reasons — right next to the score bar — made it clear that the effective score and the raw score are different things. In the plain output, that information was there but required reading carefully. In the table, it was impossible to miss.

The table format also exposed which songs had many reasons vs. few. A song that earned points on genre, mood, energy, acousticness, instrumentalness, valence, speechiness, decade, and detail_mood fills six lines in the reasons column. A song that only earned energy proximity points fills one line. That visual asymmetry immediately communicates how well the song actually matched vs. how much it just happened to score.
