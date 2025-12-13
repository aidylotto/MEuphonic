from dataclasses import dataclass
from typing import Dict, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


analyzer = SentimentIntensityAnalyzer()

# Simple arousal (energy) cues; expand anytime
AROUSAL_UP = {"excited", "thrilled", "furious", "rage", "panic", "anxious", "ecstatic", "hyped"}
AROUSAL_DOWN = {"tired", "calm", "peaceful", "empty", "numb", "sleepy", "still", "quiet"}

LABEL_KEYWORDS = {
    "sad": ["sad", "lonely", "heartbroken", "depressed", "melancholy", "cry", "grief", "loss"],
    "happy": ["happy", "joy", "excited", "celebrate", "victory", "smile", "grateful", "hopeful"],
    "angry": ["angry", "furious", "rage", "frustrated", "fight", "hate", "betrayed"],
    "calm": ["calm", "peaceful", "relaxed", "chill", "serene", "soft", "meditative"],
    "romantic": ["love", "romantic", "crush", "tender", "affection", "kiss", "yearning"],
}


@dataclass
class MoodProfile:
    description: str
    label: str
    tempo: int
    energy: float       # 0..1
    valence: float      # -1..1
    mode: str           # major/minor


def _keyword_label(text: str) -> Tuple[str, int]:
    scores: Dict[str, int] = {k: 0 for k in LABEL_KEYWORDS}
    for label, words in LABEL_KEYWORDS.items():
        for w in words:
            if w in text:
                scores[label] += 1
    best = max(scores, key=scores.get)
    return best, scores[best]


def _estimate_energy(text: str, base: float) -> float:
    tokens = set(text.split())
    bump = 0.0
    bump += 0.12 * len(tokens.intersection(AROUSAL_UP))
    bump -= 0.12 * len(tokens.intersection(AROUSAL_DOWN))
    return max(0.0, min(1.0, base + bump))


def analyze_mood(description: str) -> MoodProfile:
    text = description.lower().strip()

    # VADER sentiment: compound is in [-1, 1]
    sentiment = analyzer.polarity_scores(description)
    compound = sentiment["compound"]  # valence estimate

    # base energy from intensity (neg/pos plus punctuation)
    base_energy = min(1.0, max(0.0, 0.35 + 0.35 * (sentiment["pos"] + sentiment["neg"])))
    energy = _estimate_energy(text, base_energy)

    # keyword label with fallback
    label, strength = _keyword_label(text)
    if strength == 0:
        # fallback: label from valence + energy
        if compound < -0.25 and energy < 0.55:
            label = "sad"
        elif compound < -0.25 and energy >= 0.55:
            label = "angry"
        elif compound > 0.25 and energy >= 0.55:
            label = "happy"
        elif compound > 0.25 and energy < 0.55:
            label = "romantic"
        else:
            label = "calm"

    # mode choice from valence
    mode = "minor" if compound < 0 else "major"

    # tempo mapping from energy (keep within a musical range)
    tempo = int(60 + energy * 90)  # 60..150

    return MoodProfile(
        description=description,
        label=label,
        tempo=tempo,
        energy=energy,
        valence=compound,
        mode=mode,
    )
