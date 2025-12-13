# core/melody_engine.py

import random
from typing import List

from .emotion_engine import MoodProfile


SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
}


def generate_melody(
    root_note: int,
    mood: MoodProfile,
    total_bars: int,
    beats_per_bar: int = 4,
) -> List[int]:
    scale = SCALES[mood.mode]
    melody = []

    notes_count = total_bars * beats_per_bar

    base_octave = root_note + 12  # above chords

    for i in range(notes_count):
        degree = random.choice(scale)
        note = base_octave + degree

        # emotional shaping
        if mood.energy < 0.4:
            note -= random.choice([0, 2])   # more stepwise
        elif mood.energy > 0.7:
            note += random.choice([0, 2, 4])

        melody.append(note)

    return melody
