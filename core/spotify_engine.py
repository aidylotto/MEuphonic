import os
import time
import base64
import requests
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MARKET = os.getenv("SPOTIFY_MARKET", "US")

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
    def __init__(self):
        self._token: Optional[str] = None
        self._expires: float = 0

    def _token_headers(self):
        if self._token and time.time() < self._expires:
            return {"Authorization": f"Bearer {self._token}"}

        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        r = requests.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._expires = time.time() + data["expires_in"] - 30
        return {"Authorization": f"Bearer {self._token}"}

    def _get(self, path, params=None):
        r = requests.get(
            API_BASE + path,
            headers=self._token_headers(),
            params=params,
            timeout=15
        )
        r.raise_for_status()
        return r.json()

    # ---------- ARTISTS ----------

    def popular_artists_by_genre(self, genre: str, limit=5, offset=0) -> List[SpotifyArtist]:
        data = self._get(
            "/search",
            {
                "q": f"genre:{genre}",
                "type": "artist",
                "limit": limit,
                "offset": offset,
                "market": MARKET
            }
        )

        items = data.get("artists", {}).get("items", [])
        items.sort(key=lambda a: a.get("popularity", 0), reverse=True)

        return [
            SpotifyArtist(
                id=a["id"],
                name=a["name"],
                url=a["external_urls"]["spotify"],
                popularity=a["popularity"]
            )
            for a in items
        ]

    # ---------- TRACKS ----------

    def recommend_tracks(
        self,
        seed_artists: List[str],
        mood_energy: float,
        limit=10
    ) -> List[SpotifyTrack]:

        params = {
            "seed_artists": ",".join(seed_artists[:5]),
            "limit": limit,
            "market": MARKET,
            "target_energy": min(1.0, max(0.1, mood_energy)),
            "target_valence": min(1.0, max(0.1, mood_energy))
        }

        data = self._get("/recommendations", params)

        tracks = []
        for t in data.get("tracks", []):
            tracks.append(
                SpotifyTrack(
                    id=t["id"],
                    name=t["name"],
                    artist=t["artists"][0]["name"],
                    url=t["external_urls"]["spotify"],
                    popularity=t["popularity"]
                )
            )

        return tracks
