"""
Amapiano AI YouTube Channel - Configuration Template
Copy this to config.py and fill in your API keys
"""

# API Keys (fill these in)
FAL_API_KEY = "your-fal-ai-key-here"
YOUTUBE_CLIENT_ID = "your-google-client-id.apps.googleusercontent.com"
YOUTUBE_CLIENT_SECRET = "your-google-client-secret"

# Channel Settings
CHANNEL_NAME = "LatentFlow"
CHANNEL_HANDLE = "@latentflow"

# Video Settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

# Pricing (fal.ai costs)
COST_PER_IMAGE = 0.04  # USD, Nano Banana Pro

# Playlists
PLAYLISTS = {
    "chill": "Amapiano Chill - Study & Relax",
    "party": "Amapiano Party - High Energy",
    "deep": "Amapiano Deep - Soulful Vibes",
    "fusion": "Amapiano Fusion - World Music",
    "new": "New Amapiano 2026 - Latest Hits"
}

# Visual Style Prompts
VISUAL_STYLES = {
    "nostalgic": """Nostalgic South African township at golden hour,
children playing in distance, warm analog film grain,
mellow sunset colors, soft purple and orange hues,
vintage aesthetic, amapiano vibe, dreamy atmosphere, 4K""",

    "neon_city": """South African city skyline at night, neon lights,
amapiano vibe, purple and cyan colors,
futuristic African aesthetic, 4K""",

    "abstract": """Abstract African geometric patterns,
vibrant colors, music visualization style,
dynamic flowing shapes, modern tribal art, 4K""",

    "club": """Underground club scene, DJ booth,
colored lighting, crowd silhouettes,
amapiano party atmosphere, 4K""",

    "nature": """African savanna at sunset,
silhouette of acacia trees, warm golden light,
peaceful atmosphere, cinematic composition, 4K"""
}

# Title Templates
TITLE_TEMPLATES = [
    "{track_name} | Amapiano 2026",
    "{track_name} - Amapiano Mix",
    "Amapiano: {track_name} | New SA House",
    "{track_name} | Best Amapiano 2026",
]

# Description Template
DESCRIPTION_TEMPLATE = """🎵 {track_name}
🎧 Amapiano Vibes - Your daily dose of South African house music

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 SUBSCRIBE for more Amapiano: {channel_url}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎹 Genre: {genre}
⏱️ Duration: {duration}
🌍 Style: {style}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 MORE PLAYLISTS:
▶️ Amapiano Chill - Study & Relax
▶️ Amapiano Party - High Energy
▶️ Amapiano Deep - Soulful Vibes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#amapiano #southafrica #pianomusic #amapianovibes #sahouse #newmusic2026

© All music created with AI - Original compositions
"""

# Tags
TAGS = [
    "amapiano",
    "amapiano 2026",
    "amapiano mix",
    "south african house",
    "sa house music",
    "piano music",
    "amapiano chill",
    "amapiano party",
    "african music",
    "deep house",
    "study music",
    "relax music"
]
