from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pathlib import Path

from core.spotify_engine import SpotifyClient

from core.emotion_engine import analyze_mood
from core.theory_engine import plan_song
from core.structure_engine import build_structure
from core.midi_engine import render_to_midi

app = FastAPI()
templates = Jinja2Templates(directory="templates")
spotify = SpotifyClient()


@app.post("/spotify/artists")
def spotify_artists(description: str = Form(...)):
    # simple query construction: mood words + context terms
    mood_query = f"{description}"
    artists = spotify.search_artists(mood_query, limit=5)
    return {"artists": [a.__dict__ for a in artists]}


@app.post("/spotify/tracks")
def spotify_tracks(artist_id: str = Form(...)):
    tracks = spotify.artist_top_tracks(artist_id, limit=10)
    # We'll return 10 and let UI show top 3 first
    return {"tracks": [t.__dict__ for t in tracks]}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
def generate(description: str = Form(...)):
    mood = analyze_mood(description)
    plan = plan_song(mood)
    structure = build_structure(plan)

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "meuphonic_song.mid"

    midi_path = render_to_midi(structure, plan.tempo, str(out_path), mood)
    return FileResponse(
        path=midi_path,
        filename="meuphonic_song.mid",
        media_type="audio/midi",
    )
