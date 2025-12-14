from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

GENRES = {
    "rock": ["electric guitar", "drums", "bass", "power"],
    "metal": ["distortion", "aggressive", "dark"],
    "jazz": ["swing", "complex harmony", "improvisation"],
    "pop": ["catchy", "simple", "emotional"],
    "ambient": ["slow", "pads", "atmosphere"],
    "classical": ["orchestral", "strings", "piano"]
}

@dataclass
class MusicProfile:
    genre: str
    tempo: int
    scale: str
    energy: float


def analyze_text_to_music(description: str) -> MusicProfile:
    desc_vec = model.encode(description)

    best_genre = "pop"
    best_score = -1

    for genre, keywords in GENRES.items():
        kw_vec = model.encode(" ".join(keywords))
        score = np.dot(desc_vec, kw_vec)
        if score > best_score:
            best_score = score
            best_genre = genre

    energy = min(1.0, max(0.2, best_score / 10))

    tempo_map = {
        "ambient": 60,
        "jazz": 90,
        "pop": 100,
        "rock": 120,
        "metal": 150,
        "classical": 70
    }

    scale_map = {
        "metal": "minor",
        "rock": "minor",
        "ambient": "minor",
        "jazz": "dorian",
        "pop": "major",
        "classical": "minor"
    }

    return MusicProfile(
        genre=best_genre,
        tempo=tempo_map[best_genre],
        scale=scale_map[best_genre],
        energy=energy
    )
