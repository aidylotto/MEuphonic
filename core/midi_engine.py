from typing import List, Optional, Tuple
from pathlib import Path

from mido import Message, MidiFile, MidiTrack, bpm2tempo, MetaMessage

from .style_engine import select_style
from .melody_engine import generate_melody
from .bass_engine import bass_for_chords
from .drum_engine import drum_hits
from .guitar_engine import arp_pattern, strum_pattern


ROOT_NOTES_MID = {"C": 60, "D": 62, "E": 64, "F": 65, "G": 67, "A": 69, "B": 71}

# General MIDI programs
GM_PIANO = 0
GM_FLUTE = 73
GM_BASS = 33
GM_EG_CLEAN = 27
GM_EG_OVERDRIVE = 29
GM_EG_DIST = 30


def _chord_notes(chord_name: str) -> List[int]:
    root_char = chord_name[0].upper()
    is_minor = "m" in chord_name[1:]
    root = ROOT_NOTES_MID.get(root_char, 60)
    if is_minor:
        return [root, root + 3, root + 7]
    return [root, root + 4, root + 7]


def _sec_velocity(section_name: str, base: int) -> int:
    if "Chorus" in section_name:
        return min(100, base + 12)
    if "Intro" in section_name or "Outro" in section_name:
        return max(35, base - 10)
    return base


def _beat_to_ticks(beat: float, ticks_per_beat: int) -> int:
    return int(round(beat * ticks_per_beat))


def render_to_midi(structure, tempo_bpm: int, output_path: str, mood) -> str:
    style = select_style(mood)

    mid = MidiFile()
    ticks_per_beat = mid.ticks_per_beat

    # Tracks
    chord_track = MidiTrack()
    melody_track = MidiTrack()
    bass_track = MidiTrack()
    drums_track = MidiTrack()
    guitar_track = MidiTrack()

    mid.tracks.append(chord_track)
    mid.tracks.append(melody_track)
    mid.tracks.append(bass_track)
    mid.tracks.append(drums_track)
    mid.tracks.append(guitar_track)

    # Tempo
    chord_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo_bpm), time=0))

    # Instruments
    chord_track.append(Message("program_change", program=GM_PIANO, time=0))
    melody_track.append(Message("program_change", program=GM_FLUTE, time=0))
    bass_track.append(Message("program_change", program=GM_BASS, time=0))

    if style.guitar == "clean":
        guitar_track.append(Message("program_change", program=GM_EG_CLEAN, time=0))
    elif style.guitar == "overdrive":
        guitar_track.append(Message("program_change", program=GM_EG_OVERDRIVE, time=0))
    elif style.guitar == "distortion":
        guitar_track.append(Message("program_change", program=GM_EG_DIST, time=0))
    else:
        # still set something; we will keep guitar silent if None
        guitar_track.append(Message("program_change", program=GM_EG_CLEAN, time=0))

    DRUM_CH = 9  # General MIDI drum channel

    # Flatten bars
    all_bar_chords: List[str] = []
    section_names: List[str] = []
    for sec in structure.sections:
        for ch in sec.chords:
            all_bar_chords.append(ch)
            section_names.append(sec.name)

    total_bars = len(all_bar_chords)

    # --- CHORDS: keep subtle + not constant (leave space for guitar) ---
    bar_ticks = 4 * ticks_per_beat
    for bar_i, chord_name in enumerate(all_bar_chords):
        sec = section_names[bar_i]
        notes = _chord_notes(chord_name)

        # quieter if guitar is present (avoid mush)
        base_vel = 48 if style.guitar else 58
        vel = _sec_velocity(sec, base_vel)

        for n in notes:
            chord_track.append(Message("note_on", note=n, velocity=vel, time=0))
        chord_track.append(Message("note_off", note=notes[0], velocity=0, time=bar_ticks))
        for n in notes[1:]:
            chord_track.append(Message("note_off", note=n, velocity=0, time=0))

    # --- GUITAR: rhythmic comping/arps (only if style says so) ---
    if style.guitar:
        # emit events using beat offsets within each bar (convert to ticks with deltas)
        last_tick = 0
        abs_tick = 0

        for bar_i, chord_name in enumerate(all_bar_chords):
            sec = section_names[bar_i]
            chord_notes = _chord_notes(chord_name)
            # guitar up an octave for clarity
            chord_notes = [n + 12 for n in chord_notes]

            if style.chord_style == "arp":
                events = arp_pattern(chord_notes)
            else:
                events = strum_pattern(chord_notes)

            vel = _sec_velocity(sec, 72)

            # section drop: no guitar in intro sometimes
            if "Intro" in sec and mood.energy < 0.6:
                abs_tick += bar_ticks
                continue

            for note, beat in events:
                event_tick = abs_tick + _beat_to_ticks(beat, ticks_per_beat)
                delta = event_tick - last_tick
                guitar_track.append(Message("note_on", note=note, velocity=vel, time=delta))
                guitar_track.append(Message("note_off", note=note, velocity=0, time=int(0.2 * ticks_per_beat)))
                last_tick = event_tick + int(0.2 * ticks_per_beat)

            abs_tick += bar_ticks

    # --- BASS: moving pattern per bar ---
    bass_bars = bass_for_chords(all_bar_chords, activity=style.bass_activity)
    last_tick = 0
    abs_tick = 0
    for bar_i, hits in enumerate(bass_bars):
        sec = section_names[bar_i]
        vel = _sec_velocity(sec, 70 if "Chorus" in sec else 62)

        for note, beat in hits:
            event_tick = abs_tick + _beat_to_ticks(beat, ticks_per_beat)
            delta = event_tick - last_tick
            bass_track.append(Message("note_on", note=note, velocity=vel, time=delta))
            bass_track.append(Message("note_off", note=note, velocity=0, time=int(0.35 * ticks_per_beat)))
            last_tick = event_tick + int(0.35 * ticks_per_beat)

        abs_tick += bar_ticks

    # --- MELODY: phrased + chorus lift ---
    first_root = ROOT_NOTES_MID.get(all_bar_chords[0][0].upper(), 60)
    melody = generate_melody(first_root, mood, total_bars, melody_density=style.melody_density)

    last_tick = 0
    abs_tick = 0
    for beat_i, note in enumerate(melody):
        bar_i = beat_i // 4
        sec = section_names[bar_i]

        # verse 1: intentionally sparser melody (more adult feel)
        if sec == "Verse 1" and mood.energy < 0.65 and (beat_i % 4 in (1, 3)):
            abs_tick += ticks_per_beat
            continue

        # rest
        if note is None:
            abs_tick += ticks_per_beat
            continue

        adj = style.chorus_lift if "Chorus" in sec else 0
        vel = _sec_velocity(sec, 78)

        delta = abs_tick - last_tick
        melody_track.append(Message("note_on", note=note + adj, velocity=vel, time=delta))
        melody_track.append(Message("note_off", note=note + adj, velocity=0, time=int(0.9 * ticks_per_beat)))
        last_tick = abs_tick + int(0.9 * ticks_per_beat)
        abs_tick += ticks_per_beat

    # --- DRUMS: section-aware (no full drums in intro/outro if calm/sad) ---
    hits = drum_hits(style.drums, total_bars)
    # We'll suppress drums in intro/outro for calmer moods
    def allowed(beat_pos: float) -> bool:
        bar_i = int(beat_pos) // 4
        sec = section_names[bar_i]
        if mood.label in ("sad", "romantic", "calm") and ("Intro" in sec or "Outro" in sec):
            return False
        return True

    last_tick = 0
    for note, beat_pos in hits:
        if not allowed(beat_pos):
            continue
        event_tick = _beat_to_ticks(beat_pos, ticks_per_beat)
        delta = event_tick - last_tick
        drums_track.append(Message("note_on", channel=DRUM_CH, note=note, velocity=78, time=delta))
        drums_track.append(Message("note_off", channel=DRUM_CH, note=note, velocity=0, time=int(0.12 * ticks_per_beat)))
        last_tick = event_tick + int(0.12 * ticks_per_beat)

    out_path = Path(output_path).with_suffix(".mid")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(out_path)
    return str(out_path)
