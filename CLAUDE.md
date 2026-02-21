# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CLI tool (`gpp`) that generates Ken Burns slideshow videos from Google Photos albums. Downloads photos, applies randomized Ken Burns effects (zoom/pan), and assembles them into a video with crossfade transitions using ffmpeg.

## Build & Run

```bash
pip install .                # Install the CLI
gpp <album-url> [options]    # Run it
```

No test suite or linter is configured.

**External dependency:** FFmpeg must be installed and on PATH.

**OAuth credentials:** Requires a Google Cloud OAuth `client_secret.json` for the Photos Library API. Tokens are cached in `token.json`.

## Architecture

The pipeline flows linearly through these modules in `src/gpp/`:

1. **cli.py** — Entry point (`main()`). Parses args, orchestrates the full pipeline.
2. **google_photos.py** — OAuth2 authentication (with token caching) and Google Photos Library API calls. Handles both shared album URLs (requires `sharedAlbums:join`) and direct album URLs/IDs. Uses the `photoslibrary` scope (not readonly) because joining shared albums is a write operation.
3. **downloader.py** — Downloads photos at 1920x1080 to a temp directory (`gpp_` prefix), fixes EXIF orientation with Pillow.
4. **kenburns.py** — Generates ffmpeg `zoompan` filter strings. Randomly picks from 5 presets: zoom-in-center, zoom-in-third, zoom-out, pan-left-right, pan-right-left.
5. **video.py** — Renders each photo as an individual clip with Ken Burns effect, then chains them together using ffmpeg `xfade` filters. Appends the first photo at the end for seamless looping by default.

## Key Details

- Shared album URLs (`photos.google.com/share/...`) extract a share token and call `sharedAlbums:join` to get the album ID. Direct album URLs (`photos.google.com/album/...`) use the album ID directly.
- Video encoding: libx264, CRF 20, medium preset, yuv420p. Images are padded to 1920x1080 with black bars.
- The ffmpeg filtergraph for multi-clip assembly chains xfade transitions with calculated time offsets — this is the most complex part of the codebase (`video.py:assemble_video`).
