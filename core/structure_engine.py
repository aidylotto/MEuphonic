from dataclasses import dataclass
from typing import List

from .theory_engine import SongPlan


@dataclass
class Section:
    name: str
    bars: int
    chords: List[str]


@dataclass
class SongStructure:
    sections: List[Section]


def build_structure(plan: SongPlan) -> SongStructure:
    base_prog = plan.chord_progression

    intro = Section(name="Intro", bars=4, chords=base_prog[:2] * 2)
    verse = Section(name="Verse 1", bars=8, chords=base_prog * 2)
    chorus = Section(name="Chorus", bars=8, chords=base_prog * 2)
    verse2 = Section(name="Verse 2", bars=8, chords=base_prog * 2)
    final_chorus = Section(name="Final Chorus", bars=8, chords=base_prog * 2)
    outro = Section(name="Outro", bars=4, chords=base_prog[:2] * 2)

    return SongStructure(
        sections=[intro, verse, chorus, verse2, final_chorus, outro]
    )
