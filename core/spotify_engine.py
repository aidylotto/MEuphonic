import os
import time
import base64
import requests
from dataclasses import dataclass
from typing import List, Dict, Optional
from dotenv import load_dotenv

import re
from typing import List
from .emotion_engine import MoodProfile  # if this creates circular import, remove and use typing.Any


load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "US")

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


@dataclass
class SpotifyArtist:
    id: str
    name: str
    url: str
    popularity: int


@dataclass
class SpotifyTrack:
    id: str
    name: str
    artist: str
    url: str
    popularity: int


class SpotifyClient:
    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env")

        auth = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}

        r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=20)
        r.raise_for_status()
        payload = r.json()

        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600)
        return self._token

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def search_artists(self, mood_query: str, limit: int = 5) -> List[SpotifyArtist]:
        # Using Search endpoint :contentReference[oaicite:3]{index=3}
        params = {"q": mood_query, "type": "artist", "limit": limit}
        data = self._get("/search", params=params)

        artists = []
        for a in data.get("artists", {}).get("items", []):
            artists.append(
                SpotifyArtist(
                    id=a["id"],
                    name=a["name"],
                    url=a["external_urls"]["spotify"],
                    popularity=a.get("popularity", 0),
                )
            )
        return artists

    def artist_top_tracks(self, artist_id: str, limit: int = 10) -> List[SpotifyTrack]:
        # Get Artist's Top Tracks endpoint :contentReference[oaicite:4]{index=4}
        data = self._get(f"/artists/{artist_id}/top-tracks", params={"market": SPOTIFY_MARKET})
        tracks = []
        for t in data.get("tracks", [])[:limit]:
            tracks.append(
                SpotifyTrack(
                    id=t["id"],
                    name=t["name"],
                    artist=t["artists"][0]["name"],
                    url=t["external_urls"]["spotify"],
                    popularity=t.get("popularity", 0),
                )
            )
        return tracks

import re
from typing import List

from .emotion_engine import MoodProfile


def build_mood_query(description: str, mood: MoodProfile) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", description.lower())
    tokens = [t for t in text.split() if len(t) >= 4]
    top = tokens[:6]
    # Include mood label to steer artist search
    return f'{mood.label} {" ".join(top)}'.strip()


def rank_tracks_by_mood_text(description: str, tracks: List) -> List:
    """
    tracks: List of SpotifyTrack objects (defined in this module).
    We avoid importing SpotifyTrack here to prevent circular imports.
    """
    text = description.lower()
    keywords = set(re.findall(r"[a-z]{4,}", text))

    def score(t) -> float:
        hay = f"{t.name} {t.artist}".lower()
        overlap = sum(1 for w in keywords if w in hay)
        return (overlap * 10.0) + (t.popularity * 0.05)

    return sorted(tracks, key=score, reverse=True)
