from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

# ---------------------------------------------------------------------------
# ALGORITHM RECIPE — BASELINE WEIGHT TABLE
#
# These are the default weights used by the "balanced" scoring mode.
# Each weight controls the maximum points a feature can contribute.
#
# Original features:
#   genre (1.0)            -- categorical; mismatch scores zero, not negative
#   mood  (2.0)            -- second strongest categorical signal
#   energy (3.0)           -- best single numerical proxy for "vibe intensity"
#   acousticness (1.0)     -- separates organic (folk/jazz) from electronic (EDM/synth)
#   instrumentalness (1.0) -- separates background listening from vocal tracks
#   valence (0.5)          -- fine-tunes emotional tone (dark vs. upbeat)
#   speechiness (0.5)      -- separates rap/spoken-word from sung tracks
#   acoustic_bonus (0.5)   -- small bonus when user just wants "acoustic" (bool pref)
#
# Advanced features:
#   popularity (0.5)       -- proximity to user's target mainstream appeal (0-100)
#   decade (1.0)           -- decay-based era match; loses 0.25 pts per decade apart
#   detail_mood (1.5)      -- granular tag match (e.g. "euphoric", "aggressive")
#   liveness (0.5)         -- proximity: 1.0 = live concert feel, 0.0 = studio clean
#   loudness (0.5)         -- proximity: 1.0 = loud/dynamic, 0.0 = quiet/gentle
# ---------------------------------------------------------------------------

WEIGHTS = {
    "genre":           1.0,
    "mood":            2.0,
    "energy":          3.0,
    "acousticness":    1.0,
    "instrumentalness":1.0,
    "valence":         0.5,
    "speechiness":     0.5,
    "acoustic_bonus":  0.5,
    "popularity":      0.5,
    "decade":          1.0,
    "detail_mood":     1.5,
    "liveness":        0.5,
    "loudness":        0.5,
}


# ---------------------------------------------------------------------------
# SCORING MODES — Strategy Pattern
#
# Each mode is a partial weight override dict merged onto the baseline WEIGHTS
# at score time. Only the keys that change need to be listed.
#
# Design: _score_core accepts an optional `mode_weights` dict. Inside the
# function a merged dict `w = {**WEIGHTS, **mode_weights}` is built once and
# used for every lookup. Switching strategies = swapping this dict. No
# duplicated logic anywhere.
#
# Modes:
#   balanced      -- baseline weights; no overrides (default)
#   genre_first   -- genre boosted to 4.0; best for strict genre purists
#   mood_first    -- mood+detail_mood boosted; genre becomes a tiebreaker
#   energy_focused -- energy dominates at 6.0; best for intensity matching
#   discovery     -- genre and decade zeroed out; rewards vibe over category
# ---------------------------------------------------------------------------

SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {},   # no overrides; uses WEIGHTS as-is

    # Genre-First: genre is the primary gate. Songs outside the user's genre
    # have almost no chance of appearing. Good for users who will not tolerate
    # recommendations outside their preferred category.
    "genre_first": {
        "genre":       4.0,   # was 1.0 — now the dominant signal
        "mood":        1.0,   # reduced to a secondary tiebreaker
        "energy":      1.5,   # reduced to fine-tuning
        "detail_mood": 0.5,   # reduced; granular tag matters less
    },

    # Mood-First: both the broad mood tag and the granular detail_mood are
    # boosted. Genre becomes nearly irrelevant. Best for users who say "I want
    # something euphoric" without caring whether it is pop or EDM.
    "mood_first": {
        "genre":       0.5,   # reduced to a weak tiebreaker
        "mood":        4.0,   # was 2.0 — primary signal
        "energy":      1.5,   # reduced
        "detail_mood": 3.0,   # was 1.5 — granular tag now very important
    },

    # Energy-Focused: energy proximity dominates at 6.0 points. Every other
    # feature is a minor adjustment. Best for users whose main axis is
    # intensity — workout vs. study vs. background — regardless of genre.
    "energy_focused": {
        "genre":       0.5,   # reduced to near-zero influence
        "mood":        0.5,   # reduced
        "energy":      6.0,   # was 3.0 — completely dominates ranking
        "detail_mood": 0.5,   # reduced
        "decade":      0.0,   # ignored
    },

    # Discovery: genre and era are both zeroed out so the user is exposed to
    # songs they would normally filter away. Mood, energy, and detail_mood
    # still guide the result — but genre label never gatekeeps it.
    "discovery": {
        "genre":       0.0,   # ignored — open to any genre
        "decade":      0.0,   # ignored — open to any era
        "mood":        3.0,   # boosted to compensate for lost genre signal
        "energy":      3.0,   # same as balanced
        "detail_mood": 2.0,   # boosted
    },
}


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """Represents a song and its audio feature attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    speechiness: float = 0.05
    instrumentalness: float = 0.0
    popularity: float = 50.0
    release_decade: float = 2010.0
    detail_mood: str = ""
    liveness: float = 0.10
    loudness: float = 0.60


@dataclass
class UserProfile:
    """Represents a user's stated taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: Optional[float] = None
    target_acousticness: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    target_speechiness: Optional[float] = None
    target_popularity: Optional[float] = None
    preferred_decade: Optional[float] = None
    preferred_detail_mood: Optional[str] = None
    target_liveness: Optional[float] = None
    target_loudness: Optional[float] = None


# ---------------------------------------------------------------------------
# SCORING RULE — applied to one song at a time
# ---------------------------------------------------------------------------

def _proximity(target: float, actual: float, weight: float) -> Tuple[float, float]:
    """Returns (points_earned, proximity_ratio) for a numerical feature."""
    ratio = 1.0 - abs(target - actual)
    return round(weight * ratio, 2), round(ratio, 2)


def _score_core(
    # Song attributes
    genre: str, mood: str, energy: float, acousticness: float,
    instrumentalness: float, valence: float, speechiness: float,
    popularity: float, release_decade: float, detail_mood: str,
    liveness: float, loudness: float,
    # User preferences
    user_genre: str, user_mood: str,
    target_energy: Optional[float],
    target_acousticness: Optional[float],
    likes_acoustic: bool,
    target_instrumentalness: Optional[float],
    target_valence: Optional[float],
    target_speechiness: Optional[float],
    target_popularity: Optional[float],
    preferred_decade: Optional[float],
    preferred_detail_mood: Optional[str],
    target_liveness: Optional[float],
    target_loudness: Optional[float],
    # Strategy: merged weight dict (baseline + mode overrides)
    mode_weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, List[str]]:
    """Scores one song against user preferences using the supplied weight strategy."""
    # Merge baseline with any mode overrides — mode values win on conflict.
    w = {**WEIGHTS, **(mode_weights or {})}

    score = 0.0
    reasons: List[str] = []

    # --- Categorical: Genre ---
    if w["genre"] > 0 and user_genre not in ("any", "") and genre == user_genre:
        score += w["genre"]
        reasons.append(f"genre match '{genre}' (+{w['genre']})")

    # --- Categorical: Mood ---
    if w["mood"] > 0 and user_mood and mood == user_mood:
        score += w["mood"]
        reasons.append(f"mood match '{mood}' (+{w['mood']})")

    # --- Numerical: Energy proximity ---
    if target_energy is not None:
        pts, ratio = _proximity(target_energy, energy, w["energy"])
        score += pts
        reasons.append(f"energy proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Acousticness proximity (two paths) ---
    if target_acousticness is not None:
        pts, ratio = _proximity(target_acousticness, acousticness, w["acousticness"])
        score += pts
        reasons.append(f"acousticness proximity {ratio:.2f} (+{pts})")
    elif likes_acoustic and acousticness > 0.6:
        score += w["acoustic_bonus"]
        reasons.append(f"acoustic bonus (+{w['acoustic_bonus']})")

    # --- Numerical: Instrumentalness proximity ---
    if target_instrumentalness is not None:
        pts, ratio = _proximity(target_instrumentalness, instrumentalness, w["instrumentalness"])
        score += pts
        reasons.append(f"instrumentalness proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Valence proximity ---
    if target_valence is not None:
        pts, ratio = _proximity(target_valence, valence, w["valence"])
        score += pts
        reasons.append(f"valence proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Speechiness proximity ---
    if target_speechiness is not None:
        pts, ratio = _proximity(target_speechiness, speechiness, w["speechiness"])
        score += pts
        reasons.append(f"speechiness proximity {ratio:.2f} (+{pts})")

    # --- ADVANCED: Popularity proximity ---
    if target_popularity is not None:
        pop_ratio = max(0.0, 1.0 - abs(target_popularity - popularity) / 100.0)
        pts = round(w["popularity"] * pop_ratio, 2)
        score += pts
        reasons.append(f"popularity proximity {pop_ratio:.2f} (+{pts})")

    # --- ADVANCED: Decade preference (decay-based) ---
    if w["decade"] > 0 and preferred_decade is not None:
        decades_apart = abs(int(preferred_decade) - int(release_decade)) // 10
        decade_ratio = max(0.0, 1.0 - 0.25 * decades_apart)
        pts = round(w["decade"] * decade_ratio, 2)
        score += pts
        reasons.append(f"decade score {decade_ratio:.2f} ({int(release_decade)}s) (+{pts})")

    # --- ADVANCED: Detail mood exact match ---
    if w["detail_mood"] > 0 and preferred_detail_mood and detail_mood == preferred_detail_mood:
        score += w["detail_mood"]
        reasons.append(f"detail mood match '{detail_mood}' (+{w['detail_mood']})")

    # --- ADVANCED: Liveness proximity ---
    if target_liveness is not None:
        pts, ratio = _proximity(target_liveness, liveness, w["liveness"])
        score += pts
        reasons.append(f"liveness proximity {ratio:.2f} (+{pts})")

    # --- ADVANCED: Loudness proximity ---
    if target_loudness is not None:
        pts, ratio = _proximity(target_loudness, loudness, w["loudness"])
        score += pts
        reasons.append(f"loudness proximity {ratio:.2f} (+{pts})")

    return round(score, 2), reasons


# ---------------------------------------------------------------------------
# OOP INTERFACE  (used by tests/test_recommender.py)
# ---------------------------------------------------------------------------

class Recommender:
    """Ranks songs against a UserProfile using the weighted scoring recipe."""

    def __init__(self, songs: List[Song]):
        """Stores the song catalog that all recommendations will be drawn from."""
        self.songs = songs

    def _score(self, user: UserProfile, song: Song,
               mode: str = "balanced") -> Tuple[float, List[str]]:
        """Scores one song against a UserProfile using the given scoring mode."""
        return _score_core(
            genre=song.genre, mood=song.mood,
            energy=song.energy, acousticness=song.acousticness,
            instrumentalness=song.instrumentalness,
            valence=song.valence, speechiness=song.speechiness,
            popularity=song.popularity, release_decade=song.release_decade,
            detail_mood=song.detail_mood, liveness=song.liveness,
            loudness=song.loudness,
            user_genre=user.favorite_genre, user_mood=user.favorite_mood,
            target_energy=user.target_energy,
            target_acousticness=user.target_acousticness,
            likes_acoustic=user.likes_acoustic,
            target_instrumentalness=user.target_instrumentalness,
            target_valence=user.target_valence,
            target_speechiness=user.target_speechiness,
            target_popularity=user.target_popularity,
            preferred_decade=user.preferred_decade,
            preferred_detail_mood=user.preferred_detail_mood,
            target_liveness=user.target_liveness,
            target_loudness=user.target_loudness,
            mode_weights=SCORING_MODES.get(mode, {}),
        )

    def recommend(self, user: UserProfile, k: int = 5,
                  mode: str = "balanced") -> List[Song]:
        """Returns top-k songs ranked by the given scoring mode."""
        scored = [(song, self._score(user, song, mode)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song,
                                mode: str = "balanced") -> str:
        """Returns a human-readable explanation of the score for the given mode."""
        _, reasons = self._score(user, song, mode)
        return "; ".join(reasons) if reasons else "no matching features found"


# ---------------------------------------------------------------------------
# FUNCTIONAL INTERFACE  (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file, converting numeric fields to float."""
    numeric_fields = {
        "id", "energy", "tempo_bpm", "valence", "danceability",
        "acousticness", "speechiness", "instrumentalness",
        "popularity", "release_decade", "liveness", "loudness",
    }
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            songs.append({
                key: float(val) if key in numeric_fields else val
                for key, val in row.items()
            })
    return songs


def score_song(user_prefs: Dict, song: Dict,
               mode: str = "balanced") -> Tuple[float, List[str]]:
    """Scores one song dict against user preferences using the given mode."""
    return _score_core(
        genre=song.get("genre", ""),
        mood=song.get("mood", ""),
        energy=float(song.get("energy", 0.5)),
        acousticness=float(song.get("acousticness", 0.5)),
        instrumentalness=float(song.get("instrumentalness", 0.0)),
        valence=float(song.get("valence", 0.5)),
        speechiness=float(song.get("speechiness", 0.05)),
        popularity=float(song.get("popularity", 50.0)),
        release_decade=float(song.get("release_decade", 2010.0)),
        detail_mood=song.get("detail_mood", ""),
        liveness=float(song.get("liveness", 0.10)),
        loudness=float(song.get("loudness", 0.60)),
        user_genre=user_prefs.get("genre", "any"),
        user_mood=user_prefs.get("mood", ""),
        target_energy=user_prefs.get("target_energy"),
        target_acousticness=user_prefs.get("target_acousticness"),
        likes_acoustic=bool(user_prefs.get("likes_acoustic", False)),
        target_instrumentalness=user_prefs.get("target_instrumentalness"),
        target_valence=user_prefs.get("target_valence"),
        target_speechiness=user_prefs.get("target_speechiness"),
        target_popularity=user_prefs.get("target_popularity"),
        preferred_decade=user_prefs.get("preferred_decade"),
        preferred_detail_mood=user_prefs.get("preferred_detail_mood"),
        target_liveness=user_prefs.get("target_liveness"),
        target_loudness=user_prefs.get("target_loudness"),
        mode_weights=SCORING_MODES.get(mode, {}),
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    mode: str = "balanced") -> List[Tuple[Dict, float, str]]:
    """Scores every song, sorts descending, returns top-k as (song, score, explanation) tuples."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, mode)
        explanation = "; ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
