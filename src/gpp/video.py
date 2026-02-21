"""Video assembly: Ken Burns clips + crossfade transitions."""

import subprocess
import tempfile
from pathlib import Path

from .kenburns import get_zoompan_filter


def _run_ffmpeg(args: list[str], desc: str = "") -> None:
    """Run an ffmpeg command, raising on failure."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed{' (' + desc + ')' if desc else ''}: {result.stderr}")


def generate_clip(
    image_path: Path,
    output_path: Path,
    duration: float,
    fps: int,
) -> None:
    """Generate a single Ken Burns clip from an image."""
    zoompan = get_zoompan_filter(duration, fps)

    _run_ffmpeg([
        "-i", str(image_path),
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,"
               f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,"
               f"{zoompan},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-t", str(duration),
        str(output_path),
    ], desc=image_path.name)


def assemble_video(
    image_paths: list[Path],
    output_path: str,
    duration: float = 6.0,
    transition: float = 1.5,
    fps: int = 30,
    loop_friendly: bool = True,
) -> None:
    """Generate the final slideshow video with Ken Burns effects and crossfades.

    Creates individual clips per photo, then chains them with xfade transitions.
    If loop_friendly is True, appends the first photo again at the end with a crossfade.
    """
    if not image_paths:
        raise ValueError("No images provided")

    work_dir = Path(tempfile.mkdtemp(prefix="gpp_clips_"))

    # For loop-friendly output, add the first image again at the end
    images = list(image_paths)
    if loop_friendly and len(images) > 1:
        images.append(images[0])

    # Step 1: Generate individual clips
    clips = []
    total = len(images)
    for i, img in enumerate(images, 1):
        print(f"  [{i}/{total}] Rendering clip for {img.name}", flush=True)
        clip_path = work_dir / f"clip_{i:04d}.mp4"
        generate_clip(img, clip_path, duration, fps)
        clips.append(clip_path)

    if len(clips) == 1:
        # Single image, just copy
        _run_ffmpeg(["-i", str(clips[0]), "-c", "copy", output_path])
        return

    # Step 2: Chain clips with xfade transitions
    # Build a complex filtergraph chaining xfade between consecutive clips
    print("  Assembling final video with crossfades...", flush=True)

    inputs = []
    for clip in clips:
        inputs.extend(["-i", str(clip)])

    # Build xfade filter chain
    # Each xfade takes two streams and produces one. We chain them sequentially.
    filter_parts = []
    n = len(clips)

    # The offset for each xfade is: (clip_duration - transition) * clip_index
    # But accounting for how each xfade shortens the timeline
    # After k xfades, total duration = k*(duration - transition) + duration
    # So offset for xfade k (0-indexed) = (k+1)*duration - (k+1)*transition
    #   = (k+1)*(duration - transition)

    prev_label = "[0:v]"
    for i in range(1, n):
        offset = i * duration - i * transition
        if offset < 0:
            offset = 0
        out_label = f"[v{i}]" if i < n - 1 else "[vout]"
        filter_parts.append(
            f"{prev_label}[{i}:v]xfade=transition=fade:duration={transition}:offset={offset}{out_label}"
        )
        prev_label = out_label

    filtergraph = ";".join(filter_parts)

    _run_ffmpeg(
        inputs + [
            "-filter_complex", filtergraph,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            output_path,
        ],
        desc="final assembly",
    )

    print(f"  Video saved to {output_path}")
