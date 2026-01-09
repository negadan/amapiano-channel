# Quick Start for AI Agents

## When User Says "Process this track" or shares a Suno link:

### 1. Get Info
Ask for:
- The Suno link
- The FULL description they used in Suno (for mood-based image generation)
- Preferred track name (if they want to rename it)

### 2. Fetch & Download
```bash
cd /data/data/com.termux/files/home/myproject/amapiano-channel

# Create directory
mkdir -p tracks/{track_slug}

# Download MP3 from Suno CDN URL
curl -L "{mp3_url}" -o tracks/{track_slug}/track.mp3
```

### 3. Generate Images
Use fal.ai with MOOD-BASED prompts (not literal instruments).

Analyze the song description for:
- Emotional mood (nostalgic? energetic? peaceful? spiritual?)
- Match to color palette (warm = deep/soulful, cool = chill, vibrant = party)

Generate:
- 4K horizontal (3840x2160) → `thumbnail.png`
- 1080p vertical (1080x1920) → `short_vertical.png`

**ALWAYS show user the images before proceeding!**
```bash
cp tracks/{slug}/thumbnail.png /storage/emulated/0/Download/preview.png
```

### 4. Create Videos
Main video (4K):
```bash
python3 create_video.py --audio tracks/{slug}/track.mp3 --image tracks/{slug}/thumbnail.png --output tracks/{slug}/video.mp4 --name "Track Name"
```

Short (1080p, 55 seconds):
```bash
# Use ffmpeg with pulsing zoom effect (see AGENT_GUIDE.md)
```

### 5. Upload
```bash
python3 upload_to_youtube.py --video tracks/{slug}/video.mp4 --title "Track Name | Style 2026" --privacy public
python3 upload_to_youtube.py --video tracks/{slug}/short.mp4 --title "Track Name | Style #Shorts" --privacy public
```

### 6. Add to Playlist
Use YouTube API (see AGENT_GUIDE.md for code)

### 7. Update channel_history.json
Add new track entry with all IDs and URLs.

---

## Current Pending Work

Check `channel_history.json` for:
- `pending_tasks.shorts_need_related_video` - Shorts that need Related Video set in YouTube Studio

## Playlist Categories
- **chill** - Study & Relax (soft, mellow tracks)
- **party** - High Energy (upbeat, danceable)
- **deep** - Soulful Vibes (emotional, spiritual, Afro-fusion)
- **fusion** - World Music (experimental, cross-genre)
- **new** - New Releases 2026

---

## Important Notes
- Main videos: 4K (3840x2160) with full effects
- Shorts: 1080p (1080x1920) with pulsing zoom
- Always preview images with user before creating videos
- Image prompts should capture MOOD, not literal song content
- Update channel_history.json after every upload
