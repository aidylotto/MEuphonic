from typing import List, Tuple

def arp_pattern(chord_notes: List[int]) -> List[Tuple[int, float]]:
    # 8th-note arpeggio feel
    seq = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
    notes = []
    for i, t in enumerate(seq):
        notes.append((chord_notes[i % len(chord_notes)], t))
    return notes

def strum_pattern(chord_notes: List[int]) -> List[Tuple[int, float]]:
    # simple strum on beats 1 and 3 (with a slight "spread")
    notes = []
    for beat in (0.0, 2.0):
        spread = [0.0, 0.03, 0.06]  # tiny strum feel
        for n, s in zip(chord_notes, spread):
            notes.append((n, beat + s))
    return notes
