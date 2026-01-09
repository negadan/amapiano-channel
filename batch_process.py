#!/usr/bin/env python3
"""
Batch Process Suno Links
Fetches metadata, calculates duration, groups by mood, generates images
"""

import os
import json
import requests
import re
from typing import List, Dict
from config import FAL_API_KEY, VISUAL_STYLES

# Mood keywords for grouping
MOOD_KEYWORDS = {
    "chill": ["nostalgic", "chill", "mellow", "relax", "warm", "soft", "gentle", "calm", "ambient", "study"],
    "party": ["party", "dance", "energy", "club", "hype", "bass", "upbeat", "groove", "bounce", "high energy"],
    "deep": ["deep", "soulful", "emotional", "introspective", "melancholic", "reflective", "moody"],
    "fusion": ["fusion", "world", "experimental", "hausa", "fuji", "afrobeat", "goje", "traditional", "ethnic"]
}


def fetch_suno_metadata(url: str) -> dict:
    """Fetch metadata from a single Suno URL"""
    from fetch_suno import fetch_suno_metadata as fetch_single
    return fetch_single(url)


def batch_fetch_metadata(urls: List[str]) -> List[dict]:
    """Fetch metadata for multiple Suno URLs"""
    tracks = []
    for i, url in enumerate(urls):
        print(f"Fetching [{i+1}/{len(urls)}]: {url}")
        try:
            metadata = fetch_suno_metadata(url)
            if metadata.get('title'):
                tracks.append(metadata)
                print(f"  ✓ {metadata['title']} ({metadata['duration']:.1f}s)")
            else:
                print(f"  ✗ Failed to fetch metadata")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    return tracks


def calculate_total_duration(tracks: List[dict]) -> float:
    """Calculate total duration of all tracks"""
    return sum(t.get('duration', 0) for t in tracks)


def detect_mood(description: str) -> str:
    """Detect primary mood from track description"""
    desc_lower = description.lower()
    scores = {mood: 0 for mood in MOOD_KEYWORDS}

    for mood, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                scores[mood] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "chill"  # default to chill


def group_by_mood(tracks: List[dict]) -> Dict[str, List[dict]]:
    """Group tracks by detected mood"""
    groups = {mood: [] for mood in MOOD_KEYWORDS}

    for track in tracks:
        mood = detect_mood(track.get('description', ''))
        track['detected_mood'] = mood
        groups[mood].append(track)

    return groups


def order_for_flow(tracks: List[dict]) -> List[dict]:
    """Order tracks for smooth listening flow"""
    # Sort by BPM if available, otherwise by mood
    def sort_key(track):
        mood_order = {"chill": 0, "deep": 1, "fusion": 2, "party": 3}
        return (mood_order.get(track.get('detected_mood', 'chill'), 0),
                track.get('bpm', 100))

    return sorted(tracks, key=sort_key)


def generate_image_prompt(track: dict) -> str:
    """Generate AI image prompt from track description"""
    desc = track.get('description', '')
    title = track.get('title', '')
    mood = track.get('detected_mood', 'chill')

    # Extract scene elements from description
    scene_elements = []
    if 'playground' in desc.lower() or 'children' in desc.lower():
        scene_elements.append('children playing in distance')
    if 'sunset' in desc.lower() or 'golden' in desc.lower():
        scene_elements.append('golden hour sunset')
    if 'township' in desc.lower() or 'south africa' in desc.lower():
        scene_elements.append('South African township')
    if 'night' in desc.lower() or 'club' in desc.lower():
        scene_elements.append('nighttime city lights')
    if 'nature' in desc.lower() or 'savanna' in desc.lower():
        scene_elements.append('African savanna landscape')

    # Build prompt based on mood
    base_prompts = {
        "chill": "Nostalgic warm scene, soft golden light, peaceful atmosphere",
        "party": "Vibrant nightlife scene, neon colors, energetic crowd silhouettes",
        "deep": "Moody atmospheric scene, purple and blue tones, introspective vibe",
        "fusion": "African cultural fusion, traditional patterns, modern aesthetic"
    }

    prompt = base_prompts.get(mood, base_prompts["chill"])
    if scene_elements:
        prompt += ", " + ", ".join(scene_elements)

    prompt += ", amapiano music visualizer style, cinematic, 4K"

    return prompt


def generate_track_image(track: dict, output_dir: str, vertical: bool = False) -> str:
    """Generate AI image for a track (horizontal for full video, vertical for Short)"""
    slug = track.get('slug', 'unknown')

    if vertical:
        # Use create_short's jaw-dropping vertical prompt
        from create_short import generate_vertical_image_prompt
        prompt = generate_vertical_image_prompt(track)
        output_path = os.path.join(output_dir, f"{slug}_vertical.png")
        width, height = 1080, 1920
    else:
        prompt = generate_image_prompt(track)
        output_path = os.path.join(output_dir, f"{slug}.png")
        width, height = 1920, 1080

    if os.path.exists(output_path):
        print(f"  Image exists: {output_path}")
        return output_path

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://fal.run/fal-ai/flux/schnell",
        headers=headers,
        json={
            "prompt": prompt,
            "image_size": {"width": width, "height": height},
            "num_images": 1
        }
    )

    if response.status_code == 200:
        data = response.json()
        image_url = data["images"][0]["url"]

        img_response = requests.get(image_url)
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_response.content)

        return output_path

    return None


def download_track_audio(track: dict, output_dir: str) -> str:
    """Download MP3 for a track"""
    mp3_url = track.get('mp3_url')
    slug = track.get('slug', 'unknown')
    output_path = os.path.join(output_dir, f"{slug}.mp3")

    if os.path.exists(output_path):
        print(f"  Audio exists: {output_path}")
        return output_path

    if not mp3_url:
        return None

    response = requests.get(mp3_url, stream=True)
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return output_path


def process_batch(urls: List[str], compilation_name: str = "compilation") -> dict:
    """
    Full batch processing pipeline
    Returns compilation info with ordered tracks
    """
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING: {len(urls)} tracks")
    print(f"{'='*60}\n")

    # 1. Fetch all metadata
    print("Step 1: Fetching metadata...")
    tracks = batch_fetch_metadata(urls)

    if not tracks:
        print("No tracks fetched!")
        return None

    # 2. Calculate duration
    total_duration = calculate_total_duration(tracks)
    total_minutes = total_duration / 60
    print(f"\nTotal duration: {total_minutes:.1f} minutes ({len(tracks)} tracks)")

    if total_minutes < 60:
        print(f"⚠️  Need {60 - total_minutes:.1f} more minutes for 1 hour")
    else:
        print(f"✓ Enough for {total_minutes/60:.1f} hour compilation")

    # 3. Group by mood
    print("\nStep 2: Analyzing moods...")
    groups = group_by_mood(tracks)
    for mood, group_tracks in groups.items():
        if group_tracks:
            print(f"  {mood}: {len(group_tracks)} tracks")

    # 4. Order for flow
    print("\nStep 3: Ordering for smooth flow...")
    ordered_tracks = order_for_flow(tracks)

    # Create output directory
    output_dir = f"compilations/{compilation_name}"
    os.makedirs(output_dir, exist_ok=True)

    # 5. Download audio and generate images (horizontal + vertical)
    print("\nStep 4: Downloading audio & generating images...")
    for i, track in enumerate(ordered_tracks):
        print(f"\n[{i+1}/{len(ordered_tracks)}] {track['title']}")

        # Download audio
        audio_path = download_track_audio(track, output_dir)
        if audio_path:
            track['local_audio'] = audio_path
            print(f"  ✓ Audio downloaded")

        # Generate horizontal image (for full video)
        image_path = generate_track_image(track, output_dir, vertical=False)
        if image_path:
            track['local_image'] = image_path
            print(f"  ✓ Horizontal image (16:9)")

        # Generate vertical image (for Short)
        vertical_path = generate_track_image(track, output_dir, vertical=True)
        if vertical_path:
            track['local_image_vertical'] = vertical_path
            print(f"  ✓ Vertical image (9:16)")

    # Save compilation info
    compilation_info = {
        "name": compilation_name,
        "total_duration": total_duration,
        "total_minutes": total_minutes,
        "track_count": len(ordered_tracks),
        "tracks": ordered_tracks
    }

    info_path = os.path.join(output_dir, "compilation_info.json")
    with open(info_path, 'w') as f:
        json.dump(compilation_info, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Batch processing complete!")
    print(f"  Output: {output_dir}")
    print(f"  Duration: {total_minutes:.1f} minutes")
    print(f"{'='*60}\n")

    return compilation_info


def print_manual_steps(tracks: List[dict]):
    """Print manual steps required after upload"""
    print("\n" + "="*60)
    print("📋 MANUAL STEPS REQUIRED (YouTube Studio)")
    print("="*60)
    print("\nFor each Short, add 'Related Video' to link to full track:")
    print("  1. Go to YouTube Studio → Content → Shorts")
    print("  2. Click ⋮ menu → Edit")
    print("  3. Select 'Related Video'")
    print("  4. Pick the full track")
    print("  5. Save")
    print("\nTracks to link:")
    for i, track in enumerate(tracks, 1):
        title = track.get('title', 'Unknown')
        print(f"  {i}. Short: '{title}' → Full: '{title}'")
    print("="*60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch process Suno links")
    parser.add_argument("--links", "-l", nargs="+", help="Suno URLs to process")
    parser.add_argument("--file", "-f", help="File containing Suno URLs (one per line)")
    parser.add_argument("--name", "-n", default="compilation", help="Compilation name")

    args = parser.parse_args()

    urls = []
    if args.links:
        urls = args.links
    elif args.file:
        with open(args.file) as f:
            urls = [line.strip() for line in f if line.strip()]

    if urls:
        process_batch(urls, args.name)
    else:
        print("Provide URLs with --links or --file")
