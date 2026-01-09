#!/usr/bin/env python3
"""
Check pending manual tasks for the channel
Run this to see what needs to be done in YouTube Studio
"""

import json
import os

HISTORY_FILE = 'channel_history.json'


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}


def check_pending_tasks():
    """Display all pending manual tasks"""
    history = load_history()

    print("\n" + "="*60)
    print("📋 PENDING MANUAL TASKS")
    print("="*60)

    pending = history.get('pending_tasks', {})
    shorts_pending = pending.get('shorts_need_related_video', [])

    if shorts_pending:
        print("\n🔗 Shorts needing 'Related Video' link:")
        print("   (YouTube Studio → Content → Shorts → Edit → Related Video)")
        print()
        for item in shorts_pending:
            short_id = item.get('short_id')
            title = item.get('short_title')
            link_to = item.get('link_to_video_id')
            print(f"   [ ] {title}")
            print(f"       Short: https://youtube.com/shorts/{short_id}")
            print(f"       Link to: https://youtu.be/{link_to}")
            print()
    else:
        print("\n✅ No pending 'Related Video' tasks!")

    # Check for shorts without related_video_set
    tracks = history.get('tracks', [])
    unset = []
    for track in tracks:
        if track.get('shorts_created') and not track.get('related_video_set', False):
            unset.append(track)

    if unset and not shorts_pending:
        print("\n⚠️  Shorts may need 'Related Video' set:")
        for track in unset:
            print(f"   - {track.get('title')}")

    print("="*60)

    # Show stats
    stats = history.get('stats', {})
    print(f"\n📊 Channel Stats:")
    print(f"   Uploads: {stats.get('total_uploads', 0)}")
    print(f"   Shorts: {stats.get('total_shorts', 0)}")
    print(f"   Subscribers: {stats.get('subscribers', 0)}")
    print(f"   Watch Hours: {stats.get('watch_hours', 0)}")
    print(f"   Monetization: {stats.get('monetization_status', 'not_eligible')}")
    print()


def mark_related_video_done(short_id: str):
    """Mark a short's related video as set"""
    history = load_history()

    # Remove from pending tasks
    pending = history.get('pending_tasks', {})
    shorts_pending = pending.get('shorts_need_related_video', [])
    pending['shorts_need_related_video'] = [
        s for s in shorts_pending if s.get('short_id') != short_id
    ]

    # Update track
    for track in history.get('tracks', []):
        if track.get('short_id') == short_id:
            track['related_video_set'] = True
            print(f"✅ Marked '{track.get('title')}' related video as set")

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check pending tasks")
    parser.add_argument("--done", "-d", help="Mark short ID as done (related video set)")

    args = parser.parse_args()

    if args.done:
        mark_related_video_done(args.done)

    check_pending_tasks()
