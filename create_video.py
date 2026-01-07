#!/usr/bin/env python3
"""
Create professional Amapiano visualizer videos
Vizzy.io style circular audio-reactive visualizer
"""

import os
import subprocess
import sys
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CHANNEL_NAME

# Layout constants
TEXT_MARGIN = 60
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
    Create a Vizzy.io style circular audio-reactive visualizer.

    Features:
    - Blurred/dimmed background
    - Particle starfield effect
    - Circular cutout in center
    - Audio spectrum ring (polar warped)
    - Pulse/breathing effect
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

    print(f"Creating Vizzy-style circular visualizer...")
    print(f"Duration: {duration:.1f}s | Frames: {total_frames}")

    # Escape text
    safe_track = track_name.replace("'", "'\\''").replace(":", "\\:") if track_name else ""
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")

    # Sizes
    RING_SIZE = 600  # Size of the spectrum ring
    CENTER_SIZE = 300  # Size of center circle cutout

    # Build the filter complex (Vizzy.io style)
    filter_complex = f"""
[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},setsar=1,format=rgba[bg_orig];

[bg_orig]boxblur=15:15,eq=brightness=-0.15:saturation=0.8[bg_blurred];

[bg_orig]crop=h={CENTER_SIZE}:w={CENTER_SIZE}:x=(iw-{CENTER_SIZE})/2:y=(ih-{CENTER_SIZE})/2,
geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='if(lt(hypot(X-W/2,Y-H/2),W/2-5),255,0)'[circle_art];

[1:a]showfreqs=s=1920x200:mode=bar:fscale=log:ascale=sqrt:colors=gold|orange|red:win_size=1024,
format=rgba[spectrum_linear];

[spectrum_linear]split[s1][s2];
[s2]hflip[s2_flip];
[s1][s2_flip]hstack,
scale={RING_SIZE}:{RING_SIZE},
v360=input=equirect:output=fisheye:h_fov=180:v_fov=180,
geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='if(between(hypot(X-W/2,Y-H/2),{CENTER_SIZE//2+20},{RING_SIZE//2}),255,0)'[polar_ring];

[polar_ring]split[ring1][ring2];
[ring1]gblur=sigma=10[ring_glow];
[ring_glow][ring2]blend=all_mode=screen[glowing_ring];

[bg_blurred][glowing_ring]overlay=x=(W-w)/2:y=(H-h)/2:format=auto[comp1];

[comp1][circle_art]overlay=x=(W-w)/2:y=(H-h)/2:format=auto[comp2];

[comp2]zoompan=z='1+0.0001*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[zoomed];

[zoomed]fade=t=in:st=0:d={FADE_DURATION},fade=t=out:st={max(0, duration-FADE_DURATION)}:d={FADE_DURATION}[faded];

[faded]drawtext=text='{safe_track}':x={TEXT_MARGIN}:y={TEXT_MARGIN}:fontsize=48:fontcolor=white:borderw=3:bordercolor=black,
drawtext=text='@{safe_channel}':x=w-text_w-{TEXT_MARGIN}:y=h-{TEXT_MARGIN}:fontsize=24:fontcolor=white@0.7:borderw=2:bordercolor=black@0.5[v]
"""

    # Clean up the filter (remove newlines for ffmpeg)
    filter_complex = filter_complex.replace('\n', '').replace('  ', ' ').strip()

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


def create_simple_video(
    audio_path: str,
    image_path: str,
    output_path: str,
    track_name: str = "",
    limit_duration: float = None
) -> bool:
    """
    Fallback: Simple video with spectrum bars at bottom (if complex filter fails).
    """

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        return False

    audio_duration = get_audio_duration(audio_path)
    duration = limit_duration if limit_duration and limit_duration < audio_duration else audio_duration
    total_frames = int(duration * VIDEO_FPS)

    safe_track = track_name.replace("'", "'\\''").replace(":", "\\:") if track_name else ""
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")

    VISUALIZER_HEIGHT = 150

    filter_complex = (
        f"[1:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
        f"vignette=PI/4[bg];"
        f"[0:a]showfreqs=s={VIDEO_WIDTH}x{VISUALIZER_HEIGHT}:mode=bar:colors=gold|orange:ascale=log:fscale=log[bars];"
        f"[bars]split[b1][b2];[b1]gblur=sigma=5[blur];[blur][b2]blend=all_mode=screen[glowing_bars];"
        f"[bg][glowing_bars]overlay=0:H-{VISUALIZER_HEIGHT}:format=auto[combined];"
        f"[combined]fade=t=in:st=0:d={FADE_DURATION},fade=t=out:st={max(0,duration-FADE_DURATION)}:d={FADE_DURATION}[faded];"
        f"[faded]drawtext=text='{safe_track}':x={TEXT_MARGIN}:y={TEXT_MARGIN}:fontsize=48:fontcolor=white:borderw=3:bordercolor=black,"
        f"drawtext=text='@{safe_channel}':x=w-text_w-{TEXT_MARGIN}:y=h-{TEXT_MARGIN}:fontsize=24:fontcolor=white@0.7:borderw=2:bordercolor=black@0.5[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-loop", "1", "-i", image_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p"
    ]

    if limit_duration:
        cmd.extend(["-t", str(limit_duration)])

    cmd.append(output_path)

    print(f"Creating simple video with spectrum bars...")
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

    parser = argparse.ArgumentParser(description="Create Vizzy-style circular visualizer video")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file")
    parser.add_argument("--image", "-i", required=True, help="Path to background image")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--name", "-n", default="", help="Track name for overlay")
    parser.add_argument("--simple", "-s", action="store_true", help="Use simple spectrum bars instead")
    parser.add_argument("--duration", "-d", type=float, help="Limit video duration in seconds")

    args = parser.parse_args()

    if args.simple:
        success = create_simple_video(
            args.audio, args.image, args.output,
            track_name=args.name, limit_duration=args.duration
        )
    else:
        success = create_video(
            args.audio, args.image, args.output,
            track_name=args.name, limit_duration=args.duration
        )

        # Fallback to simple if complex fails
        if not success:
            print("\nFalling back to simple visualizer...")
            success = create_simple_video(
                args.audio, args.image, args.output,
                track_name=args.name, limit_duration=args.duration
            )

    sys.exit(0 if success else 1)
