from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.ai_music_brain import analyze_text_to_music
from core.midi_engine import render_to_midi
from core.spotify_engine import SpotifyClient

print("WEB APP LOADED")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
spotify = SpotifyClient()

GENRE_MAP = {
    "rock": "rock",
    "metal": "metal",
    "jazz": "jazz",
    "pop": "pop",
    "ambient": "ambient",
    "classical": "classical",
}


# ---------------- HOME ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------- MIDI GENERATION ----------------

@app.post("/generate")
def generate(description: str = Form(...)):
    print("GENERATE:", description[:80])

    profile = analyze_text_to_music(description)

    out_path = Path("outputs/meuphonic.mid")
    out_path.parent.mkdir(exist_ok=True)

    midi_path = render_to_midi(profile, str(out_path))

    return FileResponse(
        midi_path,
        filename="meuphonic.mid",
        media_type="audio/midi"
    )


# ---------------- SPOTIFY: ARTISTS FIRST ----------------

@app.post("/spotify/artists")
def spotify_artists(description: str = Form(...), variant: int = Form(0)):
    print("SPOTIFY ARTISTS:", description[:80], "variant:", variant)

    profile = analyze_text_to_music(description)
    genre = GENRE_MAP.get(profile.genre, "pop")

    artists = spotify.popular_artists_by_genre(
        genre=genre,
        limit=5,
        offset=(variant % 3) * 5
    )

    return JSONResponse({
        "artists": [a.__dict__ for a in artists]
    })


# ---------------- SPOTIFY: TRACKS FROM CHOSEN ARTIST ----------------

@app.post("/spotify/tracks")
def spotify_tracks(description: str = Form(...), artist_id: str = Form(...)):
    print("SPOTIFY TRACKS:", artist_id)

    profile = analyze_text_to_music(description)

    tracks = spotify.recommend_tracks(
        seed_artists=[artist_id],
        mood_energy=profile.energy,
        limit=10
    )

    return JSONResponse({
        "tracks": [t.__dict__ for t in tracks]
    })
