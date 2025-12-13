from typing import List, Tuple
import random

ROOT_NOTES = {"C": 36, "D": 38, "E": 40, "F": 41, "G": 43, "A": 45, "B": 47}


def bass_pattern_for_bar(root_note: int, activity: float) -> List[Tuple[int, float]]:
    """
    Returns (note, beat_position_in_bar). Adds 5th/passing notes based on activity.
    """
    hits: List[Tuple[int, float]] = []
    fifth = root_note + 7

    # Always hit root on beat 1
    hits.append((root_note, 0.0))

    # Activity drives extra motion
    if activity > 0.55:
        hits.append((fifth, 1.5))  # upbeat motion

    if activity > 0.75:
        passing = root_note + random.choice([2, 3, 5])  # simple passing tones
        hits.append((passing, 2.5))

    # Often return to root near end
    hits.append((root_note, 3.0))
    return hits


def bass_for_chords(chords: List[str], activity: float) -> List[List[Tuple[int, float]]]:
    """
    For each bar chord, return a bar pattern list of (note, beat_in_bar).
    """
    bars: List[List[Tuple[int, float]]] = []
    for ch in chords:
        root = ch[0].upper()
        root_note = ROOT_NOTES.get(root, 36)
        bars.append(bass_pattern_for_bar(root_note, activity))
    return bars
