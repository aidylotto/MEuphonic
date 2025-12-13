from typing import List
from pathlib import Path

from mido import Message, MidiFile, MidiTrack, bpm2tempo, MetaMessage

from .melody_engine import generate_melody
from .bass_engine import bass_for_chords
from .drum_engine import drum_pattern


ROOT_NOTES_MID = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71}


def _chord_notes(chord_name: str) -> List[int]:
    root_char = chord_name[0].upper()
    is_minor = "m" in chord_name[1:]

    root = ROOT_NOTES_MID.get(root_char, 60)
    if is_minor:
        return [root, root + 3, root + 7]
    return [root, root + 4, root + 7]


def render_to_midi(structure, tempo_bpm: int, output_path: str, mood) -> str:
    mid = MidiFile()

    chords_track = MidiTrack()
    melody_track = MidiTrack()
    bass_track = MidiTrack()
    drums_track = MidiTrack()

    mid.tracks.append(chords_track)
    mid.tracks.append(melody_track)
    mid.tracks.append(bass_track)
    mid.tracks.append(drums_track)

    ticks_per_beat = mid.ticks_per_beat
    beat_ticks = ticks_per_beat
    bar_ticks = 4 * ticks_per_beat

    # tempo meta on first track
    chords_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo_bpm), time=0))

    # instruments (General MIDI)
    chords_track.append(Message("program_change", program=0, time=0))   # Piano
    melody_track.append(Message("program_change", program=73, time=0))  # Flute-ish
    bass_track.append(Message("program_change", program=33, time=0))    # Bass

    # drums are on channel 9 (0-indexed)
    DRUM_CH = 9

    # Flatten chords per bar for bass generation
    all_bar_chords: List[str] = []
    section_names: List[str] = []

    for sec in structure.sections:
        for ch in sec.chords:
            all_bar_chords.append(ch)
            section_names.append(sec.name)

    total_bars = len(all_bar_chords)

    # ---- CHORDS (one chord per bar) ----
    for bar_index, chord_name in enumerate(all_bar_chords):
        notes = _chord_notes(chord_name)

        # subtle section dynamics
        sec = section_names[bar_index]
        vel = 52
        if "Chorus" in sec:
            vel = 62

        for n in notes:
            chords_track.append(Message("note_on", note=n, velocity=vel, time=0))
        chords_track.append(Message("note_off", note=notes[0], velocity=0, time=bar_ticks))
        for n in notes[1:]:
            chords_track.append(Message("note_off", note=n, velocity=0, time=0))

    # ---- BASS (root per bar, plays on beats 1 and 3) ----
    bass_roots = bass_for_chords(all_bar_chords)
    for bar_index, root_note in enumerate(bass_roots):
        sec = section_names[bar_index]
        vel = 65 if "Chorus" in sec else 55

        # beat 1
        bass_track.append(Message("note_on", note=root_note, velocity=vel, time=0))
        bass_track.append(Message("note_off", note=root_note, velocity=0, time=beat_ticks))

        # beat 2 (rest)
        bass_track.append(Message("note_on", note=root_note, velocity=0, time=beat_ticks))
        bass_track.append(Message("note_off", note=root_note, velocity=0, time=0))

        # beat 3
        bass_track.append(Message("note_on", note=root_note, velocity=vel, time=0))
        bass_track.append(Message("note_off", note=root_note, velocity=0, time=beat_ticks))

        # beat 4 (rest)
        bass_track.append(Message("note_on", note=root_note, velocity=0, time=beat_ticks))
        bass_track.append(Message("note_off", note=root_note, velocity=0, time=0))

    # ---- MELODY (one note per beat, higher in chorus) ----
    first_root = ROOT_NOTES_MID.get(all_bar_chords[0][0].upper(), 60)
    melody_notes = generate_melody(first_root, mood, total_bars)

    for beat_index, note in enumerate(melody_notes):
        # identify section by bar
        bar_index = beat_index // 4
        sec = section_names[bar_index]

        # chorus lifts melody
        adj_note = note + (12 if "Chorus" in sec else 0)

        vel = 80 if "Chorus" in sec else 70
        melody_track.append(Message("note_on", note=adj_note, velocity=vel, time=0))
        melody_track.append(Message("note_off", note=adj_note, velocity=0, time=beat_ticks))

    # ---- DRUMS (kick/snare/hat) ----
    hits = drum_pattern(total_bars)
    # To keep timing simple: emit events in beat order with time deltas.
    last_beat = 0
    for drum_note, beat in hits:
        delta_beats = beat - last_beat
        drums_track.append(Message("note_on", channel=DRUM_CH, note=drum_note, velocity=70, time=delta_beats * beat_ticks))
        drums_track.append(Message("note_off", channel=DRUM_CH, note=drum_note, velocity=0, time=int(0.25 * beat_ticks)))
        last_beat = beat

    out_path = Path(output_path).with_suffix(".mid")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(out_path)
    return str(out_path)
