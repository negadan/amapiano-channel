#!/usr/bin/env python3
"""
Create Hour-Long Compilation Videos
Combines multiple tracks with image transitions, visualizer, and chapters
"""

import os
import json
import subprocess
from typing import List, Dict
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CHANNEL_NAME

# Compilation settings
CROSSFADE_DURATION = 3  # seconds for audio/video crossfade
VISUALIZER_HEIGHT = 150
TEXT_DISPLAY_DURATION = 5  # seconds to show track name


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS for YouTube chapters"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def create_compilation(
    compilation_info: dict,
    output_path: str,
    include_visualizer: bool = True
) -> dict:
    """
    Create hour-long compilation video

    Args:
        compilation_info: Dict with tracks list from batch_process
        output_path: Output video path
        include_visualizer: Whether to add spectrum visualizer

    Returns:
        Dict with video path and chapter timestamps
    """
    tracks = compilation_info['tracks']
    compilation_dir = os.path.dirname(compilation_info['tracks'][0].get('local_audio', ''))

    print(f"\n{'='*60}")
    print(f"CREATING COMPILATION: {len(tracks)} tracks")
    print(f"{'='*60}\n")

    # Step 1: Create concat file for audio with crossfades
    print("Step 1: Preparing audio concat...")
    audio_files = []
    for track in tracks:
        audio_path = track.get('local_audio')
        if audio_path and os.path.exists(audio_path):
            audio_files.append(audio_path)

    # Create intermediate audio with crossfades
    concat_audio = os.path.join(compilation_dir, "concat_audio.mp3")

    if len(audio_files) == 1:
        concat_audio = audio_files[0]
    else:
        # Use ffmpeg to concat with crossfade
        filter_parts = []
        for i, audio in enumerate(audio_files):
            filter_parts.append(f"[{i}:a]")

        # Build crossfade chain
        cf_filter = f"{''.join(filter_parts)}concat=n={len(audio_files)}:v=0:a=1[outa]"

        inputs = []
        for audio in audio_files:
            inputs.extend(["-i", audio])

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", cf_filter,
            "-map", "[outa]",
            "-c:a", "libmp3lame", "-q:a", "2",
            concat_audio
        ]

        print("  Concatenating audio...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Error: {result.stderr[-500:]}")
            return None

    # Calculate chapter timestamps
    print("\nStep 2: Calculating chapter timestamps...")
    chapters = []
    current_time = 0.0

    for track in tracks:
        chapters.append({
            "title": track.get('title', 'Unknown'),
            "start": current_time,
            "timestamp": format_timestamp(current_time)
        })
        duration = track.get('duration', 0)
        current_time += duration
        print(f"  {chapters[-1]['timestamp']} - {track.get('title')}")

    # Step 3: Create video with image transitions
    print("\nStep 3: Creating video with transitions...")

    # For simplicity, create video segments and concat
    # Each segment: image zoompan + visualizer + text overlay

    segment_files = []
    current_time = 0.0

    for i, track in enumerate(tracks):
        print(f"\n  [{i+1}/{len(tracks)}] {track.get('title')}")

        image_path = track.get('local_image')
        audio_path = track.get('local_audio')
        duration = track.get('duration', 0)
        title = track.get('title', 'Unknown')

        if not image_path or not audio_path:
            print(f"    Skipping - missing files")
            continue

        segment_path = os.path.join(compilation_dir, f"segment_{i:03d}.mp4")
        segment_files.append(segment_path)

        # Calculate frames
        total_frames = int(duration * VIDEO_FPS)
        safe_title = title.replace("'", "'\\''").replace(":", "\\:")

        # Build filter
        filter_parts = []

        # Background with zoom
        filter_parts.append(
            f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            f"zoompan=z='1+0.00015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
            f"vignette=PI/5[bg]"
        )

        if include_visualizer:
            # Spectrum bars
            filter_parts.append(
                f"[1:a]showfreqs=s={VIDEO_WIDTH}x{VISUALIZER_HEIGHT}:"
                f"mode=bar:ascale=sqrt:fscale=log:"
                f"colors=0xFFAA00|0xFF6600|0xFF3300:"
                f"win_size=1024[bars_raw]"
            )

            # Glow
            filter_parts.append(
                f"[bars_raw]split[b1][b2];"
                f"[b1]gblur=sigma=6[blur];"
                f"[blur][b2]blend=all_mode=screen:all_opacity=0.8[bars_glow]"
            )

            # Overlay bars
            filter_parts.append(
                f"[bars_glow]format=rgba[bars_fmt];"
                f"[bg][bars_fmt]overlay=0:H-{VISUALIZER_HEIGHT}:format=auto[with_bars]"
            )

            base_output = "[with_bars]"
        else:
            base_output = "[bg]"

        # Text overlay (track name at start)
        text_fade_out = min(TEXT_DISPLAY_DURATION, duration - 1)
        filter_parts.append(
            f"{base_output}drawtext=text='{safe_title}':"
            f"x=(w-text_w)/2:y=100:"
            f"fontsize=48:fontcolor=white:"
            f"borderw=3:bordercolor=black@0.7:"
            f"enable='lt(t,{text_fade_out})':"
            f"alpha='if(lt(t,{text_fade_out-1}),1,(({text_fade_out}-t)))'[v]"
        )

        filter_complex = ";".join(filter_parts)

        # Build segment
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            segment_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✓ Segment created")
        else:
            print(f"    ✗ Error: {result.stderr[-300:]}")

    # Step 4: Concat all segments with crossfade transitions
    print("\nStep 4: Concatenating segments with transitions...")

    if len(segment_files) == 0:
        print("No segments created!")
        return None

    # Create concat list
    concat_list = os.path.join(compilation_dir, "concat_list.txt")
    with open(concat_list, 'w') as f:
        for seg in segment_files:
            f.write(f"file '{os.path.abspath(seg)}'\n")

    # Concat without transitions (simpler, faster)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print("  Concatenating final video...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Error: {result.stderr[-500:]}")
        return None

    # Get final duration
    final_duration = get_audio_duration(output_path)
    final_minutes = final_duration / 60

    print(f"\n{'='*60}")
    print(f"✓ Compilation created!")
    print(f"  Output: {output_path}")
    print(f"  Duration: {final_minutes:.1f} minutes")
    print(f"  Tracks: {len(tracks)}")
    print(f"{'='*60}\n")

    # Generate chapter description
    chapter_text = "CHAPTERS:\n"
    for ch in chapters:
        chapter_text += f"{ch['timestamp']} - {ch['title']}\n"

    return {
        "video_path": output_path,
        "duration": final_duration,
        "chapters": chapters,
        "chapter_text": chapter_text,
        "track_count": len(tracks)
    }


def generate_compilation_description(compilation_info: dict, chapters: List[dict]) -> str:
    """Generate YouTube description with chapters"""

    mood_emoji = {
        "chill": "☕",
        "party": "🔥",
        "deep": "💫",
        "fusion": "🌍"
    }

    # Detect primary mood
    moods = [t.get('detected_mood', 'chill') for t in compilation_info['tracks']]
    primary_mood = max(set(moods), key=moods.count)
    emoji = mood_emoji.get(primary_mood, "🎵")

    description = f"""{emoji} {compilation_info['name']} | Amapiano Mix 2026

{compilation_info['total_minutes']:.0f} minutes of smooth amapiano vibes. Perfect for studying, working, or just vibing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📑 CHAPTERS (click to jump):

"""

    for ch in chapters:
        description += f"{ch['timestamp']} - {ch['title']}\n"

    description += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe to @{CHANNEL_NAME} for more Amapiano

🎧 Playlists:
▶️ Chill - Study & Relax
▶️ Party - High Energy
▶️ Deep - Soulful Vibes

#amapiano #amapianomix #studymusic #chillbeats #southafrica #amapiano2026

© {CHANNEL_NAME} 2026 - AI Generated Music
"""

    return description


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create compilation video")
    parser.add_argument("--info", "-i", required=True, help="Path to compilation_info.json")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--no-visualizer", action="store_true", help="Skip visualizer")

    args = parser.parse_args()

    with open(args.info) as f:
        compilation_info = json.load(f)

    result = create_compilation(
        compilation_info,
        args.output,
        include_visualizer=not args.no_visualizer
    )

    if result:
        print("\nChapter timestamps for YouTube description:")
        print(result['chapter_text'])
