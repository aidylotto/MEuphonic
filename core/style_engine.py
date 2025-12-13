from dataclasses import dataclass
from typing import Optional

from .emotion_engine import MoodProfile


@dataclass(frozen=True)
class StyleProfile:
    name: str
    drums: str                  # "lofi" | "rock" | "ambient"
    guitar: Optional[str]       # None | "clean" | "overdrive" | "distortion"
    chord_style: str            # "block" | "arp" | "strum"
    bass_activity: float        # 0..1 (how much bass moves)
    melody_density: float       # 0..1 (rests/phrases)
    chorus_lift: int            # semitones to lift chorus melody


def select_style(mood: MoodProfile) -> StyleProfile:
    # Song-like, adult defaults (avoid lullaby)
    if mood.label == "angry" or mood.energy >= 0.75:
        return StyleProfile(
            name="angry_rock",
            drums="rock",
            guitar="distortion",
            chord_style="strum",
            bass_activity=0.9,
            melody_density=0.85,
            chorus_lift=0,
        )

    if mood.label in ("sad", "romantic") and mood.energy < 0.55:
        return StyleProfile(
            name="indie_melancholy",
            drums="lofi",
            guitar="clean",
            chord_style="arp",
            bass_activity=0.65,
            melody_density=0.55,  # more rests
            chorus_lift=12,       # chorus lifts
        )

    # Default modern pop/indie
    return StyleProfile(
        name="indie_pop",
        drums="rock",
        guitar="overdrive" if mood.energy > 0.6 else "clean",
        chord_style="strum",
        bass_activity=0.7,
        melody_density=0.75,
        chorus_lift=12,
    )
