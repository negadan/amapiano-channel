# LatentFlow YouTube Channel - AI Agent Guide

## Overview
This is an automated YouTube music channel that publishes AI-generated music (from Suno) with custom visualizer videos. Any AI agent can use this guide to continue the automation.

**Channel:** LatentFlow (@latentflow)
**Goal:** 4,000 watch hours + 1,000 subscribers for monetization
**Content:** AI-generated music across genres (Amapiano, Afro-fusion, Soulful, etc.)

---

## Project Structure

```
/data/data/com.termux/files/home/myproject/amapiano-channel/
├── config.py                 # API keys and settings
├── youtube_token.pickle      # YouTube OAuth credentials
├── channel_history.json      # Track all uploads and stats
├── AGENT_GUIDE.md           # This file
├── tracks/                   # All processed tracks
│   ├── remember_when/
│   ├── inspired_by_the_numbers/
│   └── reborn/
└── Scripts:
    ├── create_video.py       # Main video creator (with effects)
    ├── create_short.py       # Shorts creator
    ├── upload_to_youtube.py  # YouTube uploader
    ├── fetch_suno.py         # Fetch Suno metadata
    └── batch_process.py      # Batch processing
```

---

## Complete Workflow for New Track

### Step 1: Get Track Info from User
User provides:
- Suno link (e.g., `https://suno.com/s/xyz`)
- Full description/prompt they used in Suno (IMPORTANT for mood-based images)

### Step 2: Fetch Metadata
```bash
# Use WebFetch or fetch_suno.py to get:
# - Title, duration, MP3 URL, style tags
```

### Step 3: Ask User for Details
- Track name (may need renaming)
- Playlist category: chill, party, deep, fusion, new

### Step 4: Create Track Directory & Download
```bash
mkdir -p tracks/{track_slug}
curl -L "{mp3_url}" -o tracks/{track_slug}/track.mp3
```

### Step 5: Generate Images (IMPORTANT - Read Image Philosophy Below)
Generate TWO images using fal.ai:
- **Horizontal QHD** (2560x1440) - for main video (Flux Dev model)
- **Vertical 1080p** (1080x1920) - for Short

```python
import requests

FAL_API_KEY = "51f834d9-a22b-414e-969c-911f4432e10d:d063d2fbecb810e27babbcd7ab22c3ce"

# Generate image (Use Flux Dev for best results)
response = requests.post(
    "https://fal.run/fal-ai/flux/dev",
    headers={
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "prompt": "YOUR MOOD-BASED PROMPT HERE",
        "image_size": {"width": 2560, "height": 1440},
        "num_images": 1
    }
)
image_url = response.json()["images"][0]["url"]
```

### Step 6: Create Videos

**Main Video (4K with effects):**
```bash
python3 create_video.py \
  --audio tracks/{slug}/track.mp3 \
  --image tracks/{slug}/thumbnail.png \
  --output tracks/{slug}/video.mp4 \
  --name "Track Name"
```

For TRUE 4K, use this ffmpeg command:
```bash
ffmpeg -y -loop 1 -i thumbnail.png -i track.mp3 \
-filter_complex "
[0:v]scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,
zoompan=z='1+0.0001*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=FRAMES:s=3840x2160:fps=30,
vignette=PI/5[bg];
[1:a]showfreqs=s=3840x360:mode=bar:ascale=sqrt:fscale=log:colors=0xFFAA00|0xFF6600|0xFF3300:win_size=1024[bars_raw];
[bars_raw]split[b1][b2];[b1]gblur=sigma=8[bars_blur];[bars_blur][b2]blend=all_mode=screen:all_opacity=0.9[bars_glow];
[1:a]showwaves=s=3840x2160:mode=p2p:colors=white@0.3:scale=sqrt:rate=30[waves_raw];[waves_raw]gblur=sigma=2[sparkles];
[bg][sparkles]blend=all_mode=screen:all_opacity=0.15[bg_sparkle];
[bars_glow]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*min(1,(H-Y)/360*1.5)'[bars_fade];
[bg_sparkle][bars_fade]overlay=0:H-360:format=auto[with_bars];
[with_bars]fade=t=in:st=0:d=2,fade=t=out:st=FADE_OUT_START:d=2,
drawtext=text='TRACK NAME':x=120:y=120:fontsize=104:fontcolor=white:borderw=6:bordercolor=black@0.7,
drawtext=text='@LatentFlow':x=w-text_w-120:y=h-480:fontsize=52:fontcolor=white@0.8:borderw=4:bordercolor=black@0.5,
format=yuv420p[v]
" -map "[v]" -map 1:a -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -shortest video.mp4
```

**Short (1080p with pulsing zoom):**
```bash
ffmpeg -y -loop 1 -i short_vertical.png -ss 20 -i track.mp3 \
-filter_complex "
[0:v]scale=1200:2133,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,
zoompan=z='1.02+0.015*sin(2*PI*on/120)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,
eq=brightness=0.02:saturation=1.1,vignette=PI/4[video];
[1:a]showfreqs=s=1080x200:mode=bar:colors=white|orange:fscale=log:ascale=log[spectrum];
color=c=black:s=1080x1920:d=55[bg];
[bg][video]overlay=0:0[v1];
[v1][spectrum]overlay=0:H-h-80:shortest=1,format=yuv420p[outv]
" -map "[outv]" -map 1:a -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -t 55 short.mp4
```

### Step 7: Upload to YouTube
```bash
python3 upload_to_youtube.py \
  --video tracks/{slug}/video.mp4 \
  --title "Track Name | Style 2026" \
  --privacy public

python3 upload_to_youtube.py \
  --video tracks/{slug}/short.mp4 \
  --title "Track Name | Style #Shorts" \
  --privacy public
```

### Step 8: Add to Playlist
```python
import pickle
from googleapiclient.discovery import build

with open('youtube_token.pickle', 'rb') as token:
    credentials = pickle.load(token)

youtube = build('youtube', 'v3', credentials=credentials)

# Playlist IDs
PLAYLISTS = {
    "chill": "PLBJ04ECkxUV95VcSO14RE3P2fV4QPWLsz",
    "party": "PLBJ04ECkxUV_PLrxk61qWLvl7L0wjAeio",
    "deep": "PLBJ04ECkxUV-kLbBBjv0OvKEVrvl-ZID1",
    "fusion": "PLBJ04ECkxUV8-UDbqOUufD6ldifgAcTIy",
    "new": "PLBJ04ECkxUV-eULEkdUdbq8Swp95J7J6C"
}

youtube.playlistItems().insert(
    part="snippet",
    body={
        "snippet": {
            "playlistId": PLAYLISTS["deep"],
            "resourceId": {"kind": "youtube#video", "videoId": "VIDEO_ID"}
        }
    }
).execute()
```

### Step 9: Update channel_history.json
Add the new track to the tracks array and update stats.

---

## IMAGE PROMPTING PHILOSOPHY (CRITICAL)

### DO NOT:
- Literally describe instruments ("dùndún drums in foreground")
- Include specific objects mentioned in song description
- Be too literal with the song content

### DO:
- Capture the MOOD and EMOTIONAL FEEL
- Use colors that match the vibe
- Create cinematic, visually appealing scenes
- Think: "What atmosphere does this music create?"

### Mood-to-Visual Mapping:

| Song Mood | Visual Elements |
|-----------|-----------------|
| Nostalgic, Soulful | Golden hour, warm amber, silhouettes, dust particles, soft light |
| Party, High Energy | Neon lights, vibrant colors, city nights, movement blur |
| Chill, Relaxing | Soft pastels, nature, water, clouds, serene landscapes |
| Spiritual, Deep | Sunrise/sunset, ethereal light rays, mystical atmosphere |
| Afro-fusion | African landscapes, warm earth tones, cultural patterns (subtle) |

### Example Transformation:

**Song Description:** "Nostalgic Three Step recording of kids playing and laughing, Amapiano journey, Jazzy & Soulful, West African percussion, dùndún drums, Yoruba groove, spiritual feel"

**BAD Image Prompt:** "Nigerian village with dùndún drums, children playing with percussion instruments, Yoruba patterns"

**GOOD Image Prompt:** "Golden hour African landscape, warm nostalgic childhood memory atmosphere, silhouettes of children playing in dusty golden light, spiritual sunset with deep orange and amber sky, soft lens flare and floating dust particles, soulful dreamy atmosphere, cinematic wide shot, warm earth tones, peaceful village soft focus background, emotional evocative mood"

### Color Palettes by Playlist:
- **Chill:** Soft blues, purples, pastels, muted tones
- **Party:** Vibrant pinks, cyans, neons, high contrast
- **Deep:** Warm ambers, oranges, golds, earth tones
- **Fusion:** Rich earth tones mixed with vibrant accents

---

## Main Video Effects (create_video.py)
- Ken Burns slow zoom (0.01% per frame)
- Glowing orange spectrum bars at bottom
- Sparkle particles synced to audio
- Cinematic vignette
- Fade in/out (2 seconds)
- Track name (top left)
- @LatentFlow watermark (bottom right)

## Short Effects
- Slow breathing/pulsing zoom (in/out cycle)
- Orange/white spectrum bars at bottom
- Saturation boost + vignette
- No text overlays
- 50-60 seconds duration
- Start from ~20 seconds into track (skip intro)

---

## API Keys & Credentials

**fal.ai (Image Generation):**
```
FAL_API_KEY = "51f834d9-a22b-414e-969c-911f4432e10d:d063d2fbecb810e27babbcd7ab22c3ce"
```

**YouTube:** OAuth credentials stored in `youtube_token.pickle`

---

## Current Channel Stats
Check `channel_history.json` for:
- All uploaded tracks
- Video IDs and URLs
- Playlist assignments
- Pending tasks (like setting Related Video on Shorts)

---

## Manual Tasks (YouTube Studio)
After uploading Shorts, manually set "Related Video" to link to main video:
1. Go to YouTube Studio → Content → Shorts
2. Edit the Short → Related Video → Select main video

---

## Troubleshooting

### Video shows wrong resolution:
Check with: `ffprobe -v error -select_streams v:0 -show_entries stream=width,height video.mp4`

### YouTube upload fails:
- Check youtube_token.pickle is valid
- May need to re-authenticate with authenticate_youtube.py

### 4K render too slow:
- **USE HARDWARE ACCELERATION:** On Android/Termux, use `-c:v h264_mediacodec` instead of `libx264`.
- **Optimize Filters:** Render visualizers at 1080p and scale up, rather than rendering at 4K.
- **Backgrounding:** Keep Termux in the foreground or use `termux-wake-lock` to prevent the OS from killing the process.

**Optimized 4K Command for Termux:**
```bash
ffmpeg -y -loop 1 -i thumbnail.png -i track.mp3 \
-filter_complex "
[0:v]scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,
zoompan=z='1+0.0001*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=FRAMES:s=3840x2160:fps=30,
vignette=PI/5[bg];
[1:a]showfreqs=s=1920x180:mode=bar:ascale=sqrt:fscale=log:colors=0xFFAA00|0xFF6600|0xFF3300:win_size=1024[bars_raw];
[bars_raw]split[b1][b2];[b1]gblur=sigma=4[bars_blur];[bars_blur][b2]blend=all_mode=screen:all_opacity=0.9,scale=3840:180[bars_glow];
[1:a]showwaves=s=1920x1080:mode=p2p:colors=white@0.3:scale=sqrt:rate=30[waves_raw];[waves_raw]gblur=sigma=2,scale=3840:2160[sparkles];
[bg][sparkles]blend=all_mode=screen:all_opacity=0.15[bg_sparkle];
[bars_glow]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*min(1,(H-Y)/180*1.5)'[bars_fade];
[bg_sparkle][bars_fade]overlay=0:H-180:format=auto[with_bars];
[with_bars]fade=t=in:st=0:d=2,fade=t=out:st=FADE_OUT_START:d=2,
drawtext=text='TRACK NAME':x=120:y=120:fontsize=104:fontcolor=white:borderw=6:bordercolor=black@0.7,
drawtext=text='@LatentFlow':x=w-text_w-120:y=h-480:fontsize=52:fontcolor=white@0.8:borderw=4:bordercolor=black@0.5,
format=yuv420p[v]
" -map "[v]" -map 1:a -c:v h264_mediacodec -b:v 12M -c:a aac -b:a 192k -shortest video.mp4
```

---

## Quick Reference Commands

```bash
# Check video resolution
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 video.mp4

# Get audio duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 track.mp3

# Copy to Downloads for preview
cp file.png /storage/emulated/0/Download/

# Check channel history
cat channel_history.json | python3 -m json.tool
```

---

## Contact
Channel: https://youtube.com/@latentflow
This automation was built to create a million-dollar music channel through consistent, quality AI-generated content.
