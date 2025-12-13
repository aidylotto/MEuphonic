import os
import time
import base64
import requests
import re
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv

# ---- ENV --------------------------------------------------------------------

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "US")

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

# ---- DATA MODELS ------------------------------------------------------------

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


# ---- SPOTIFY CLIENT ----------------------------------------------------------

class SpotifyClient:
    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ---- AUTH ---------------------------------------------------------------

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 30:
            return self._token

        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env")

        auth = base64.b64encode(
            f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()

        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}

        r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=20)
        r.raise_for_status()

        payload = r.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600)
        return self._token

    # ---- HTTP ---------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    # ---- SEARCH -------------------------------------------------------------

    def search_artists(self, query: str, limit: int = 5) -> List[SpotifyArtist]:
        params = {"q": query, "type": "artist", "limit": limit}
        data = self._get("/search", params=params)

        artists: List[SpotifyArtist] = []
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
        data = self._get(
            f"/artists/{artist_id}/top-tracks",
            params={"market": SPOTIFY_MARKET},
        )

        tracks: List[SpotifyTrack] = []
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

    def search_tracks(self, query: str, limit: int = 50) -> List[SpotifyTrack]:
        params = {"q": query, "type": "track", "limit": limit}
        data = self._get("/search", params=params)

        tracks: List[SpotifyTrack] = []
        for t in data.get("tracks", {}).get("items", []):
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


# ---- RANKING / UTILITIES -----------------------------------------------------

def rank_tracks_popular_and_relevant(
    description: str,
    tracks: List[SpotifyTrack],
    min_popularity: int = 55,
) -> List[SpotifyTrack]:
    """
    Rank tracks by mood relevance + popularity.
    Designed to surface popular but emotionally relevant songs.
    """
    text = description.lower()
    keywords = set(re.findall(r"[a-z]{4,}", text))

    def text_overlap(t: SpotifyTrack) -> float:
        hay = f"{t.name} {t.artist}".lower()
        return sum(1 for w in keywords if w in hay)

    def score(t: SpotifyTrack) -> float:
        relevance = min(1.0, text_overlap(t) / 4.0)
        popularity = t.popularity / 100.0
        return (0.60 * relevance) + (0.40 * popularity)

    filtered = [t for t in tracks if t.popularity >= min_popularity]
    return sorted(filtered, key=score, reverse=True)
