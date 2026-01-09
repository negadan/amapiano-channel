#!/usr/bin/env python3
"""
Create a CORRECT parallax effect using FFmpeg.
Separates background and foreground using a mask and animates them with different zoom speeds.
"""

import os
import subprocess
import sys
import argparse

# Constants
WIDTH = 1080
HEIGHT = 1920
FPS = 30

def create_parallax_video(
    image_path: str,
    mask_path: str,
    audio_path: str,
    output_path: str,
    duration: float = 15.0,
    invert_mask: bool = False
) -> bool:
    """
    Create a parallax video from an image and a mask.
    
    Args:
        image_path: Path to the full image.
        mask_path: Path to the grayscale mask (white = foreground).
        audio_path: Path to the audio file.
        output_path: Path to save the video.
        duration: Duration of the video in seconds.
        invert_mask: Whether to invert the mask (if white = background).
    """
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return False
    if not os.path.exists(mask_path):
        print(f"Error: Mask not found: {mask_path}")
        return False
        
    print(f"Creating parallax video...")
    print(f"Image: {image_path}")
    print(f"Mask: {mask_path}")
    print(f"Output: {output_path}")
    
    total_frames = int(duration * FPS)
    
    # FFmpeg Filter Complex
    # 1. Prepare Background (Layer 0)
    #    - Start at scale 1.0
    #    - Zoom in slowly to 1.10 over duration
    #    - Blur slightly to create depth of field and hide the "hole" behind foreground
    
    # 2. Prepare Foreground (Layer 1)
    #    - Apply mask to image to create transparent foreground
    #    - Start at scale 1.05 (slightly larger/closer)
    #    - Zoom in faster to 1.25 over duration
    
    # 3. Overlay
    
    # Note on Masking:
    # alphamerge takes [RGB][Alpha]. 
    # If mask is grayscale, we can use it as alpha directly or after formatting.
    
    mask_filter = "[1:v]format=gray"
    if invert_mask:
        mask_filter += ",negate"
    mask_filter += "[mask];"
    
    filter_complex = (
        f"{mask_filter}"
        f"[0:v][mask]alphamerge[fg_raw];"
        
        # Background Layer
        # Scale to avoid jitter, then zoompan.
        # z='min(zoom+0.0003,1.15)': Zoom speed 0.0003 per frame.
        f"[0:v]scale=-1:{HEIGHT},zoompan=z='min(zoom+0.0003,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        f"gblur=sigma=3[bg];"
        
        # Foreground Layer
        # Start zoom at 1.1 to seem closer? 
        # Actually zoompan z init value is 1. If we want it larger, we can just zoom faster.
        # But for parallax, the FG should move MORE than the BG.
        # z='min(zoom+0.0008,1.3)'
        f"[fg_raw]scale=-1:{HEIGHT},zoompan=z='min(zoom+0.0008,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={WIDTH}x{HEIGHT}:fps={FPS}[fg];"
        
        # Composite
        f"[bg][fg]overlay=0:0[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-loop", "1", "-i", mask_path,
    ]
    
    if os.path.exists(audio_path):
        cmd.extend(["-i", audio_path])
        map_audio = "-map 2:a"
    else:
        # Generate silent audio if needed or just ignore
        map_audio = ""
        
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]"
    ])
    
    if map_audio:
        cmd.extend(map_audio.split())
        
    cmd.extend([
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_path
    ])
    
    # print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Success! Video saved to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running ffmpeg: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Parallax Video")
    parser.add_argument("--image", "-i", required=True, help="Main image path")
    parser.add_argument("--mask", "-m", required=True, help="Mask image path")
    parser.add_argument("--audio", "-a", help="Audio file path")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--duration", "-d", type=float, default=15.0, help="Duration in seconds")
    parser.add_argument("--invert", action="store_true", help="Invert mask")
    
    args = parser.parse_args()
    
    create_parallax_video(
        args.image,
        args.mask,
        args.audio,
        args.output,
        args.duration,
        args.invert
    )
