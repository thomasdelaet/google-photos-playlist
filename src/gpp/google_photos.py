"""Google Photos API integration: OAuth and album photo fetching."""

import re
from pathlib import Path
from typing import Optional

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
API_BASE = "https://photoslibrary.googleapis.com/v1"


def authenticate(credentials_path: str, token_path: str) -> Credentials:
    """Authenticate with Google Photos API, caching tokens for reuse."""
    creds = None
    token_file = Path(token_path)

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(credentials_path).exists():
                raise FileNotFoundError(
                    f"OAuth client secret file not found: {credentials_path}\n"
                    "Download it from Google Cloud Console > APIs & Services > Credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json())

    return creds


def parse_album_id(album_url_or_id: str) -> "tuple[Optional[str], Optional[str]]":
    """Parse a Google Photos album URL or raw ID.

    Returns (album_id, share_token) - one will be set depending on URL type.
    """
    # Shared album URL: https://photos.google.com/share/AF1Qip...
    m = re.match(r"https?://photos\.google\.com/share/([A-Za-z0-9_-]+)", album_url_or_id)
    if m:
        return None, m.group(1)

    # Direct album URL: https://photos.google.com/album/AF1Qip...
    m = re.match(r"https?://photos\.google\.com/album/([A-Za-z0-9_-]+)", album_url_or_id)
    if m:
        return m.group(1), None

    # Assume raw album ID
    if not album_url_or_id.startswith("http"):
        return album_url_or_id, None

    raise ValueError(f"Cannot parse album URL: {album_url_or_id}")


def _headers(creds: Credentials) -> dict:
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}


def _join_shared_album(creds: Credentials, share_token: str) -> str:
    """Join a shared album and return its album ID."""
    resp = requests.post(
        f"{API_BASE}/sharedAlbums:join",
        headers=_headers(creds),
        json={"shareToken": share_token},
    )
    resp.raise_for_status()
    return resp.json()["album"]["id"]


def fetch_album_photos(creds: Credentials, album_url_or_id: str) -> list[dict]:
    """Fetch all photo metadata from an album.

    Returns list of dicts with keys: id, baseUrl, width, height, filename.
    """
    album_id, share_token = parse_album_id(album_url_or_id)

    if share_token:
        album_id = _join_shared_album(creds, share_token)

    photos = []
    page_token = None

    while True:
        body = {"albumId": album_id, "pageSize": 100}
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(
            f"{API_BASE}/mediaItems:search",
            headers=_headers(creds),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("mediaItems", []):
            meta = item.get("mediaMetadata", {})
            if "photo" not in meta:
                continue  # Skip videos
            photos.append({
                "id": item["id"],
                "baseUrl": item["baseUrl"],
                "width": int(meta.get("width", 0)),
                "height": int(meta.get("height", 0)),
                "filename": item.get("filename", "unknown.jpg"),
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return photos
