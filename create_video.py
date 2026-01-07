#!/usr/bin/env python3
"""
Create professional Amapiano visualizer videos
Clean spectrum bars + sparkles + Ken Burns zoom
"""

import os
import subprocess
import sys
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CHANNEL_NAME

# Layout constants
TEXT_MARGIN = 60
FADE_DURATION = 2
VISUALIZER_HEIGHT = 180


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
    Create a professional music visualizer with:
    - Ken Burns slow zoom
    - Glowing spectrum bars at bottom
    - Sparkle particles
    - Cinematic vignette
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

    print(f"Creating video with spectrum bars + sparkles...")
    print(f"Duration: {duration:.1f}s | Frames: {total_frames}")

    # Escape text
    safe_track = track_name.replace("'", "'\\''").replace(":", "\\:") if track_name else ""
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")

    # Build the filter complex
    filter_parts = []

    # 1. Background with Ken Burns zoom + vignette
    filter_parts.append(
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan=z='1+0.00015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
        f"vignette=PI/5[bg]"
    )

    # 2. Spectrum bars with glow (warm colors to match sunset)
    filter_parts.append(
        f"[1:a]showfreqs=s={VIDEO_WIDTH}x{VISUALIZER_HEIGHT}:"
        f"mode=bar:ascale=sqrt:fscale=log:"
        f"colors=0xFFAA00|0xFF6600|0xFF3300:"
        f"win_size=1024[bars_raw]"
    )

    # Add glow to bars
    filter_parts.append(
        f"[bars_raw]split[b1][b2];"
        f"[b1]gblur=sigma=8[bars_blur];"
        f"[bars_blur][b2]blend=all_mode=screen:all_opacity=0.9[bars_glow]"
    )

    # 3. Create sparkles/particles from audio
    # Use showwaves to create subtle particle movement synced to audio
    filter_parts.append(
        f"[1:a]showwaves=s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
        f"mode=p2p:colors=white@0.3:"
        f"scale=sqrt:rate={VIDEO_FPS}[waves_raw];"
        f"[waves_raw]gblur=sigma=2[sparkles]"
    )

    # 4. Composite layers
    # Background + sparkles (subtle)
    filter_parts.append(
        f"[bg][sparkles]blend=all_mode=screen:all_opacity=0.15[bg_sparkle]"
    )

    # Add spectrum bars at bottom with gradient fade
    filter_parts.append(
        f"[bars_glow]format=rgba,"
        f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
        f"a='alpha(X,Y)*min(1,(H-Y)/{VISUALIZER_HEIGHT}*1.5)'[bars_fade];"
        f"[bg_sparkle][bars_fade]overlay=0:H-{VISUALIZER_HEIGHT}:format=auto[with_bars]"
    )

    # 5. Final touches: fade in/out
    fade_out_start = max(0, duration - FADE_DURATION)
    filter_parts.append(
        f"[with_bars]fade=t=in:st=0:d={FADE_DURATION},"
        f"fade=t=out:st={fade_out_start}:d={FADE_DURATION}[faded]"
    )

    # 6. Text overlays
    text_filter = "[faded]"
    if track_name:
        text_filter += (
            f"drawtext=text='{safe_track}':"
            f"x={TEXT_MARGIN}:y={TEXT_MARGIN}:"
            f"fontsize=52:fontcolor=white:"
            f"borderw=3:bordercolor=black@0.7,"
        )

    text_filter += (
        f"drawtext=text='@{safe_channel}':"
        f"x=w-text_w-{TEXT_MARGIN}:y=h-{TEXT_MARGIN}-{VISUALIZER_HEIGHT}:"
        f"fontsize=26:fontcolor=white@0.8:"
        f"borderw=2:bordercolor=black@0.5[v]"
    )
    filter_parts.append(text_filter)

    # Combine all filter parts
    filter_complex = ";".join(filter_parts)

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create professional Amapiano visualizer")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file")
    parser.add_argument("--image", "-i", required=True, help="Path to background image")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--name", "-n", default="", help="Track name for overlay")
    parser.add_argument("--duration", "-d", type=float, help="Limit video duration in seconds")

    args = parser.parse_args()

    success = create_video(
        args.audio, args.image, args.output,
        track_name=args.name, limit_duration=args.duration
    )

    sys.exit(0 if success else 1)
