# core/bass_engine.py

from typing import List

ROOT_NOTES = {"C": 36, "D": 38, "E": 40, "F": 41, "G": 43, "A": 45, "B": 47}


def bass_for_chords(chords: List[str]) -> List[int]:
    """
    Simple bassline: root note each bar, in a low octave.
    """
    bass = []
    for ch in chords:
        root = ch[0].upper()
        bass.append(ROOT_NOTES.get(root, 36))
    return bass
