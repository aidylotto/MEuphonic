from typing import List, Tuple

# General MIDI Drum notes (channel 10 / index 9 in MIDI)
KICK = 36
SNARE = 38
CL_HAT = 42
OP_HAT = 46
RIDE = 51

# event: (note, beat_position_in_bar, velocity)
DrumEvent = Tuple[int, float, int]


def _intensity(section: str) -> float:
    if "Intro" in section or "Outro" in section:
        return 0.35
    if "Verse" in section:
        return 0.60
    if "Bridge" in section:
        return 0.70
    if "Chorus" in section:
        return 0.90
    return 0.60


def groove_for_bar(genre: str, section: str, energy: float) -> List[DrumEvent]:
    """
    Returns drum hits for ONE bar (4/4), beat positions in [0,4).
    """
    inten = _intensity(section)
    dens = min(1.0, max(0.0, (energy * 0.6 + inten * 0.6)))

    # Ambient: very sparse (no constant ticks)
    if genre == "ambient":
        ev: List[DrumEvent] = []
        if dens > 0.65 and "Chorus" in section:
            ev.append((KICK, 0.0, 70))
            ev.append((OP_HAT, 2.0, 50))
        return ev

    # Pop: four-on-the-floor + clap/snare on 2/4, hats 8ths (chorus), 4ths (verse)
    if genre == "pop":
        ev = [(KICK, 0.0, 92), (KICK, 1.0, 86), (KICK, 2.0, 92), (KICK, 3.0, 86)]
        ev += [(SNARE, 1.0, 88), (SNARE, 3.0, 88)]
        hat_step = 0.5 if dens > 0.65 else 1.0
        t = 0.0
        while t < 4.0:
            ev.append((CL_HAT, t, 55 if t % 1.0 else 60))
            t += hat_step
        return ev

    # Rock: kick/snare backbeat; hats 8ths in chorus
    if genre == "rock":
        ev = [(KICK, 0.0, 92), (SNARE, 1.0, 92), (KICK, 2.0, 88), (SNARE, 3.0, 92)]
        if dens > 0.55:
            # add extra kick push
            ev.append((KICK, 2.5, 78))
        # hats
        step = 0.5 if ("Chorus" in section or dens > 0.75) else 1.0
        t = 0.0
        while t < 4.0:
            ev.append((CL_HAT, t, 58))
            t += step
        # open hat lift at bar end in chorus
        if "Chorus" in section and dens > 0.7:
            ev.append((OP_HAT, 3.5, 62))
        return ev

    # Metal: double-kick flavor + tight hats; snare on 2/4; denser when energy high
    if genre == "metal":
        ev = [(SNARE, 1.0, 98), (SNARE, 3.0, 98)]
        # Kick pattern: 8ths or 16ths-ish depending on density
        kick_step = 0.5 if dens < 0.75 else 0.25
        t = 0.0
        while t < 4.0:
            ev.append((KICK, t, 95 if t % 1.0 == 0 else 82))
            t += kick_step
        # hats: steady 8ths (or ride in chorus)
        if "Chorus" in section and dens > 0.75:
            t = 0.0
            while t < 4.0:
                ev.append((RIDE, t, 70))
                t += 0.5
        else:
            t = 0.0
            while t < 4.0:
                ev.append((CL_HAT, t, 62))
                t += 0.5
        return ev

    # Jazz: swing ride pattern + light kick; brushes feel via lower velocities
    if genre == "jazz":
        ev: List[DrumEvent] = []
        # Ride: swing "ding-ding-da-ding" feel approximation
        ev += [(RIDE, 0.0, 68), (RIDE, 1.0, 62), (RIDE, 2.0, 68), (RIDE, 3.0, 62)]
        if dens > 0.55:
            ev.append((CL_HAT, 2.0, 55))  # hi-hat close on 2
            ev.append((CL_HAT, 4.0 - 0.001, 55))  # subtle close near end
        # Light kick “feathering”
        if dens > 0.5:
            ev.append((KICK, 0.0, 45))
            ev.append((KICK, 2.0, 45))
        # Snare comping in chorus/bridge
        if ("Bridge" in section or "Chorus" in section) and dens > 0.6:
            ev.append((SNARE, 1.5, 52))
            ev.append((SNARE, 2.5, 52))
        return ev

    # Fallback: simple backbeat
    return [(KICK, 0.0, 86), (SNARE, 1.0, 86), (KICK, 2.0, 80), (SNARE, 3.0, 86)]
