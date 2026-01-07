#!/usr/bin/env python3
"""
Suno Track Metadata Fetcher
Extracts metadata from Suno URLs and saves for pipeline use
"""

import os
import re
import json
import requests
from urllib.parse import urlparse

# Playlist categorization keywords
PLAYLIST_KEYWORDS = {
    "chill": ["nostalgic", "chill", "mellow", "relax", "warm", "study", "ambient", "soft", "gentle", "calm"],
    "party": ["party", "dance", "energy", "club", "hype", "bass-heavy", "upbeat", "groove", "bounce"],
    "deep": ["deep", "soulful", "emotional", "introspective", "melancholic", "reflective"],
    "fusion": ["fusion", "world", "experimental", "hausa", "fuji", "afrobeat", "goje", "traditional"]
}


def extract_track_id(url: str) -> str:
    """Extract track ID from Suno URL"""
    # Handle different URL formats
    # https://suno.com/s/M2sT9pAduGvae9pI
    # https://suno.com/song/M2sT9pAduGvae9pI
    path = urlparse(url).path
    return path.split('/')[-1]


def fetch_suno_metadata(url: str) -> dict:
    """
    Fetch metadata from a Suno track URL

    Returns dict with:
    - title, artist, duration, description
    - mp3_url, image_url
    - genre_tags, bpm
    - playlist (auto-categorized)
    """
    track_id = extract_track_id(url)

    # Fetch the page
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; AmapianoBot/1.0)'
    })
    response.raise_for_status()
    html = response.text

    # Extract JSON data from page (Suno embeds metadata in script tags)
    metadata = {}

    # Try to find the embedded JSON data
    json_match = re.search(r'<script[^>]*type="application/json"[^>]*>([^<]+)</script>', html)
    if json_match:
        try:
            page_data = json.loads(json_match.group(1))
            # Navigate to track data (structure varies)
            if 'props' in page_data:
                props = page_data.get('props', {})
                page_props = props.get('pageProps', {})
                clip = page_props.get('clip', {})
                if clip:
                    metadata = {
                        'title': clip.get('title', ''),
                        'artist': clip.get('display_name', ''),
                        'duration': clip.get('metadata', {}).get('duration', 0),
                        'description': clip.get('metadata', {}).get('prompt', ''),
                        'genre_tags': clip.get('metadata', {}).get('tags', ''),
                        'bpm': extract_bpm(clip.get('metadata', {}).get('prompt', '')),
                        'mp3_url': clip.get('audio_url', ''),
                        'image_url': clip.get('image_large_url', '') or clip.get('image_url', ''),
                        'suno_id': clip.get('id', track_id),
                        'suno_url': url,
                        'plays': clip.get('play_count', 0),
                        'created_at': clip.get('created_at', '')
                    }
        except json.JSONDecodeError:
            pass

    # Fallback: try alternative JSON structure
    if not metadata.get('title'):
        # Look for __NEXT_DATA__ script
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
        if next_data_match:
            try:
                next_data = json.loads(next_data_match.group(1))
                clip = next_data.get('props', {}).get('pageProps', {}).get('clip', {})
                if clip:
                    prompt = clip.get('metadata', {}).get('prompt', '')
                    metadata = {
                        'title': clip.get('title', ''),
                        'artist': clip.get('display_name', ''),
                        'duration': clip.get('metadata', {}).get('duration', 0),
                        'description': prompt,
                        'genre_tags': clip.get('metadata', {}).get('tags', ''),
                        'bpm': extract_bpm(prompt),
                        'mp3_url': clip.get('audio_url', ''),
                        'image_url': clip.get('image_large_url', '') or clip.get('image_url', ''),
                        'suno_id': clip.get('id', track_id),
                        'suno_url': url,
                        'plays': clip.get('play_count', 0),
                        'created_at': clip.get('created_at', '')
                    }
            except json.JSONDecodeError:
                pass

    # Auto-categorize playlist based on description
    if metadata.get('description'):
        metadata['playlist'] = categorize_playlist(metadata['description'])
    else:
        metadata['playlist'] = 'new'

    # Generate slug for folder name
    if metadata.get('title'):
        metadata['slug'] = slugify(metadata['title'])

    return metadata


def extract_bpm(text: str) -> int:
    """Extract BPM from description text"""
    bpm_match = re.search(r'(\d{2,3})\s*bpm', text.lower())
    if bpm_match:
        return int(bpm_match.group(1))
    return 0


def categorize_playlist(description: str) -> str:
    """Auto-categorize track to playlist based on description keywords"""
    desc_lower = description.lower()

    scores = {playlist: 0 for playlist in PLAYLIST_KEYWORDS}

    for playlist, keywords in PLAYLIST_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                scores[playlist] += 1

    # Get highest scoring playlist
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return 'new'


def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    # Lowercase and replace spaces with underscores
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '_', slug)
    return slug


def save_track_metadata(metadata: dict, base_dir: str = 'tracks') -> str:
    """
    Save metadata to tracks/{slug}/metadata.json
    Returns the track directory path
    """
    slug = metadata.get('slug', 'unknown')
    track_dir = os.path.join(base_dir, slug)

    os.makedirs(track_dir, exist_ok=True)

    metadata_path = os.path.join(track_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved metadata to: {metadata_path}")
    return track_dir


def download_track_audio(metadata: dict, track_dir: str) -> str:
    """Download MP3 to track directory"""
    mp3_url = metadata.get('mp3_url')
    if not mp3_url:
        print("No MP3 URL found")
        return None

    mp3_path = os.path.join(track_dir, 'track.mp3')

    print(f"Downloading audio...")
    response = requests.get(mp3_url, stream=True)
    response.raise_for_status()

    with open(mp3_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Saved audio to: {mp3_path}")
    return mp3_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Suno track metadata")
    parser.add_argument("url", help="Suno track URL")
    parser.add_argument("--download", "-d", action="store_true", help="Also download MP3")

    args = parser.parse_args()

    print(f"Fetching: {args.url}")
    metadata = fetch_suno_metadata(args.url)

    if metadata.get('title'):
        print(f"\nTrack: {metadata['title']}")
        print(f"Artist: {metadata['artist']}")
        print(f"Duration: {metadata['duration']:.1f}s")
        print(f"Playlist: {metadata['playlist']}")
        print(f"BPM: {metadata['bpm']}")
        print(f"\nDescription:\n{metadata['description']}")

        # Save metadata
        track_dir = save_track_metadata(metadata)

        # Download if requested
        if args.download:
            download_track_audio(metadata, track_dir)
    else:
        print("Failed to extract metadata")
