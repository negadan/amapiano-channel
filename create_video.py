#!/usr/bin/env python3
"""
Create professional Amapiano visualizer videos
Clean, simple, consistent - like real YouTube music channels
"""

import os
import subprocess
import sys
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CHANNEL_NAME

# Layout constants
TEXT_MARGIN = 60
VISUALIZER_HEIGHT = 150
FADE_DURATION = 2


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_video(
    audio_path: str,
    image_path: str,
    output_path: str,
    track_name: str = "",
    limit_duration: float = None
) -> bool:
    """
    Create a professional music visualizer video.

    Features:
    - Slow Ken Burns zoom on background
    - Spectrum bars at bottom
    - Vignette for cinematic look
    - Fade in/out
    - Clean text overlay (top-left)
    """

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        return False

    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False

    # Get duration
    audio_duration = get_audio_duration(audio_path)
    duration = limit_duration if limit_duration and limit_duration < audio_duration else audio_duration
    total_frames = int(duration * VIDEO_FPS)

    print(f"Creating professional video...")
    print(f"Duration: {duration:.1f}s | Frames: {total_frames}")

    # Escape text for ffmpeg
    safe_track = track_name.replace("'", "'\\''").replace(":", "\\:") if track_name else ""
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")

    # Build the filter chain
    # Step 1: Scale and zoom background with vignette
    bg_filter = (
        f"[1:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
        f"vignette=PI/4[bg]"
    )

    # Step 2: Audio spectrum bars (clean cyan/magenta gradient)
    bars_filter = (
        f"[0:a]showfreqs=s={VIDEO_WIDTH}x{VISUALIZER_HEIGHT}:"
        f"mode=bar:colors=cyan|magenta|white:"
        f"ascale=log:fscale=log:win_size=2048[bars]"
    )

    # Step 3: Overlay bars on background
    overlay_filter = f"[bg][bars]overlay=0:H-{VISUALIZER_HEIGHT}[combined]"

    # Step 4: Fade in/out
    fade_out_start = max(0, duration - FADE_DURATION)
    fade_filter = (
        f"[combined]fade=t=in:st=0:d={FADE_DURATION},"
        f"fade=t=out:st={fade_out_start}:d={FADE_DURATION}[faded]"
    )

    # Step 5: Text overlays
    text_filters = "[faded]"

    if track_name:
        # Track name - top left with outline
        text_filters += (
            f"drawtext=text='{safe_track}':"
            f"x={TEXT_MARGIN}:y={TEXT_MARGIN}:"
            f"fontsize=52:fontcolor=white:"
            f"borderw=3:bordercolor=black,"
        )

    # Channel watermark - bottom right
    text_filters += (
        f"drawtext=text='@{safe_channel}':"
        f"x=w-text_w-{TEXT_MARGIN}:y=h-{TEXT_MARGIN}:"
        f"fontsize=28:fontcolor=white@0.7:"
        f"borderw=2:bordercolor=black@0.5[v]"
    )

    # Combine all filters
    filter_complex = f"{bg_filter};{bars_filter};{overlay_filter};{fade_filter};{text_filters}"

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-loop", "1", "-i", image_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p"
    ]

    if limit_duration:
        cmd.extend(["-t", str(limit_duration)])

    cmd.append(output_path)

    print(f"Output: {output_path}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return False
        print("Video created successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_short(
    audio_path: str,
    image_path: str,
    output_path: str,
    track_name: str = "",
    start_time: float = 60,
    duration: float = 45
) -> bool:
    """Create a YouTube Short (vertical 9:16, 45-60 sec)"""

    safe_track = track_name.replace("'", "'\\''").replace(":", "\\:") if track_name else ""
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")
    total_frames = int(duration * VIDEO_FPS)

    filter_complex = (
        # Vertical format with zoom
        f"[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='1+0.0003*on':d={total_frames}:s=1080x1920:fps={VIDEO_FPS},"
        f"vignette=PI/4[bg];"
        # Spectrum bars
        f"[0:a]showfreqs=s=1080x120:mode=bar:colors=cyan|magenta:ascale=log[bars];"
        # Overlay
        f"[bg][bars]overlay=0:H-120[combined];"
        # Fade
        f"[combined]fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1[faded];"
        # Text
        f"[faded]drawtext=text='{safe_track}':x=40:y=100:fontsize=42:fontcolor=white:borderw=2:bordercolor=black,"
        f"drawtext=text='@{safe_channel}':x=w-text_w-40:y=h-80:fontsize=24:fontcolor=white@0.7:borderw=2:bordercolor=black@0.5[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", audio_path,
        "-loop", "1", "-i", image_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print(f"Creating YouTube Short...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return False
        print("Short created successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create professional Amapiano visualizer video")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file")
    parser.add_argument("--image", "-i", required=True, help="Path to background image")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--name", "-n", default="", help="Track name for overlay")
    parser.add_argument("--short", "-s", action="store_true", help="Create YouTube Short instead")
    parser.add_argument("--duration", "-d", type=float, help="Limit video duration in seconds")

    args = parser.parse_args()

    if args.short:
        success = create_short(args.audio, args.image, args.output, args.name)
    else:
        success = create_video(
            args.audio, args.image, args.output,
            track_name=args.name, limit_duration=args.duration
        )

    sys.exit(0 if success else 1)
