from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.emotion_engine import analyze_mood
from core.theory_engine import plan_song
from core.structure_engine import build_structure
from core.midi_engine import render_to_midi
from core.spotify_engine import SpotifyClient, rank_tracks_popular_and_relevant


app = FastAPI()
templates = Jinja2Templates(directory="templates")
spotify = SpotifyClient()


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
    return FileResponse(path=midi_path, filename="meuphonic_song.mid", media_type="audio/midi")


@app.post("/spotify/moodtracks")
def spotify_moodtracks(description: str = Form(...), language: str = Form("en")):
    mood = analyze_mood(description)

    # language = artist / lyrics language
    lang_hint = {
        "fa": "persian",
        "tr": "turkish",
        "ar": "arabic",
        "fr": "french",
        "es": "spanish",
        "en": "",
    }.get(language, "")

    # Broad, popularity-friendly query
    query = f"{mood.label} {lang_hint} pop mood".strip()

    candidates = spotify.search_tracks(query, limit=50)

    ranked = rank_tracks_popular_and_relevant(
        description,
        candidates,
        min_popularity=55,
    )

    return JSONResponse({"tracks": [t.__dict__ for t in ranked[:10]]})
