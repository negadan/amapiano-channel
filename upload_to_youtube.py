#!/usr/bin/env python3
"""
YouTube Upload Module for Amapiano Channel
Handles OAuth authentication and video uploads
"""

import os
import json
import pickle
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import (
    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
    CHANNEL_NAME, DESCRIPTION_TEMPLATE, TAGS
)

# OAuth scopes needed for upload
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_FILE = 'youtube_token.pickle'
HISTORY_FILE = 'channel_history.json'


def get_authenticated_service():
    """Authenticate and return YouTube API service"""
    credentials = None

    # Check for existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Create OAuth flow from credentials
            client_config = {
                "installed": {
                    "client_id": YOUTUBE_CLIENT_ID,
                    "client_secret": YOUTUBE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            # Manual console flow for Termux
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"\n{'='*60}")
            print("Open this URL in your browser to authorize:")
            print(f"\n{auth_url}\n")
            print(f"{'='*60}")
            code = input("Enter the authorization code: ").strip()
            flow.fetch_token(code=code)
            credentials = flow.credentials

        # Save token for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)


def load_history():
    """Load channel history from JSON file"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {
        "videos": [],
        "shorts": [],
        "total_uploads": 0,
        "monetization_status": "not_eligible",
        "subscribers": 0,
        "watch_hours": 0
    }


def save_history(history):
    """Save channel history to JSON file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def format_duration(seconds):
    """Format seconds to MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def upload_video(
    video_path: str,
    title: str,
    description: str = None,
    tags: list = None,
    category_id: str = "10",  # Music category
    privacy_status: str = "unlisted"
) -> dict:
    """
    Upload a video to YouTube

    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description (uses template if None)
        tags: List of tags (uses default if None)
        category_id: YouTube category ID (10 = Music)
        privacy_status: "public", "unlisted", or "private"

    Returns:
        dict with video_id and url on success
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Get authenticated service
    print("Authenticating with YouTube...")
    youtube = get_authenticated_service()

    # Prepare description
    if description is None:
        description = DESCRIPTION_TEMPLATE.format(
            track_name=title,
            channel_url=f"https://youtube.com/@{CHANNEL_NAME}",
            genre="Amapiano",
            duration="",
            style="Chill"
        )

    # Prepare tags
    if tags is None:
        tags = TAGS

    # Video metadata
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    # Upload
    print(f"Uploading: {title}")
    print(f"Privacy: {privacy_status}")

    media = MediaFileUpload(
        video_path,
        mimetype='video/mp4',
        resumable=True,
        chunksize=1024*1024  # 1MB chunks
    )

    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    # Execute with progress
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Upload progress: {progress}%")

    video_id = response['id']
    video_url = f"https://youtu.be/{video_id}"

    print(f"Upload complete!")
    print(f"Video URL: {video_url}")

    # Update history
    history = load_history()
    history["videos"].append({
        "video_id": video_id,
        "title": title,
        "uploaded_at": datetime.now().isoformat(),
        "privacy": privacy_status,
        "url": video_url,
        "local_file": video_path
    })
    history["total_uploads"] += 1
    save_history(history)

    return {
        "video_id": video_id,
        "url": video_url,
        "title": title
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", "-v", required=True, help="Path to video file")
    parser.add_argument("--title", "-t", required=True, help="Video title")
    parser.add_argument("--description", "-d", help="Video description")
    parser.add_argument("--privacy", "-p", default="unlisted",
                        choices=["public", "unlisted", "private"],
                        help="Privacy status (default: unlisted)")

    args = parser.parse_args()

    result = upload_video(
        video_path=args.video,
        title=args.title,
        description=args.description,
        privacy_status=args.privacy
    )

    print(f"\nSuccess! Video ID: {result['video_id']}")
    print(f"URL: {result['url']}")
