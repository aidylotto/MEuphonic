import random
from typing import List, Optional

from .emotion_engine import MoodProfile

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
}


def generate_melody(
    root_note: int,
    mood: MoodProfile,
    total_bars: int,
    melody_density: float,
    beats_per_bar: int = 4,
) -> List[Optional[int]]:
    """
    Returns a list of Optional[int] per beat (None = rest).
    Uses small motifs so it feels like a "song", not random notes.
    """
    scale = SCALES[mood.mode]
    beats = total_bars * beats_per_bar

    # A simple motif (relative degrees) repeated with variation
    motif = [0, 2, 4, 2] if mood.valence >= 0 else [0, 2, 3, 2]
    base_octave = root_note + 12

    melody: List[Optional[int]] = []
    for i in range(beats):
        # rests for phrasing (adult feel)
        if random.random() > melody_density:
            melody.append(None)
            continue

        deg = motif[i % len(motif)]
        note = base_octave + scale[deg % len(scale)]

        # energy drives occasional leaps
        if mood.energy > 0.7 and random.random() < 0.25:
            note += random.choice([2, 4, 7])

        melody.append(note)

    return melody
