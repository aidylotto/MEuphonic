from typing import List
from dataclasses import dataclass
from core.ai_music_brain import MusicProfile

# Scale degrees relative to tonic (in semitones)
MAJOR = {
    "I": 0,
    "ii": 2,
    "iii": 4,
    "IV": 5,
    "V": 7,
    "vi": 9,
    "vii°": 11,
}

MINOR = {
    "i": 0,
    "ii°": 2,
    "III": 3,
    "iv": 5,
    "v": 7,
    "VI": 8,
    "VII": 10,
}

# Borrowed / color chords (modal interchange)
BORROWED = {
    "bVI": 8,
    "bVII": 10,
    "IVmaj": 5,
}


@dataclass
class HarmonicContext:
    tonic: int
    scale: str
    risk: float  # 0.0 = safe pop, 1.0 = daring jazz/metal


def build_progression(
    profile: MusicProfile,
    section: str,
    tonic: int
) -> List[int]:
    """
    Returns chord roots (MIDI note numbers) for ONE BAR
    """

    ctx = HarmonicContext(
        tonic=tonic,
        scale=profile.scale,
        risk=min(1.0, profile.energy + (0.2 if profile.genre in ("jazz", "metal") else 0.0)),
    )

    # --- Section intent ---
    if section in ("Intro", "Outro"):
        tension = 0.2
    elif "Verse" in section:
        tension = 0.4
    elif "Chorus" in section:
        tension = 0.8
    elif "Bridge" in section:
        tension = 0.7
    else:
        tension = 0.4

    # --- Safe functional harmony ---
    if ctx.scale == "major":
        base = MAJOR
        tonic_deg = "I"
        dom = "V"
        pre = "IV"
    else:
        base = MINOR
        tonic_deg = "i"
        dom = "v"
        pre = "iv"

    # --- Decide chord role ---
    if tension < 0.3:
        degree = tonic_deg
    elif tension < 0.6:
        degree = pre
    else:
        degree = dom

    # --- Risky borrowing ---
    if ctx.risk > 0.6 and section in ("Chorus", "Bridge"):
        degree = "bVII" if ctx.scale == "minor" else "bVI"

    semitone = base.get(degree) or BORROWED.get(degree, 0)
    return [ctx.tonic + semitone]
