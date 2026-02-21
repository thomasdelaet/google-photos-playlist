"""CLI entry point for google-photos-playlist."""

import argparse
import random
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="gpp",
        description="Generate a Ken Burns slideshow video from a Google Photos album",
    )
    parser.add_argument(
        "album",
        help="Google Photos album URL or album ID",
    )
    parser.add_argument(
        "-o", "--output",
        default="output.mp4",
        help="Output video file path (default: output.mp4)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=6.0,
        help="Duration per photo in seconds (default: 6)",
    )
    parser.add_argument(
        "--transition",
        type=float,
        default=1.5,
        help="Crossfade transition duration in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Randomize photo order",
    )
    parser.add_argument(
        "--credentials",
        default="client_secret.json",
        help="Path to OAuth client_secret JSON (default: client_secret.json)",
    )
    parser.add_argument(
        "--token",
        default="token.json",
        help="Path to cached token (default: token.json)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second (default: 30)",
    )

    args = parser.parse_args()

    if args.transition >= args.duration:
        print(f"Error: transition ({args.transition}s) must be less than duration ({args.duration}s)")
        sys.exit(1)

    # Import here to avoid slow imports when just showing --help
    from .google_photos import authenticate, fetch_album_photos
    from .downloader import download_photos
    from .video import assemble_video

    # Step 1: Authenticate
    print("Authenticating with Google Photos...")
    try:
        creds = authenticate(args.credentials, args.token)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # Step 2: Fetch album photos
    print("Fetching album photos...")
    try:
        photos = fetch_album_photos(creds, args.album)
    except Exception as e:
        print(f"Failed to fetch album: {e}")
        sys.exit(1)

    if not photos:
        print("Error: album contains no photos")
        sys.exit(1)

    print(f"Found {len(photos)} photos")

    if args.shuffle:
        random.shuffle(photos)

    # Step 3: Download photos
    print("Downloading photos...")
    try:
        image_paths = download_photos(photos)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

    # Step 4: Generate video
    print("Generating video...")
    try:
        assemble_video(
            image_paths,
            args.output,
            duration=args.duration,
            transition=args.transition,
            fps=args.fps,
        )
    except RuntimeError as e:
        print(f"Video generation failed: {e}")
        sys.exit(1)

    print(f"Done! Output: {args.output}")


if __name__ == "__main__":
    main()
