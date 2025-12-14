from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.emotion_engine import analyze_mood
from core.theory_engine import plan_song
from core.structure_engine import build_structure
from core.midi_engine import render_to_midi

from core.spotify_engine import SpotifyClient, dedupe_tracks, rank_tracks_ai


app = FastAPI()
templates = Jinja2Templates(directory="templates")
spotify = SpotifyClient()


def lang_hint(language: str) -> str:
    # Artist/lyrics language hint (best-effort)
    return {
        "fa": "persian iranian",
        "tr": "turkish",
        "ar": "arabic",
        "fr": "french",
        "es": "spanish",
        "en": "",
    }.get(language, "")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
def generate(description: str = Form(...), genre: str = Form("pop")):
    mood = analyze_mood(description)
    plan = plan_song(mood, genre=genre)  # <-- we’ll update plan_song signature
    structure = build_structure(plan)

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "meuphonic_song.mid"

    midi_path = render_to_midi(structure, plan.tempo, str(out_path), mood, genre=genre)
    return FileResponse(path=midi_path, filename="meuphonic_song.mid", media_type="audio/midi")


@app.post("/spotify/artists")
def spotify_artists(description: str = Form(...), language: str = Form("en"), variant: int = Form(0)):
    mood = analyze_mood(description)
    hint = lang_hint(language)

    # Variant changes offset so results can differ meaningfully
    offset = (variant * 10) % 30

    query = f"{mood.label} {hint} pop".strip()
    artists = spotify.search_popular_artists(query=query, limit=5, min_popularity=60, offset=offset)

    return JSONResponse({"artists": [a.__dict__ for a in artists]})


@app.post("/spotify/tracks")
def spotify_tracks(description: str = Form(...), artist_id: str = Form(...)):
    mood = analyze_mood(description)

    artist_tracks = spotify.artist_top_tracks(artist_id, limit=10)
    year_tracks = spotify.top_songs_2025(limit_total=100)
    global_tracks = spotify.top_50_global(limit_total=50)

    candidates = dedupe_tracks(artist_tracks + year_tracks + global_tracks)
    ranked = rank_tracks_ai(description, candidates, mood_label=mood.label)

    return JSONResponse({"tracks": [t.__dict__ for t in ranked[:3]]})
