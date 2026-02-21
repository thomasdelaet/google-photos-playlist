"""Download photos from Google Photos and fix orientation."""

import tempfile
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, ImageOps


def download_photos(photos: list, output_dir: "Optional[Path]" = None) -> "list[Path]":
    """Download photos to a directory, fixing EXIF orientation.

    Uses Google Photos URL parameters to request 1920x1080-fitting images.
    Returns list of paths to downloaded images.
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="gpp_"))
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    total = len(photos)

    for i, photo in enumerate(photos, 1):
        url = f"{photo['baseUrl']}=w1920-h1080"
        ext = Path(photo["filename"]).suffix or ".jpg"
        dest = output_dir / f"{i:04d}{ext}"

        print(f"  [{i}/{total}] {photo['filename']}", end="", flush=True)

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)

        # Fix EXIF orientation
        try:
            img = Image.open(dest)
            img = ImageOps.exif_transpose(img)
            img.save(dest)
        except Exception:
            pass  # Keep original if orientation fix fails

        print(" ok")
        paths.append(dest)

    return paths
