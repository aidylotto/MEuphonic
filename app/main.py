from pathlib import Path

from core.emotion_engine import analyze_mood
from core.theory_engine import plan_song
from core.structure_engine import build_structure
from core.midi_engine import render_to_midi


def main():
    print("=== MEuphonic: Mood → Music Generator (MIDI MVP) ===\n")
    description = input("Describe your mood or feeling in detail:\n> ")

    print("\n[1] Analyzing mood...")
    mood = analyze_mood(description)
    print(f"  -> Detected mood label: {mood.label}")
    print(f"  -> Tempo: {mood.tempo} BPM, Mode: {mood.mode}, Energy: {mood.energy:.2f}")

    print("\n[2] Planning song...")
    plan = plan_song(mood)
    print(f"  -> Key: {plan.key} {plan.scale_mode}")
    print(f"  -> Base progression: {' - '.join(plan.chord_progression)}")

    print("\n[3] Building structure...")
    structure = build_structure(plan)
    for sec in structure.sections:
        print(f"  -> {sec.name}: {sec.bars} bars")

    print("\n[4] Rendering to MIDI...")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "meuphonic_song.mid"

    midi_path = render_to_midi(structure, plan.tempo, str(output_path), mood)
    print(f"\nDone! MIDI file saved at: {midi_path}")
    print("\nOpen it in a DAW (FL Studio/Ableton/LMMS) or any MIDI player.")


if __name__ == "__main__":
    main()
