# MEuphonic — Mood → Music Engine

An AI-based music generator tool based on your mood !
MEuphonic generates music from natural-language emotion descriptions.

## What it does (current)
- Accepts a detailed mood/feeling description (text)
- Extracts a mood profile (valence/energy + label)
- Maps mood to musical decisions (tempo, mode, progression)
- Builds a song structure (intro/verse/chorus/bridge/outro)
- Produces a multi-track MIDI file (chords, melody, bass, drums)
- Optional: Web UI for generating MIDI in the browser

## Quick start (Windows / VS Code)
1) Create & activate venv:
```powershell
py -m venv .venv
. .\.venv\Scripts\Activate.ps1
