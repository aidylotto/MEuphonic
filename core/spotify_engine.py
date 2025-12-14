import os
import time
import base64
import requests
import re
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "US")

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

TOP_SONGS_2025_PLAYLIST_ID = os.getenv("SPOTIFY_TOP_SONGS_YEAR_ID", "37i9dQZEVXd4EBHBQ1yVHj")
TOP_50_GLOBAL_PLAYLIST_ID = os.getenv("SPOTIFY_TOP_50_GLOBAL_ID", "37i9dQZEVXbMDoHDwVN2tF")


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

    def _request_get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """
        Robust GET:
          - refresh token on 401
          - backoff on 429 using Retry-After (seconds)
        """
        for attempt in range(5):
            token = self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            r = requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=20)

            # Rate limit
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", "1"))
                time.sleep(max(1, retry_after))
                continue

            # Token expired/invalid -> refresh once
            if r.status_code == 401:
                self._token = None
                self._token_expires_at = 0.0
                continue

            r.raise_for_status()
            return r.json()

        raise RuntimeError("Spotify API request failed after retries (rate limit / auth)")

    # ----- ARTISTS -----

    def search_artists(self, query: str, limit: int = 20, offset: int = 0) -> List[SpotifyArtist]:
        data = self._request_get("/search", params={"q": query, "type": "artist", "limit": limit, "offset": offset})
        out: List[SpotifyArtist] = []
        for a in data.get("artists", {}).get("items", []):
            out.append(
                SpotifyArtist(
                    id=a["id"],
                    name=a["name"],
                    url=a["external_urls"]["spotify"],
                    popularity=a.get("popularity", 0),
                )
            )
        return out

    def search_popular_artists(self, query: str, limit: int = 5, min_popularity: int = 60, offset: int = 0) -> List[SpotifyArtist]:
        raw = self.search_artists(query=query, limit=30, offset=offset)
        filtered = [a for a in raw if a.popularity >= min_popularity]
        filtered.sort(key=lambda x: x.popularity, reverse=True)
        return filtered[:limit]

    # ----- TRACKS -----

    def artist_top_tracks(self, artist_id: str, limit: int = 10) -> List[SpotifyTrack]:
        data = self._request_get(f"/artists/{artist_id}/top-tracks", params={"market": SPOTIFY_MARKET})
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

    def _get_several_tracks(self, ids: List[str]) -> Dict[str, int]:
        """
        Get Several Tracks returns popularity 0..100. :contentReference[oaicite:7]{index=7}
        """
        pop: Dict[str, int] = {}
        # API supports up to 50 ids per call
        for i in range(0, len(ids), 50):
            chunk = ids[i : i + 50]
            data = self._request_get("/tracks", params={"ids": ",".join(chunk), "market": SPOTIFY_MARKET})
            for t in data.get("tracks", []) or []:
                if t and t.get("id"):
                    pop[t["id"]] = int(t.get("popularity") or 0)
        return pop

    def playlist_tracks(self, playlist_id: str, limit_total: int = 100) -> List[SpotifyTrack]:
        """
        Playlist items endpoint: max limit is 50; paginate using offset. :contentReference[oaicite:8]{index=8}
        """
        items: List[SpotifyTrack] = []
        offset = 0
        while len(items) < limit_total:
            page_limit = min(50, limit_total - len(items))
            data = self._request_get(
                f"/playlists/{playlist_id}/tracks",
                params={"limit": page_limit, "offset": offset, "market": SPOTIFY_MARKET},
            )
            raw_items = data.get("items", [])
            if not raw_items:
                break

            for it in raw_items:
                t = (it or {}).get("track")
                if not t or not t.get("id"):
                    continue
                items.append(
                    SpotifyTrack(
                        id=t["id"],
                        name=t["name"],
                        artist=(t.get("artists") or [{}])[0].get("name", "Unknown"),
                        url=t.get("external_urls", {}).get("spotify", ""),
                        popularity=int(t.get("popularity") or 0),  # may be 0/absent
                    )
                )

            offset += len(raw_items)
            if len(raw_items) < page_limit:
                break

        # Fill missing popularity via batch call (more reliable)
        need = [t.id for t in items if t.popularity == 0]
        if need:
            pops = self._get_several_tracks(need)
            for t in items:
                if t.popularity == 0 and t.id in pops:
                    t.popularity = pops[t.id]

        return items

    def top_songs_2025(self, limit_total: int = 100) -> List[SpotifyTrack]:
        return self.playlist_tracks(TOP_SONGS_2025_PLAYLIST_ID, limit_total=limit_total)

    def top_50_global(self, limit_total: int = 50) -> List[SpotifyTrack]:
        return self.playlist_tracks(TOP_50_GLOBAL_PLAYLIST_ID, limit_total=limit_total)


def dedupe_tracks(tracks: List[SpotifyTrack]) -> List[SpotifyTrack]:
    seen = set()
    out = []
    for t in tracks:
        if t.id in seen:
            continue
        seen.add(t.id)
        out.append(t)
    return out


def rank_tracks_ai(description: str, tracks: List[SpotifyTrack], mood_label: str) -> List[SpotifyTrack]:
    """
    Lightweight “AI-ish” ranker:
      - relevance via normalized keyword overlap (description + mood)
      - popularity bias (strong)
    Deterministic and fast; improves noticeably over raw search.
    """
    desc = (description or "").lower()
    desc = re.sub(r"[^a-z0-9\s]", " ", desc)
    desc = re.sub(r"\s+", " ", desc).strip()

    words = set([w for w in desc.split() if len(w) >= 4])
    if mood_label:
        words.add(mood_label.lower())

    def rel_score(t: SpotifyTrack) -> float:
        hay = f"{t.name} {t.artist}".lower()
        return sum(1.0 for w in words if w in hay)

    def score(t: SpotifyTrack) -> float:
        rel = rel_score(t)
        pop = (t.popularity or 0) / 100.0
        return (rel * 1.2) + (pop * 2.0)

    return sorted(tracks, key=score, reverse=True)
