import traceback
from typing import List
from pathlib import Path

from mido import Message, MidiFile, MidiTrack, bpm2tempo, MetaMessage

from .melody_engine import generate_melody
from .bass_engine import bass_for_chords
from .drum_engine import drum_hits
from .guitar_engine import arp_pattern, strum_pattern
from .theory_engine import SongPlan


ROOT_NOTES_MID = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71}

# GM instruments
GM_PIANO = 0
GM_EG_CLEAN = 27
GM_EG_OVERDRIVE = 29
GM_EG_DIST = 30
GM_BASS = 33
GM_JAZZ_GUITAR = 26
GM_PAD = 89
GM_FLUTE = 73

DRUM_CH = 9


def _chord_notes(ch: str) -> List[int]:
    root = ROOT_NOTES_MID.get(ch[0].upper(), 60)
    if "m7" in ch:
        return [root, root + 3, root + 7, root + 10]
    if "maj7" in ch:
        return [root, root + 4, root + 7, root + 11]
    if "m" in ch:
        return [root, root + 3, root + 7]
    return [root, root + 4, root + 7]


def render_to_midi(structure, tempo_bpm: int, output_path: str, mood, genre: str) -> str:
    try:
        mid = MidiFile()
        ticks = mid.ticks_per_beat
        bar = 4 * ticks

        chord_t = MidiTrack()
        melody_t = MidiTrack()
        bass_t = MidiTrack()
        drum_t = MidiTrack()
        guitar_t = MidiTrack()

        mid.tracks += [chord_t, melody_t, bass_t, drum_t, guitar_t]

        chord_t.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo_bpm), time=0))

        # --- instrumentation by genre ---
        if genre == "metal":
            chord_t.append(Message("program_change", program=GM_EG_DIST, time=0))
            guitar_t.append(Message("program_change", program=GM_EG_DIST, time=0))
        elif genre == "rock":
            chord_t.append(Message("program_change", program=GM_EG_CLEAN, time=0))
            guitar_t.append(Message("program_change", program=GM_EG_OVERDRIVE, time=0))
        elif genre == "jazz":
            chord_t.append(Message("program_change", program=GM_JAZZ_GUITAR, time=0))
            melody_t.append(Message("program_change", program=GM_FLUTE, time=0))
        elif genre == "ambient":
            chord_t.append(Message("program_change", program=GM_PAD, time=0))
        else:  # pop
            chord_t.append(Message("program_change", program=GM_PIANO, time=0))

        bass_t.append(Message("program_change", program=GM_BASS, time=0))

        # flatten chords
        chords = []
        for sec in structure.sections:
            chords.extend(sec.chords)

        # --- CHORDS ---
        for ch in chords:
            notes = _chord_notes(ch)
            for n in notes:
                chord_t.append(Message("note_on", note=n, velocity=55, time=0))
            for n in notes:
                chord_t.append(Message("note_off", note=n, velocity=0, time=bar))

        # --- BASS ---
        bass_hits = bass_for_chords(chords, activity=0.8 if genre in ("rock", "metal") else 0.4)
        abs_tick = last = 0
        for hits in bass_hits:
            for note, beat in hits:
                t = abs_tick + int(beat * ticks)
                delta = max(0, t - last)
                bass_t.append(Message("note_on", note=note, velocity=80, time=delta))
                bass_t.append(Message("note_off", note=note, velocity=0, time=int(0.3 * ticks)))
                last = t + int(0.3 * ticks)
            abs_tick += bar

        # --- MELODY ---
        root = ROOT_NOTES_MID.get(chords[0][0], 60)
        melody = generate_melody(root, mood, len(chords), melody_density=0.6)

        abs_tick = last = 0
        for note in melody:
            if note is None:
                abs_tick += ticks
                continue
            delta = max(0, abs_tick - last)
            melody_t.append(Message("note_on", note=note, velocity=90, time=delta))
            melody_t.append(Message("note_off", note=note, velocity=0, time=int(0.8 * ticks)))
            last = abs_tick + int(0.8 * ticks)
            abs_tick += ticks

        # --- DRUMS ---
        drum_pattern = drum_hits(
            "rock" if genre in ("rock", "metal") else "soft",
            len(chords),
        )

        last = 0
        for note, beat in drum_pattern:
            t = int(beat * ticks)
            delta = max(0, t - last)
            drum_t.append(Message("note_on", channel=DRUM_CH, note=note, velocity=90, time=delta))
            drum_t.append(Message("note_off", channel=DRUM_CH, note=note, velocity=0, time=int(0.1 * ticks)))
            last = t + int(0.1 * ticks)

        out = Path(output_path).with_suffix(".mid")
        out.parent.mkdir(exist_ok=True)
        mid.save(out)
        return str(out)

    except Exception:
        traceback.print_exc()
        raise
