#!/usr/bin/env python3
"""
One-time YouTube authentication script
Run this once to get your OAuth token, then uploads work automatically
"""

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

from config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_FILE = 'youtube_token.pickle'

def authenticate():
    """Run OAuth flow and save token"""
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

    auth_url, _ = flow.authorization_url(prompt='consent')

    print("\n" + "="*60)
    print("YOUTUBE AUTHENTICATION")
    print("="*60)
    print("\n1. Open this URL in your browser:\n")
    print(auth_url)
    print("\n2. Sign in with your YouTube/Google account")
    print("3. Click 'Allow' to grant upload permissions")
    print("4. Copy the authorization code shown")
    print("="*60 + "\n")

    code = input("Paste the authorization code here: ").strip()

    flow.fetch_token(code=code)

    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(flow.credentials, token)

    print("\nAuthentication successful!")
    print(f"Token saved to: {TOKEN_FILE}")
    print("You can now upload videos without re-authenticating.")

if __name__ == "__main__":
    authenticate()
