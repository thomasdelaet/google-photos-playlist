# Google Photos Playlist

Generate Ken Burns slideshow videos from Google Photos albums. Downloads photos from an album, applies randomized Ken Burns effects (zoom, pan), and assembles them into a video with crossfade transitions.

## Prerequisites

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/) installed and available on your PATH
- A Google Cloud project with the [Photos Library API](https://developers.google.com/photos/library/guides/get-started) enabled
- An OAuth 2.0 client secret JSON file downloaded from Google Cloud Console

## Installation

```bash
pip install .
```

## Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Photos Library API**
3. Create OAuth 2.0 credentials (Desktop application)
4. Download the client secret JSON and save it as `client_secret.json` in your working directory

## Usage

```bash
gpp <album-url-or-id> [options]
```

### Examples

```bash
# Basic usage with a shared album URL
gpp "https://photos.google.com/share/AF1Qip..."

# Custom output and timing
gpp "https://photos.google.com/share/AF1Qip..." -o slideshow.mp4 --duration 8 --transition 2

# Shuffle photo order
gpp "https://photos.google.com/share/AF1Qip..." --shuffle
```

### Options

| Option | Default | Description |
|---|---|---|
| `-o, --output` | `output.mp4` | Output video file path |
| `--duration` | `6.0` | Duration per photo in seconds |
| `--transition` | `1.5` | Crossfade transition duration in seconds |
| `--shuffle` | off | Randomize photo order |
| `--credentials` | `client_secret.json` | Path to OAuth client secret JSON |
| `--token` | `token.json` | Path to cached auth token |
| `--fps` | `30` | Frames per second |

## How it works

1. **Authenticate** with Google Photos via OAuth 2.0
2. **Fetch** all photo metadata from the specified album
3. **Download** photos at 1920x1080 resolution with EXIF orientation correction
4. **Render** each photo as a clip with a random Ken Burns effect (zoom in, zoom out, pan left/right)
5. **Assemble** clips into a final video with crossfade transitions

The output video loops seamlessly by appending the first photo at the end with a crossfade.

## License

See [LICENSE](LICENSE) for details.
