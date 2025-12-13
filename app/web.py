from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.emotion_engine import analyze_mood
from core.theory_engine import plan_song
from core.structure_engine import build_structure
from core.midi_engine import render_to_midi
from core.spotify_engine import SpotifyClient


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
    """
    Return popular + mood-relevant tracks.
    Strategy:
      - Broad query for popularity
      - Filter low popularity
      - Re-rank by mood keyword overlap + popularity
    """
    mood = analyze_mood(description)

    lang_hint = {
        "en": "",
        "fa": "persian",
        "tr": "turkish",
        "ar": "arabic",
        "fr": "french",
        "es": "spanish",
    }.get(language, "")

    # broad, popularity-friendly query; avoid overly niche phrases
    # Example: "sad persian mood" or "happy spanish mood"
    query = f"{mood.label} {lang_hint} mood".strip()

    candidates = spotify.search_tracks(query, limit=50)

    def rank_tracks_popular_and_relevant(desc: str, tracks, min_popularity: int = 55):
        import re
        keywords = set(re.findall(r"[a-zA-Z]{4,}", desc.lower()))

        def overlap_score(t) -> float:
            hay = f"{t.name} {t.artist}".lower()
            return sum(1 for w in keywords if w in hay)

        def score(t) -> float:
            rel = min(1.0, overlap_score(t) / 4.0)        # 0..1
            pop = t.popularity / 100.0                    # 0..1
            return (0.60 * rel) + (0.40 * pop)            # bias popular but still relevant

        filtered = [t for t in tracks if t.popularity >= min_popularity]
        ranked = sorted(filtered, key=score, reverse=True)
        return ranked

    ranked = rank_tracks_popular_and_relevant(description, candidates, min_popularity=55)

    # Return top 10 so UI can show more than 3
    return JSONResponse({"tracks": [t.__dict__ for t in ranked[:10]]})
