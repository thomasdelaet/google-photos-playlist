"""Ken Burns effect logic: zoom/pan motion presets for ffmpeg zoompan filter."""

import random


def get_zoompan_filter(
    duration: float,
    fps: int,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Generate an ffmpeg zoompan filter string for a Ken Burns effect.

    Randomly selects from several motion presets:
    - Zoom in to center
    - Zoom in to a rule-of-thirds point
    - Zoom out from center
    - Pan left-to-right with slight zoom
    - Pan right-to-left with slight zoom
    """
    total_frames = int(duration * fps)
    # Zoom range: start/end zoom factors
    # We use a modest zoom range (1.0 to 1.15) for subtle, pleasant motion
    zoom_amount = 0.15

    preset = random.choice(["zoom_in_center", "zoom_in_third", "zoom_out", "pan_lr", "pan_rl"])

    if preset == "zoom_in_center":
        # Slow zoom into center
        z_expr = f"1.0+{zoom_amount}*(in/{total_frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    elif preset == "zoom_in_third":
        # Zoom into a rule-of-thirds intersection
        tx = random.choice([1 / 3, 2 / 3])
        ty = random.choice([1 / 3, 2 / 3])
        z_expr = f"1.0+{zoom_amount}*(in/{total_frames})"
        x_expr = f"iw*{tx}-(iw/zoom/2)"
        y_expr = f"ih*{ty}-(ih/zoom/2)"

    elif preset == "zoom_out":
        # Start zoomed in, slowly zoom out
        z_expr = f"{1.0 + zoom_amount}-{zoom_amount}*(in/{total_frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    elif preset == "pan_lr":
        # Pan from left to right with slight zoom
        z_expr = f"1.0+0.05*(in/{total_frames})"
        # x pans from 0 to (iw - iw/zoom)
        x_expr = f"(iw-iw/zoom)*(in/{total_frames})"
        y_expr = "ih/2-(ih/zoom/2)"

    elif preset == "pan_rl":
        # Pan from right to left with slight zoom
        z_expr = f"1.0+0.05*(in/{total_frames})"
        x_expr = f"(iw-iw/zoom)*(1-in/{total_frames})"
        y_expr = "ih/2-(ih/zoom/2)"

    return (
        f"zoompan=z='{z_expr}'"
        f":x='{x_expr}'"
        f":y='{y_expr}'"
        f":d={total_frames}"
        f":s={width}x{height}"
        f":fps={fps}"
    )
