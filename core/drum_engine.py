from typing import List, Tuple

KICK = 36
SNARE = 38
HAT_CLOSED = 42
HAT_OPEN = 46


def drum_hits(style: str, total_bars: int, beats_per_bar: int = 4) -> List[Tuple[int, float]]:
    """
    Returns list of (note, beat_position) where beat_position can be fractional:
    0.0, 0.5, 1.0, 1.5 ... measured in beats from song start.
    """
    hits: List[Tuple[int, float]] = []
    total_beats = total_bars * beats_per_bar

    for b in range(total_beats):
        beat_in_bar = b % beats_per_bar
        base = float(b)

        if style == "ambient":
            # very sparse: kick on 1, soft hat on 3
            if beat_in_bar == 0:
                hits.append((KICK, base))
            if beat_in_bar == 2:
                hits.append((HAT_CLOSED, base))
            continue

        if style == "lofi":
            # lofi: kick on 1, snare on 3, hats on 8ths
            if beat_in_bar == 0:
                hits.append((KICK, base))
            if beat_in_bar == 2:
                hits.append((SNARE, base))
            hits.append((HAT_CLOSED, base))
            hits.append((HAT_CLOSED, base + 0.5))
            continue

        # rock / default: backbeat + hats + small kick variation
        if beat_in_bar in (0, 2):
            hits.append((KICK, base))
        if beat_in_bar in (1, 3):
            hits.append((SNARE, base))

        # 8th hats
        hits.append((HAT_CLOSED, base))
        hits.append((HAT_CLOSED, base + 0.5))

        # occasional open hat on bar end (adds adult feel)
        if beat_in_bar == 3:
            hits.append((HAT_OPEN, base + 0.5))

    return hits
