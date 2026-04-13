from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

# ---------------------------------------------------------------------------
# ALGORITHM RECIPE — WEIGHT TABLE
#
# Each weight controls the maximum points a feature can contribute to a score.
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
# Advanced features (new):
#   popularity (0.5)       -- proximity to user's target mainstream appeal (0-100)
#   decade (1.0)           -- decay-based era match; loses 0.25 pts per decade apart
#   detail_mood (1.5)      -- granular tag match (e.g. "euphoric", "aggressive")
#   liveness (0.5)         -- proximity: 1.0 = live concert feel, 0.0 = studio clean
#   loudness (0.5)         -- proximity: 1.0 = loud/dynamic, 0.0 = quiet/gentle
#
# Max possible score (all optional features active, target_acousticness path):
#   1.0 + 2.0 + 3.0 + 1.0 + 1.0 + 0.5 + 0.5 + 0.5 + 1.0 + 1.5 + 0.5 + 0.5 = 13.0
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
    # --- Advanced features ---
    "popularity":      0.5,   # proximity on normalized 0-1 scale
    "decade":          1.0,   # decay: -0.25 per decade away from preferred era
    "detail_mood":     1.5,   # exact tag match only; no partial credit
    "liveness":        0.5,   # proximity: studio (0) vs. live (1)
    "loudness":        0.5,   # proximity: quiet (0) vs. loud/dynamic (1)
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
    speechiness: float = 0.05        # default: typical sung track
    instrumentalness: float = 0.0    # default: has vocals
    # Advanced features
    popularity: float = 50.0         # mainstream appeal score, 0-100
    release_decade: float = 2010.0   # e.g. 1990.0, 2000.0, 2010.0, 2020.0
    detail_mood: str = ""            # granular tag: euphoric, aggressive, peaceful, etc.
    liveness: float = 0.10           # 0 = studio clean, 1 = live concert feel
    loudness: float = 0.60           # 0 = quiet/gentle, 1 = loud/dynamic


@dataclass
class UserProfile:
    """Represents a user's stated taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional original fine-tuning (None = not specified, skip that feature)
    target_valence: Optional[float] = None
    target_acousticness: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    target_speechiness: Optional[float] = None
    # Optional advanced preferences (None = not specified, skip that feature)
    target_popularity: Optional[float] = None      # 0-100; low = underground, high = mainstream
    preferred_decade: Optional[float] = None       # e.g. 2000.0 for Y2K era vibes
    preferred_detail_mood: Optional[str] = None    # exact granular tag to match
    target_liveness: Optional[float] = None        # 0 = studio, 1 = live
    target_loudness: Optional[float] = None        # 0 = quiet, 1 = loud


# ---------------------------------------------------------------------------
# SCORING RULE — applied to one song at a time
# Returns (score, reasons) where reasons explains each contributing factor.
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
    # Advanced user preferences
    target_popularity: Optional[float],
    preferred_decade: Optional[float],
    preferred_detail_mood: Optional[str],
    target_liveness: Optional[float],
    target_loudness: Optional[float],
) -> Tuple[float, List[str]]:
    """Shared scoring logic used by both the OOP and functional interfaces."""
    score = 0.0
    reasons: List[str] = []

    # --- Categorical: Genre (+1.0 max) ---
    if user_genre not in ("any", "") and genre == user_genre:
        score += WEIGHTS["genre"]
        reasons.append(f"genre match '{genre}' (+{WEIGHTS['genre']})")

    # --- Categorical: Mood (+2.0 max) ---
    if user_mood and mood == user_mood:
        score += WEIGHTS["mood"]
        reasons.append(f"mood match '{mood}' (+{WEIGHTS['mood']})")

    # --- Numerical: Energy proximity (+3.0 max) ---
    if target_energy is not None:
        pts, ratio = _proximity(target_energy, energy, WEIGHTS["energy"])
        score += pts
        reasons.append(f"energy proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Acousticness proximity (+1.0 max) ---
    # Two paths: explicit target takes priority over boolean like/dislike
    if target_acousticness is not None:
        pts, ratio = _proximity(target_acousticness, acousticness, WEIGHTS["acousticness"])
        score += pts
        reasons.append(f"acousticness proximity {ratio:.2f} (+{pts})")
    elif likes_acoustic and acousticness > 0.6:
        score += WEIGHTS["acoustic_bonus"]
        reasons.append(f"acoustic bonus (+{WEIGHTS['acoustic_bonus']})")

    # --- Numerical: Instrumentalness proximity (+1.0 max) ---
    if target_instrumentalness is not None:
        pts, ratio = _proximity(target_instrumentalness, instrumentalness, WEIGHTS["instrumentalness"])
        score += pts
        reasons.append(f"instrumentalness proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Valence proximity (+0.5 max) ---
    if target_valence is not None:
        pts, ratio = _proximity(target_valence, valence, WEIGHTS["valence"])
        score += pts
        reasons.append(f"valence proximity {ratio:.2f} (+{pts})")

    # --- Numerical: Speechiness proximity (+0.5 max) ---
    if target_speechiness is not None:
        pts, ratio = _proximity(target_speechiness, speechiness, WEIGHTS["speechiness"])
        score += pts
        reasons.append(f"speechiness proximity {ratio:.2f} (+{pts})")

    # --- ADVANCED: Popularity proximity (+0.5 max) ---
    # Normalize both values to 0-1 range before applying proximity.
    # target_popularity=20 means "underground"; target_popularity=80 means "mainstream".
    if target_popularity is not None:
        pop_ratio = max(0.0, 1.0 - abs(target_popularity - popularity) / 100.0)
        pts = round(WEIGHTS["popularity"] * pop_ratio, 2)
        score += pts
        reasons.append(f"popularity proximity {pop_ratio:.2f} (+{pts})")

    # --- ADVANCED: Decade preference — decay-based (+1.0 max) ---
    # Exact decade match = full 1.0 points.
    # Each decade away loses 0.25 points (4+ decades away = 0 points).
    # E.g. preferred=2000, actual=2010 -> 1 decade apart -> 0.75 points.
    if preferred_decade is not None:
        decades_apart = abs(int(preferred_decade) - int(release_decade)) // 10
        decade_ratio = max(0.0, 1.0 - 0.25 * decades_apart)
        pts = round(WEIGHTS["decade"] * decade_ratio, 2)
        score += pts
        reasons.append(f"decade score {decade_ratio:.2f} ({int(release_decade)}s) (+{pts})")

    # --- ADVANCED: Detail mood exact match (+1.5 max) ---
    # More specific than the broad mood tag. No partial credit.
    if preferred_detail_mood and detail_mood == preferred_detail_mood:
        score += WEIGHTS["detail_mood"]
        reasons.append(f"detail mood match '{detail_mood}' (+{WEIGHTS['detail_mood']})")

    # --- ADVANCED: Liveness proximity (+0.5 max) ---
    # 0.0 = pure studio recording, 1.0 = live concert feel.
    if target_liveness is not None:
        pts, ratio = _proximity(target_liveness, liveness, WEIGHTS["liveness"])
        score += pts
        reasons.append(f"liveness proximity {ratio:.2f} (+{pts})")

    # --- ADVANCED: Loudness proximity (+0.5 max) ---
    # 0.0 = quiet/gentle, 1.0 = loud/dynamic/hard-hitting.
    if target_loudness is not None:
        pts, ratio = _proximity(target_loudness, loudness, WEIGHTS["loudness"])
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

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Translates a UserProfile and Song into _score_core arguments and returns (score, reasons)."""
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
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Scores every song in the catalog and returns the top-k matches for the given user."""
        scored = [(song, self._score(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a human-readable string listing every scoring reason for the given song."""
        _, reasons = self._score(user, song)
        return "; ".join(reasons) if reasons else "no matching features found"


# ---------------------------------------------------------------------------
# FUNCTIONAL INTERFACE  (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file, converting numeric fields to float."""
    numeric_fields = {
        "id", "energy", "tempo_bpm", "valence", "danceability",
        "acousticness", "speechiness", "instrumentalness",
        # Advanced numeric fields
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


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Scores one song dict against user preferences and returns (score, reasons)."""
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
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Scores every song, sorts by score descending, and returns the top-k as (song, score, explanation) tuples."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "no matching features"
        scored.append((song, score, explanation))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
