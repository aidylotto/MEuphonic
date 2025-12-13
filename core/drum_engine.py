# core/drum_engine.py

from typing import List, Tuple

# MIDI Channel 9 (0-indexed 9, 1-indexed channel 10) is drums in General MIDI.
KICK = 36
SNARE = 38
HAT_CLOSED = 42


def drum_pattern(total_bars: int, beats_per_bar: int = 4) -> List[Tuple[int, int]]:
    """
    Returns a list of (midi_note, beat_index) hits.
    beat_index is in 'beats' (not ticks): 0..(total_bars*beats_per_bar - 1)
    """
    hits: List[Tuple[int, int]] = []
    total_beats = total_bars * beats_per_bar

    for b in range(total_beats):
        beat_in_bar = b % beats_per_bar

        # Kick on 1 and 3
        if beat_in_bar in (0, 2):
            hits.append((KICK, b))

        # Snare on 2 and 4
        if beat_in_bar in (1, 3):
            hits.append((SNARE, b))

        # Closed hat every beat
        hits.append((HAT_CLOSED, b))

    return hits
