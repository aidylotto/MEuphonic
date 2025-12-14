from dataclasses import dataclass
from typing import List
import numpy as np

from sentence_transformers import SentenceTransformer

from .emotion_engine import MoodProfile


# Load once (fast after first run)
_EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")


@dataclass
class SongPlan:
    key: str
    scale_mode: str
    chord_progression: List[str]
    tempo: int
    genre: str


# --- Genre prototypes (semantic anchors) ---
GENRE_PROFILES = {
    "rock": {
        "text": "emotional rock song, guitar driven, adult, expressive, band",
        "tempo": (100, 140),
        "progressions": [
            ["Am", "F", "C", "G"],
            ["Em", "G", "D", "A"],
        ],
        "key": "A",
    },
    "metal": {
        "text": "heavy metal aggressive powerful dark intense",
        "tempo": (130, 180),
        "progressions": [
            ["Em", "C", "D", "Em"],
            ["Dm", "C", "Bb", "C"],
        ],
        "key": "E",
    },
    "jazz": {
        "text": "jazz sophisticated moody late night club",
        "tempo": (90, 150),
        "progressions": [
            ["Dm7", "G7", "Cmaj7", "Cmaj7"],
            ["Cm7", "F7", "Bbmaj7", "Ebmaj7"],
        ],
        "key": "C",
    },
    "pop": {
        "text": "modern pop emotional catchy mainstream",
        "tempo": (85, 125),
        "progressions": [
            ["C", "G", "Am", "F"],
            ["F", "G", "Em", "Am"],
        ],
        "key": "C",
    },
    "ambient": {
        "text": "ambient calm atmospheric cinematic emotional",
        "tempo": (60, 90),
        "progressions": [
            ["Am", "Em", "F", "C"],
            ["Dm", "Am", "G", "F"],
        ],
        "key": "D",
    },
}


def _pick_genre_by_text(description: str) -> str:
    desc_emb = _EMBEDDER.encode(description, normalize_embeddings=True)

    best_genre = "pop"
    best_score = -1.0

    for genre, cfg in GENRE_PROFILES.items():
        g_emb = _EMBEDDER.encode(cfg["text"], normalize_embeddings=True)
        score = float(np.dot(desc_emb, g_emb))
        if score > best_score:
            best_score = score
            best_genre = genre

    return best_genre


def plan_song(mood: MoodProfile, genre: str | None = None) -> SongPlan:
    """
    AI-assisted planning:
    - genre chosen semantically from text if not forced
    - mood modulates tempo + mode
    """

    if genre is None or genre == "auto":
        genre = _pick_genre_by_text(mood.description)

    cfg = GENRE_PROFILES.get(genre, GENRE_PROFILES["pop"])

    # tempo modulation by energy
    t_min, t_max = cfg["tempo"]
    tempo = int(t_min + (t_max - t_min) * mood.energy)

    # choose progression deterministically but varied
    prog = cfg["progressions"][0 if mood.energy < 0.6 else 1]

    # emotional mode
    scale_mode = "minor" if mood.label in ("sad", "romantic") else "major"

    return SongPlan(
        key=cfg["key"],
        scale_mode=scale_mode,
        chord_progression=prog,
        tempo=tempo,
        genre=genre,
    )
