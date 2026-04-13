"""
Command line runner for the Music Recommender Simulation.

This file defines user taste profiles and runs the recommender.
You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# USER TASTE PROFILES
# Each profile is a dictionary of preference signals your score_song function
# will compare against every song in the catalog.
#
# Features used:
#   genre              (str)   -- preferred genre label
#   mood               (str)   -- preferred mood label
#   target_energy      (float) -- ideal energy level, 0.0 (calm) to 1.0 (intense)
#   target_valence     (float) -- ideal emotional brightness, 0.0 (dark) to 1.0 (upbeat)
#   likes_acoustic     (bool)  -- True = prefers organic/acoustic sound
#   target_instrumentalness (float) -- 1.0 = wants fully instrumental (no vocals)
#   target_speechiness (float) -- 1.0 = wants rap/spoken word style
# ---------------------------------------------------------------------------

# Profile 1: High-Energy Pop
# Upbeat, danceable pop -- high energy, high valence, very low instrumentalness
high_energy_pop = {
    "genre": "pop",
    "mood": "happy",
    "target_energy": 0.85,
    "target_valence": 0.82,
    "likes_acoustic": False,
    "target_acousticness": 0.15,
    "target_instrumentalness": 0.00,
    "target_speechiness": 0.06,
}

# Profile 2: Chill Lofi
# Quiet, wordless background music for studying -- high instrumentalness is critical
chill_lofi = {
    "genre": "lofi",
    "mood": "focused",
    "target_energy": 0.40,
    "target_valence": 0.58,
    "likes_acoustic": True,
    "target_acousticness": 0.78,
    "target_instrumentalness": 0.88,
    "target_speechiness": 0.03,
}

# Profile 3: Deep Intense Rock
# Heavy, aggressive tracks -- high energy, low valence, loud and electric
deep_intense_rock = {
    "genre": "rock",
    "mood": "intense",
    "target_energy": 0.91,
    "target_valence": 0.48,
    "likes_acoustic": False,
    "target_acousticness": 0.10,
    "target_instrumentalness": 0.02,
    "target_speechiness": 0.06,
}

# Profile 4: Late-night study session (kept for edge case critique)
study_user = chill_lofi

# Profile 5: Morning workout (kept for backwards compatibility)
workout_user = deep_intense_rock

# Profile 6: Vague chill listener (edge case -- no genre set)
vague_user = {
    "genre": "any",
    "mood": "chill",
    "target_energy": 0.40,
    "target_valence": 0.60,
    "likes_acoustic": False,
    "target_instrumentalness": 0.50,
    "target_speechiness": 0.05,
}

# ---------------------------------------------------------------------------
# CRITIQUE: Does the profile differentiate "intense rock" vs "chill lofi"?
#
# Song: Storm Runner (rock, intense)
#   energy=0.91, valence=0.48, acousticness=0.10, instrumentalness=0.00
#
# Song: Library Rain (lofi, chill)
#   energy=0.35, valence=0.60, acousticness=0.86, instrumentalness=0.92
#
# FULL PROFILE (study_user / workout_user):
#   energy alone separates them (0.91 vs 0.35) -- score gap is wide
#   instrumentalness adds a second axis: 0.00 vs 0.92 -- rock is penalized hard
#   genre + mood add a third lock -- three independent dimensions all point correctly
#   Verdict: DIFFERENTIATED cleanly
#
# NARROW PROFILE (vague_user, genre="any"):
#   energy still separates them, so basic ranking works
#   BUT: a classical song (energy=0.22) now scores HIGHER than lofi (energy=0.35)
#   because it is also closer to target_energy=0.40 -- wrong result
#   mood="chill" has no match in the catalog for classical, which saves it --
#   but only by accident, not by design
#   Verdict: FRAGILE -- correct output for the wrong reasons
#
# MISSING DIMENSION problem:
#   If a user wants "chill but electronic" (low energy, no acousticness),
#   no profile above captures that. synthwave Night Drive Loop (energy=0.75)
#   would score low on energy proximity but there is no way to reward its
#   electronic texture without a target_acousticness preference in the profile.
#   Adding "target_acousticness" to every profile would close this gap.
# ---------------------------------------------------------------------------


def print_recommendations(label: str, user_prefs: dict, songs: list, k: int = 3) -> None:
    """Prints a clean, readable block of recommendations for one user profile."""
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print(f"\n{'=' * 60}")
    print(f"  PROFILE : {label}")
    print(f"  GENRE   : {user_prefs.get('genre', 'any').upper():<10}  "
          f"MOOD: {user_prefs.get('mood', '—').upper():<10}  "
          f"ENERGY: {user_prefs.get('target_energy', '—')}")
    print(f"{'=' * 60}")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        # Score bar — 9.5 is the max possible score
        filled = int((score / 9.5) * 20)
        bar = "#" * filled + "-" * (20 - filled)

        print(f"\n  #{rank}  {song['title']}  -  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']:<10}  Energy: {song['energy']}")
        print(f"       Score: {score:>5.2f} / 9.50  [{bar}]")
        print(f"       Why:")
        for reason in explanation.split("; "):
            print(f"         * {reason}")

    print(f"\n{'-' * 60}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded songs: {len(songs)}")

    # --- Standard profiles ---
    standard_profiles = {
        "High-Energy Pop": high_energy_pop,
        "Chill Lofi": chill_lofi,
        "Deep Intense Rock": deep_intense_rock,
    }

    # --- Adversarial / edge case profiles ---
    # Each one is designed to expose a specific weakness in the scoring logic.

    # EDGE CASE 1: Conflicting energy + mood
    # energy=0.9 screams "intense" but mood="sad" — no song in the catalog is both.
    # Expected failure: system is forced to choose between high energy OR sad mood,
    # it cannot satisfy both. Watch which dimension wins.
    conflicting_energy_mood = {
        "genre": "blues",
        "mood": "sad",
        "target_energy": 0.90,
        "target_valence": 0.20,
        "likes_acoustic": False,
        "target_acousticness": 0.10,
        "target_instrumentalness": 0.10,
        "target_speechiness": 0.05,
    }

    # EDGE CASE 2: Ghost genre (not in catalog)
    # Genre "metal" does not exist in the 18-song catalog.
    # Expected failure: zero genre points for every song — system falls back to
    # mood and energy only, recommending songs the user almost certainly doesn't want.
    ghost_genre = {
        "genre": "metal",
        "mood": "intense",
        "target_energy": 0.95,
        "target_valence": 0.30,
        "likes_acoustic": False,
        "target_acousticness": 0.05,
        "target_instrumentalness": 0.05,
        "target_speechiness": 0.05,
    }

    # EDGE CASE 3: Contradictory acousticness + instrumentalness
    # Wants fully instrumental (instrumentalness=1.0) but also fully electronic
    # (acousticness=0.0). In the catalog, instrumental songs are almost always
    # acoustic (lofi, classical, ambient). This profile wants something that
    # doesn't exist: a silent EDM track with no vocals.
    impossible_combo = {
        "genre": "edm",
        "mood": "euphoric",
        "target_energy": 0.97,
        "target_valence": 0.83,
        "likes_acoustic": False,
        "target_acousticness": 0.02,
        "target_instrumentalness": 1.00,
        "target_speechiness": 0.02,
    }

    # EDGE CASE 4: The "Middle of Everything" user
    # Every preference is set to the midpoint (0.5).
    # Expected failure: no song scores badly, but no song scores well either.
    # The system returns whoever happened to land closest to dead-center —
    # revealing that "average" preferences produce meaningless recommendations.
    middle_of_everything = {
        "genre": "any",
        "mood": "",
        "target_energy": 0.50,
        "target_valence": 0.50,
        "likes_acoustic": False,
        "target_acousticness": 0.50,
        "target_instrumentalness": 0.50,
        "target_speechiness": 0.05,
    }

    adversarial_profiles = {
        "EDGE 1 — Conflicting Energy + Sad Mood": conflicting_energy_mood,
        "EDGE 2 — Ghost Genre (metal, not in catalog)": ghost_genre,
        "EDGE 3 — Impossible Combo (EDM + fully instrumental)": impossible_combo,
        "EDGE 4 — Middle of Everything (all 0.5)": middle_of_everything,
    }

    # -----------------------------------------------------------------------
    # ADVANCED FEATURE PROFILES
    # Each profile uses one or more of the five new attributes:
    #   target_popularity, preferred_decade, preferred_detail_mood,
    #   target_liveness, target_loudness
    # -----------------------------------------------------------------------

    # ADVANCED 1: Y2K Nostalgic Jazz Listener
    # Wants 2000s-era jazz with a nostalgic granular tag and a live-room feel.
    # preferred_decade=2000 rewards Coffee Shop Stories (jazz, 2000, nostalgic)
    # and penalizes 2020s releases by 0.5 points.
    # target_liveness=0.4 rewards the slight live feel of Coffee Shop Stories (0.45).
    y2k_jazz = {
        "genre": "jazz",
        "mood": "relaxed",
        "target_energy": 0.35,
        "target_valence": 0.70,
        "likes_acoustic": True,
        "target_acousticness": 0.85,
        "target_instrumentalness": 0.70,
        "target_speechiness": 0.04,
        "preferred_decade": 2000,
        "preferred_detail_mood": "nostalgic",
        "target_liveness": 0.40,
        "target_loudness": 0.40,
    }

    # ADVANCED 2: Underground Aggressive Hip-Hop
    # Wants low-popularity (underground) tracks with an aggressive detail mood
    # and loud/dynamic sound. target_popularity=30 penalizes mainstream songs
    # like Gym Hero (81) and rewards less-known catalog entries.
    # preferred_detail_mood="aggressive" adds +1.5 for Block by Block and Storm Runner.
    underground_hiphop = {
        "genre": "hip-hop",
        "mood": "motivated",
        "target_energy": 0.80,
        "target_valence": 0.65,
        "likes_acoustic": False,
        "target_acousticness": 0.10,
        "target_instrumentalness": 0.05,
        "target_speechiness": 0.25,
        "target_popularity": 30,
        "preferred_decade": 2010,
        "preferred_detail_mood": "aggressive",
        "target_liveness": 0.10,
        "target_loudness": 0.85,
    }

    advanced_profiles = {
        "ADVANCED 1 — Y2K Nostalgic Jazz (2000s era, live feel)": y2k_jazz,
        "ADVANCED 2 — Underground Aggressive Hip-Hop (low popularity)": underground_hiphop,
    }

    print("\n" + "#" * 60)
    print("  STANDARD PROFILES")
    print("#" * 60)
    for label, user_prefs in standard_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)

    print("\n" + "#" * 60)
    print("  ADVERSARIAL / EDGE CASE PROFILES")
    print("#" * 60)
    for label, user_prefs in adversarial_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)

    print("\n" + "#" * 60)
    print("  ADVANCED FEATURE PROFILES")
    print("#" * 60)
    for label, user_prefs in advanced_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)


if __name__ == "__main__":
    main()
