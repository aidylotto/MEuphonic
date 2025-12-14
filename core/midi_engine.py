from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
from pathlib import Path
from typing import List
from core.ai_music_brain import MusicProfile
from core.harmony_engine import build_progression
from core.groove_engine import groove_for_bar

# General MIDI programs
GM_PIANO = 0
GM_BASS = 33
GM_GUITAR = 29
GM_STRINGS = 48
GM_PAD = 89

ROOTS = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69}

SECTION_ORDER = [
    ("Intro", 4),
    ("Verse", 8),
    ("Chorus", 8),
    ("Verse", 8),
    ("Chorus", 8),
    ("Bridge", 4),
    ("Final Chorus", 8),
    ("Outro", 4),
]


def chord_notes(root: int, minor: bool) -> List[int]:
    return [root, root + (3 if minor else 4), root + 7]


def section_intensity(name: str) -> float:
    if "Intro" in name or "Outro" in name:
        return 0.4
    if "Verse" in name:
        return 0.6
    if "Chorus" in name:
        return 0.85
    if "Bridge" in name:
        return 0.7
    return 0.6


def render_to_midi(profile: MusicProfile, output_path: str) -> str:
    mid = MidiFile()
    ticks = mid.ticks_per_beat
    bar_ticks = ticks * 4

    chord_track = MidiTrack()
    bass_track = MidiTrack()
    melody_track = MidiTrack()
    pad_track = MidiTrack()
    drum_track = MidiTrack()

    mid.tracks.extend([chord_track, bass_track, melody_track, pad_track, drum_track])

    DRUM_CH = 9

    chord_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(profile.tempo), time=0))

    # Instruments
    chord_track.append(Message("program_change", program=GM_PIANO, time=0))
    bass_track.append(Message("program_change", program=GM_BASS, time=0))
    melody_track.append(Message("program_change", program=GM_GUITAR, time=0))
    pad_track.append(Message("program_change", program=GM_PAD, time=0))

    root_note = ROOTS.get("A", 60)
    minor = profile.scale != "major"

    abs_tick = 0

    for section, bars in SECTION_ORDER:
        intensity = section_intensity(section)
        velocity = int(45 + intensity * 45)

        for _ in range(bars):
            # --- HARMONY ---
            roots = build_progression(profile, section, root_note)
            notes = chord_notes(roots[0], minor)

            chord_track.append(Message("note_on", note=notes[0], velocity=velocity, time=abs_tick))
            for n in notes[1:]:
                chord_track.append(Message("note_on", note=n, velocity=velocity, time=0))
            for i, n in enumerate(notes):
                chord_track.append(Message("note_off", note=n, velocity=0, time=bar_ticks if i == 0 else 0))

            # --- BASS ---
            if intensity > 0.45:
                bass_track.append(Message("note_on", note=roots[0] - 12, velocity=velocity, time=abs_tick))
                bass_track.append(Message("note_off", note=roots[0] - 12, velocity=0, time=bar_ticks))

            # --- MELODY (PHRASED) ---
            if intensity > 0.65:
                melody_track.append(
                    Message("note_on", note=roots[0] + 12, velocity=velocity + 10, time=abs_tick)
                )
                melody_track.append(
                    Message("note_off", note=roots[0] + 12, velocity=0, time=int(bar_ticks * 0.75))
                )

            # --- DRUMS ---
            events = groove_for_bar(profile.genre, section, profile.energy)
            last = 0
            for note, beat, vel in sorted(events, key=lambda x: x[1]):
                t = int(beat * ticks)
                drum_track.append(
                    Message("note_on", channel=DRUM_CH, note=note, velocity=vel, time=max(0, t - last))
                )
                drum_track.append(
                    Message("note_off", channel=DRUM_CH, note=note, velocity=0, time=int(0.1 * ticks))
                )
                last = t + int(0.1 * ticks)

            abs_tick = 0  # reset for next bar; MIDI deltas handled above

        if "Chorus" in section:
            root_note += 2  # lift

    out = Path(output_path)
    out.parent.mkdir(exist_ok=True)
    mid.save(out)
    return str(out)

