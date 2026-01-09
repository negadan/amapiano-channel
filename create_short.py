#!/usr/bin/env python3
"""
Create YouTube Shorts with jaw-dropping vertical images
Generates dedicated 9:16 images for maximum engagement
"""

import os
import subprocess
import requests
from typing import Optional
from config import FAL_API_KEY, VIDEO_FPS, CHANNEL_NAME

# Short settings
SHORT_WIDTH = 1080
SHORT_HEIGHT = 1920
SHORT_DURATION = 45  # seconds
VISUALIZER_HEIGHT = 250


def generate_vertical_image_prompt(track_metadata: dict) -> str:
    """
    Generate jaw-dropping vertical image prompt from track metadata
    Creates engaging, scroll-stopping visuals
    """
    description = track_metadata.get('description', '')
    title = track_metadata.get('title', '')
    mood = track_metadata.get('detected_mood', 'chill')

    # Extract scene elements from Suno description
    scene_elements = []
    desc_lower = description.lower()

    if 'playground' in desc_lower or 'children' in desc_lower:
        scene_elements.append('children playing joyfully in golden sunlight')
    if 'sunset' in desc_lower or 'golden' in desc_lower:
        scene_elements.append('breathtaking golden hour sunset with volumetric rays')
    if 'township' in desc_lower or 'south africa' in desc_lower:
        scene_elements.append('vibrant South African township with colorful houses')
    if 'night' in desc_lower or 'club' in desc_lower:
        scene_elements.append('electric nightlife with neon reflections')
    if 'nature' in desc_lower or 'savanna' in desc_lower:
        scene_elements.append('majestic African savanna with acacia silhouettes')
    if 'nostalgic' in desc_lower or 'memories' in desc_lower:
        scene_elements.append('dreamy nostalgic atmosphere with warm film grain')
    if 'piano' in desc_lower:
        scene_elements.append('elegant piano keys with dramatic lighting')

    # Mood-based base scenes
    mood_scenes = {
        "chill": "peaceful golden hour scene, warm amber tones, soft dreamy atmosphere",
        "party": "electric nightlife energy, neon lights, dancing silhouettes, vibrant colors",
        "deep": "moody atmospheric scene, deep purple and blue tones, introspective lighting",
        "fusion": "rich African cultural tapestry, traditional meets modern, bold patterns"
    }

    base_scene = mood_scenes.get(mood, mood_scenes["chill"])

    # Build the jaw-dropping prompt
    scene_part = ", ".join(scene_elements) if scene_elements else base_scene

    prompt = f"""{scene_part},
dramatic vertical composition with strong focal point,
cinematic lighting with lens flare and volumetric god rays,
hyper-detailed 8K ultra HD quality,
vibrant saturated colors that pop off screen,
African golden hour magic hour lighting,
shallow depth of field with beautiful bokeh,
professional music video aesthetic,
award-winning photography composition,
trending on ArtStation and Behance,
vertical portrait orientation 9:16 aspect ratio,
masterpiece quality, photorealistic"""

    return prompt


def generate_vertical_image(track_metadata: dict, output_path: str) -> Optional[str]:
    """Generate a jaw-dropping vertical image for a Short"""

    prompt = generate_vertical_image_prompt(track_metadata)

    print(f"Generating vertical image for: {track_metadata.get('title', 'Unknown')}")
    print(f"Prompt: {prompt[:100]}...")

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://fal.run/fal-ai/flux/schnell",
        headers=headers,
        json={
            "prompt": prompt,
            "image_size": {"width": SHORT_WIDTH, "height": SHORT_HEIGHT},
            "num_images": 1
        }
    )

    if response.status_code == 200:
        data = response.json()
        image_url = data["images"][0]["url"]

        # Download image
        img_response = requests.get(image_url)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_response.content)

        print(f"✅ Vertical image saved: {output_path}")
        return output_path
    else:
        print(f"❌ Image generation failed: {response.status_code}")
        return None


def create_short(
    audio_path: str,
    vertical_image_path: str,
    output_path: str,
    track_name: str = "",
    start_time: float = 45,
    duration: float = SHORT_DURATION
) -> bool:
    """
    Create a YouTube Short with vertical image and visualizer

    Args:
        audio_path: Path to audio file
        vertical_image_path: Path to 9:16 vertical image
        output_path: Output video path
        track_name: Track name for overlay
        start_time: Start position in audio (for hook section)
        duration: Short duration (max 60 seconds)
    """

    if not os.path.exists(audio_path):
        print(f"❌ Audio not found: {audio_path}")
        return False

    if not os.path.exists(vertical_image_path):
        print(f"❌ Image not found: {vertical_image_path}")
        return False

    total_frames = int(duration * VIDEO_FPS)
    safe_title = track_name.replace("'", "'\\''").replace(":", "\\:")
    safe_channel = CHANNEL_NAME.replace("'", "'\\''")

    print(f"Creating Short: {track_name}")
    print(f"Duration: {duration}s | Start: {start_time}s")

    # Build filter complex for vertical Short
    filter_complex = f"""
[0:v]scale={SHORT_WIDTH}:{SHORT_HEIGHT}:force_original_aspect_ratio=increase,
crop={SHORT_WIDTH}:{SHORT_HEIGHT},
zoompan=z='1+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={SHORT_WIDTH}x{SHORT_HEIGHT}:fps={VIDEO_FPS},
vignette=PI/4[bg];

[1:a]showfreqs=s={SHORT_WIDTH}x{VISUALIZER_HEIGHT}:mode=bar:ascale=sqrt:fscale=log:colors=0xFFAA00|0xFF6600|0xFF3300:win_size=1024[bars_raw];

[bars_raw]split[b1][b2];
[b1]gblur=sigma=8[blur];
[blur][b2]blend=all_mode=screen:all_opacity=0.9[bars_glow];

[bars_glow]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*min(1,(H-Y)/{VISUALIZER_HEIGHT}*1.5)'[bars_fade];

[bg][bars_fade]overlay=0:H-{VISUALIZER_HEIGHT}:format=auto[with_bars];

[with_bars]fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1,
drawtext=text='{safe_title}':x=(w-text_w)/2:y=150:fontsize=56:fontcolor=white:borderw=4:bordercolor=black@0.8,
drawtext=text='@{safe_channel}':x=(w-text_w)/2:y=h-280:fontsize=32:fontcolor=white@0.9:borderw=2:bordercolor=black@0.6[v]
"""

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", vertical_image_path,
        "-ss", str(start_time), "-t", str(duration), "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Short created: {output_path} ({size:.1f} MB)")
        return True
    else:
        print(f"❌ Error: {result.stderr[-500:]}")
        return False


def find_hook_section(audio_path: str, track_duration: float) -> float:
    """
    Find the best hook section for the Short
    Returns start time in seconds

    Strategy: Pick section after intro where groove builds
    Typically 30-90 seconds into the track
    """
    # Simple heuristic: start at ~15% into the track
    # This usually gets past the intro into the main groove
    hook_start = track_duration * 0.15

    # Ensure we have enough audio for the Short
    max_start = track_duration - SHORT_DURATION - 5
    if hook_start > max_start:
        hook_start = max(0, max_start)

    return hook_start


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Create YouTube Short with vertical image")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file")
    parser.add_argument("--metadata", "-m", help="Path to metadata.json")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--image", "-i", help="Path to existing vertical image (skip generation)")
    parser.add_argument("--start", "-s", type=float, help="Start time in seconds")
    parser.add_argument("--duration", "-d", type=float, default=SHORT_DURATION, help="Duration")

    args = parser.parse_args()

    # Load metadata if provided
    metadata = {}
    if args.metadata:
        with open(args.metadata) as f:
            metadata = json.load(f)

    # Generate or use existing vertical image
    if args.image:
        vertical_image = args.image
    else:
        vertical_image = args.output.replace('.mp4', '_vertical.png')
        generate_vertical_image(metadata, vertical_image)

    # Find hook section
    if args.start is not None:
        start_time = args.start
    else:
        duration = metadata.get('duration', 180)
        start_time = find_hook_section(args.audio, duration)

    # Create Short
    create_short(
        audio_path=args.audio,
        vertical_image_path=vertical_image,
        output_path=args.output,
        track_name=metadata.get('title', ''),
        start_time=start_time,
        duration=args.duration
    )
