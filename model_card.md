# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder 1.0 suggests songs from an 18-song catalog based on a user's stated genre, mood, and audio feature preferences. It is designed for classroom exploration of how content-based recommender systems work — not for real users or production use. The system assumes the user can explicitly state their preferences (genre, mood, target energy level) rather than learning them from listening history. It makes no personalization over time and has no memory between sessions.

---

## 3. How the Model Works

Every song in the catalog is given a score by comparing it against the user's preferences. The score is built from two types of checks. First, categorical checks: if a song's genre matches what the user wants, it earns points; same for mood. Second, proximity checks: for features like energy, acousticness, and instrumentalness, the system measures how close the song's value is to the user's target — the closer, the more points earned. A song with energy 0.82 scores nearly full points for a user who wants energy 0.85, but scores much less for a user who wants energy 0.40. Once every song has a score, they are sorted from highest to lowest and the top results are returned. Each result also includes a plain-language explanation of which features contributed to its score and how many points each one earned.

---

## 4. Data

The catalog contains 18 songs across 12 genres: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, R&B, classical, country, EDM, folk, reggae, and blues. Moods represented include happy, chill, intense, relaxed, focused, moody, motivated, romantic, melancholic, nostalgic, euphoric, dreamy, and sad. The original starter file had 10 songs; 8 were added to fill genre and mood gaps. Each song has 10 audio features: genre, mood, energy, tempo, valence, danceability, acousticness, speechiness, and instrumentalness. The catalog reflects mostly Western, English-language music conventions. Genres like K-pop, Latin, Afrobeats, and classical Indian music are entirely absent. Most songs were invented for this simulation and do not reflect real listening data or real user behavior.

---

## 5. Strengths

The system works well for users with clear, specific preferences — particularly when their target genre exists in the catalog and their energy target is close to at least one song. The study session profile (lofi, focused, energy 0.40) consistently returns Focus Flow at 9.48/9.50, which matches the musical intuition perfectly. The explanation feature is a genuine strength: every recommendation shows the exact points each feature contributed, making the system fully transparent and easy to debug. This transparency also helps expose when the system is getting the right answer for the wrong reasons.

---

## 6. Limitations and Bias

**Filter bubble from small catalog size.** The most significant weakness discovered during experiments is that the catalog is too small for genre-based filtering to be meaningful. With only one rock song in 18 songs, a user who prefers rock receives Storm Runner as their #1 result — and then falls off a cliff, with songs from completely unrelated genres filling positions #2 through #5. The system creates a false sense of confidence: it returns 5 results with clean score bars, but positions #3 through #5 are essentially random noise. In a real recommender, this would be called a filter bubble — the user never discovers music outside their stated genre because the catalog cannot support genuine variety.

**Energy gap bias against extreme preferences.** The energy proximity formula treats a gap of 0.5 as simply half points, but in practice this means users with very low energy targets (e.g., 0.10 for meditation music) are penalized far more harshly than users near the middle of the scale. A user who wants energy 0.10 loses 0.72 points on a song with energy 0.82, while a user who wants energy 0.50 loses only 0.32 points on the same song. This asymmetry means calm-preference users consistently get worse results from the same catalog.

**Ghost genre problem — silent failure.** When a user specifies a genre that does not exist in the catalog (such as "metal"), the system returns zero genre-match points for every song and quietly falls back to mood and energy. The user receives confident-looking recommendations — Storm Runner, Gym Hero — with no warning that their primary preference was completely unmet. A real system would surface a "no results for your genre" message rather than pretending to help.

**Mood label subjectivity.** Mood labels like "chill," "intense," and "moody" were assigned manually and reflect a single perspective. Two people might disagree on whether Night Drive Loop is "moody" or "focused." The system treats these labels as objective facts and matches them exactly, meaning a user who thinks of the same song as "relaxing" gets zero mood points even though their intent was correct.

**No diversity enforcement.** The ranking rule returns the top-k highest-scoring songs with no check for variety. For the Chill Lofi profile, all three top results are lofi songs by the same artist (LoRoom). A real recommender would enforce diversity — at most one song per artist, or a mix of genres that still fit the mood — to avoid repetitive recommendations.

---

## 7. Evaluation

Seven user profiles were tested: three standard (High-Energy Pop, Chill Lofi, Deep Intense Rock) and four adversarial (conflicting energy+mood, ghost genre, impossible feature combo, all-neutral preferences). For each profile the top 5 results were inspected manually and compared against musical intuition. Two weight experiments were also run: first reducing genre weight from 3.0 to 2.0, then halving it to 1.0 while doubling energy weight to 3.0. The most surprising finding was that reducing genre weight made the High-Energy Pop results more musically accurate — Rooftop Lights (indie pop, happy) correctly rose above Gym Hero (pop, intense) when mood and energy were allowed to compete with genre on more equal terms. The adversarial profiles confirmed that the system fails silently: it always returns 5 results even when the user's preferences are contradictory or entirely absent from the catalog.

---

## 8. Future Work

The highest-priority improvement would be catalog expansion — at least 10 songs per genre so that genre filtering produces meaningful variety rather than a single correct answer followed by noise. A close second would be adding a diversity enforcement step to the ranking rule, so that no artist appears more than once in the top 5. For the ghost genre problem, a simple pre-check before scoring could detect when the user's genre has zero matches and either warn the user or broaden the search automatically. Longer term, replacing the static `target_energy` with a range (`min_energy`, `max_energy`) would let users express preferences like "between 0.6 and 0.9" rather than a single point, which would reduce the energy gap bias against extreme preferences.

---

## 9. Personal Reflection

Building this recommender made clear how much hidden work the genre label is doing. Before running the weight experiments, it felt natural to give genre a heavy weight — after all, a jazz fan does not want rock recommendations. But with only 18 songs, that heavy weight creates a situation where one or two songs dominate every profile and the rest of the results are filler. The most interesting moment was watching the High-Energy Pop results change when genre weight dropped from 3.0 to 1.0: Rooftop Lights jumped to #2 purely because its mood ("happy") matched the user better than Gym Hero's ("intense") — a result that felt more human and more correct. This changed how I think about real apps like Spotify: their recommendations likely feel good not because the algorithm is smarter, but because their catalog is large enough that genre filtering actually has thousands of songs to choose from, making the heavy genre weight invisible.

---
