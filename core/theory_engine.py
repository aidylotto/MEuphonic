from dataclasses import dataclass
from typing import List

from .emotion_engine import MoodProfile


@dataclass
class SongPlan:
    key: str
    scale_mode: str
    chord_progression: List[str]
    tempo: int


def _choose_key(mood: MoodProfile) -> str:
    if mood.label in ("sad", "romantic"):
        return "A"
    if mood.label == "angry":
        return "E"
    if mood.label == "calm":
        return "D"
    return "C"


def _progression_for_mood(mood: MoodProfile) -> List[str]:
    if mood.label == "sad":
        return ["Am", "F", "C", "G"]
    elif mood.label == "angry":
        return ["Em", "G", "D", "A"]
    elif mood.label == "calm":
        return ["D", "G", "Em", "A"]
    elif mood.label == "romantic":
        return ["F", "G", "Em", "Am"]
    else:
        return ["C", "G", "Am", "F"]


def plan_song(mood: MoodProfile) -> SongPlan:
    key = _choose_key(mood)
    chords = _progression_for_mood(mood)

    return SongPlan(
        key=key,
        scale_mode=mood.mode,
        chord_progression=chords,
        tempo=mood.tempo,
    )
