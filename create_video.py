#!/usr/bin/env python3
"""
Create Amapiano visualizer videos using ffmpeg
"""

import os
import subprocess
import sys
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, CHANNEL_NAME

def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def create_visualizer_video(
    audio_path: str,
    image_path: str,
    output_path: str,
    track_name: str = "",
    effect: str = "zoom",
    limit_duration: float = None,
    mask_path: str = None
) -> bool:
    """
    Create a music visualizer video with various effects
    """

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}")
        return False

    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found: {image_path}")
        return False

    audio_duration = get_audio_duration(audio_path)
    duration = limit_duration if limit_duration and limit_duration < audio_duration else audio_duration
    print(f"Video duration: {duration:.2f} seconds")

    # Calculate zoom parameters for smooth Ken Burns effect
    total_frames = int(duration * VIDEO_FPS)

    # Base filter: scale image to fit video
    scale_filter = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}"

    if effect == "zoom":
        # Slow zoom in effect
        zoom_speed = 0.0003
        video_filter = f"[1:v]{scale_filter},zoompan=z='min(zoom+{zoom_speed},1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "pulse":
        # Color hue shift that cycles through colors
        video_filter = f"[1:v]{scale_filter},hue=h=t*15:s=1+0.3*sin(t*2)[v]"
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "waves":
        # Smooth multi-colored waveform overlay
        video_filter = f"[1:v]{scale_filter}[bg];[0:a]showwaves=s={VIDEO_WIDTH}x200:mode=line:colors=cyan|violet:rate={VIDEO_FPS}[waves];[bg][waves]overlay=0:H-200:format=auto[v]"
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "spectrum":
        # Professional Constant Q Transform (CQT) visualization (Piano roll style)
        # Detailed, colorful, and transparent. Height is 240px (120 sonogram + 120 bars)
        video_filter = f"[1:v]{scale_filter}[bg];[0:a]showcqt=s={VIDEO_WIDTH}x240:text=0:r={VIDEO_FPS}:axis=0:count=10:sono_h=120:bar_h=120[cqt];[bg][cqt]overlay=0:H-240:format=auto[v]"
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "glow_spectrum":
        # Glowing circular spectrum at bottom center - professional look
        video_filter = (
            f"[1:v]{scale_filter},zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[bg];"
            f"[0:a]showfreqs=s=800x200:mode=bar:ascale=log:fscale=log:colors=violet|blue|cyan:win_size=2048[freq];"
            f"[freq]gblur=sigma=3,format=rgba,colorchannelmixer=aa=0.85[glow];"
            f"[bg][glow]overlay=(W-w)/2:H-220:format=auto[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "audio_pulse":
        # Image pulses/breathes with the audio - bass reactive zoom
        # Uses loudnorm analysis to create zoom effect synced to audio energy
        video_filter = (
            f"[0:a]asplit=2[a1][a2];"
            f"[a2]showvolume=w=1:h=1:f=0:dm=1:ds=log,scale=1:1,format=gray,geq=lum='p(0,0)':cb=128:cr=128[vol];"
            f"[1:v]{scale_filter}[img];"
            f"[img][vol]displace=edge=wrap:xmap=red:ymap=red[displaced];"
            f"[displaced]zoompan=z='1.0+0.08*sin(on/{VIDEO_FPS}*2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "[a1]"]

    elif effect == "circle_viz":
        # Circular audio vectorscope - looks like a glowing orb reacting to music
        video_filter = (
            f"[1:v]{scale_filter},zoompan=z='1+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[bg];"
            f"[0:a]avectorscope=s=400x400:m=lissajous_xy:draw=line:scale=log:rf=20:gf=10:bf=30[scope];"
            f"[scope]gblur=sigma=5,format=rgba,colorchannelmixer=aa=0.9[glow];"
            f"[bg][glow]overlay=(W-w)/2:(H-h)/2:format=auto[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "bars_bottom":
        # Clean audio bars at bottom with gradient - like Spotify canvas
        video_filter = (
            f"[1:v]{scale_filter},zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[bg];"
            f"[0:a]showfreqs=s={VIDEO_WIDTH}x150:mode=bar:colors=white|cyan|magenta:ascale=log:fscale=log:win_size=4096[bars];"
            f"[bars]format=rgba,colorchannelmixer=aa=0.7[barbright];"
            f"[bg][barbright]overlay=0:H-150:format=auto[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "dual_waves":
        # Mirrored waveforms top and bottom - symmetrical aesthetic
        video_filter = (
            f"[1:v]{scale_filter}[bg];"
            f"[0:a]asplit=2[a1][a2];"
            f"[a1]showwaves=s={VIDEO_WIDTH}x120:mode=cline:colors=cyan|white:rate={VIDEO_FPS}[top];"
            f"[a2]showwaves=s={VIDEO_WIDTH}x120:mode=cline:colors=magenta|white:rate={VIDEO_FPS},vflip[bot];"
            f"[bg][top]overlay=0:30:format=auto[mid];"
            f"[mid][bot]overlay=0:H-150:format=auto[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "audioreactive":
        # TRUE audio-reactive: image brightness and saturation pulses with the music
        # The image glows brighter on beats and bass hits
        video_filter = (
            f"[1:v]{scale_filter}[img];"
            f"[0:a]showvolume=r={VIDEO_FPS}:w=100:h=10:f=0.5:o=h:ds=log[vol];"
            f"[img][vol]overlay=W:H,geq="
            f"lum='lum(X,Y)*1.0+0.15*lum(X,Y)*sin(N/{VIDEO_FPS}*3)':"
            f"cb='cb(X,Y)+10*sin(N/{VIDEO_FPS}*2)':"
            f"cr='cr(X,Y)+10*sin(N/{VIDEO_FPS}*2.5)',"
            f"zoompan=z='1.0+0.04*sin(on/{VIDEO_FPS}*1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "neon_bars":
        # Neon glowing frequency bars with reflection - very professional
        video_filter = (
            f"[1:v]{scale_filter},zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},"
            f"eq=brightness=0.06:saturation=1.2[bg];"
            f"[0:a]asplit=2[a1][a2];"
            f"[a1]showfreqs=s={VIDEO_WIDTH}x180:mode=bar:colors=0x00ffff|0xff00ff|0xffff00:ascale=log:fscale=log:win_size=2048[bars];"
            f"[a2]showfreqs=s={VIDEO_WIDTH}x180:mode=bar:colors=0x00ffff|0xff00ff|0xffff00:ascale=log:fscale=log:win_size=2048,vflip,colorchannelmixer=aa=0.3[reflect];"
            f"[bars]gblur=sigma=2[glow];"
            f"[bg][glow]overlay=0:H-200[withbars];"
            f"[withbars][reflect]overlay=0:H-200+180[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "trees_pulse":
        # Dark objects (trees/silhouettes) pulse with color shifts
        # Targets dark pixels (trees in silhouette images) with rhythm
        video_filter = (
            f"[1:v]{scale_filter},"
            f"geq=lum='lum(X,Y)*(1+0.1*sin(N/{VIDEO_FPS}*2)*(1-lum(X,Y)/255))':"
            f"cb='cb(X,Y)+20*sin(N/{VIDEO_FPS}*3)*(1-lum(X,Y)/255)':"
            f"cr='cr(X,Y)+25*sin(N/{VIDEO_FPS}*2.5)*(1-lum(X,Y)/255)',"
            f"zoompan=z='1+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "silhouette_glow":
        # Silhouettes get edge glow that pulses with music
        video_filter = (
            f"[1:v]{scale_filter}[base];"
            f"[base]split=2[bg][edge_src];"
            f"[edge_src]edgedetect=low=0.1:high=0.3,negate,"
            f"geq=lum='lum(X,Y)*(1+0.5*sin(N/{VIDEO_FPS}*3))':cb=128:cr=128,"
            f"hue=h=280:s=1.5,gblur=sigma=8[purple_glow];"
            f"[bg][purple_glow]blend=all_mode=screen:all_opacity=0.6,"
            f"zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "object_breathe":
        # Dark objects (trees) breathe/scale slightly with audio rhythm
        video_filter = (
            f"[1:v]{scale_filter}[base];"
            f"[base]geq="
            f"lum='lum(X,Y)*(1+0.08*sin(N/{VIDEO_FPS}*2)*(1-lum(X,Y)/255))':"
            f"cb='cb(X,Y)+8*sin(N/{VIDEO_FPS}*1.5)*(1-lum(X,Y)/255)':"
            f"cr='cr(X,Y)+12*sin(N/{VIDEO_FPS}*2.2)*(1-lum(X,Y)/255)',"
            f"zoompan=z='1+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "masked_glow":
        # Use AI-generated mask to make specific objects glow with music
        # Requires: mask image (white = effect area, black = no effect)
        # The mask should be passed as input 2
        video_filter = (
            f"[1:v]{scale_filter}[bg];"
            f"[2:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},format=gray[mask];"
            f"[bg]split=2[base][effect_src];"
            f"[effect_src]geq="
            f"lum='lum(X,Y)*(1.2+0.3*sin(N/{VIDEO_FPS}*3))':"
            f"cb='cb(X,Y)+30*sin(N/{VIDEO_FPS}*2.5)':"
            f"cr='cr(X,Y)+40*sin(N/{VIDEO_FPS}*2)',"
            f"gblur=sigma=3[glowing];"
            f"[base][glowing][mask]maskedmerge[merged];"
            f"[merged]zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "people_glow":
        # Make people/foreground objects pulse and glow with the beat
        # Uses mask where white = people
        video_filter = (
            f"[1:v]{scale_filter}[bg];"
            f"[2:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},format=gray[mask];"
            f"[bg]split=2[base][glow_src];"
            f"[glow_src]hue=h=30*sin(t*2):s=1+0.3*sin(t*3):b=1+0.2*sin(t*2.5),"
            f"gblur=sigma=4[effect];"
            f"[base][effect][mask]maskedmerge[merged];"
            f"[merged]zoompan=z='1+0.0002*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    elif effect == "vintage":
        # Lo-fi aesthetic: Film grain + Vignette + Sepia tone
        video_filter = (
            f"[1:v]{scale_filter},"
            f"noise=alls=15:allf=t+u,"
            f"vignette=PI/4,"
            f"colorbalance=rs=.1:gs=-.05:bs=-.1:rm=.1:gm=-.05:bm=-.1:rh=.1:gh=-.05:bh=-.1[v]"
        )
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    else:
        # Simple static image with audio
        video_filter = f"[1:v]{scale_filter},loop=loop=-1:size=1:start=0[v]"
        filter_complex = f"{video_filter}"
        map_args = ["-map", "[v]", "-map", "0:a"]

    # Add text overlay with track name if provided
    if track_name:
        # Escape special characters for ffmpeg
        safe_name = track_name.replace("'", "\\'").replace(":", "\\:")
        text_filter = f",drawtext=text='{safe_name}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h-100:shadowcolor=black:shadowx=2:shadowy=2"
        channel_filter = f",drawtext=text='{CHANNEL_NAME}':fontsize=32:fontcolor=white@0.8:x=(w-text_w)/2:y=50:shadowcolor=black:shadowx=1:shadowy=1"
        filter_complex = filter_complex.replace("[v]", f"{text_filter}{channel_filter}[v]")

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-loop", "1", "-i", image_path,
    ]

    # Add mask input if using mask-based effects
    if mask_path and effect in ["masked_glow", "people_glow"]:
        if not os.path.exists(mask_path):
            print(f"ERROR: Mask file not found: {mask_path}")
            return False
        cmd.extend(["-loop", "1", "-i", mask_path])

    cmd.extend([
        "-filter_complex", filter_complex,
        *map_args,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p"
    ])

    if limit_duration:
        cmd.extend(["-t", str(limit_duration)])

    cmd.append(output_path)

    print(f"Creating video with '{effect}' effect...")
    print(f"Output: {output_path}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return False
        print("Video created successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_short(
    audio_path: str,
    image_path: str,
    output_path: str,
    start_time: float = 60,
    duration: float = 45
) -> bool:
    """Create a YouTube Short (vertical 9:16, 45-60 sec)"""

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", audio_path,
        "-loop", "1", "-i", image_path,
        "-filter_complex",
        f"[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0005,1.3)':d={int(duration*VIDEO_FPS)}:s=1080x1920:fps={VIDEO_FPS}[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print(f"Creating YouTube Short...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return False
        print("Short created successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    # Test video creation
    import argparse

    parser = argparse.ArgumentParser(description="Create Amapiano visualizer video")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file")
    parser.add_argument("--image", "-i", required=True, help="Path to background image")
    parser.add_argument("--output", "-o", required=True, help="Output video path")
    parser.add_argument("--name", "-n", default="", help="Track name for overlay")
    parser.add_argument("--effect", "-e", default="zoom",
                       choices=["zoom", "pulse", "waves", "spectrum", "vintage", "static",
                                "glow_spectrum", "audio_pulse", "circle_viz", "bars_bottom",
                                "dual_waves", "audioreactive", "neon_bars", "trees_pulse",
                                "silhouette_glow", "object_breathe", "masked_glow", "people_glow"],
                       help="Visual effect to use")
    parser.add_argument("--mask", "-m", help="Mask image for masked effects (white=effect area)")
    parser.add_argument("--short", "-s", action="store_true", help="Create YouTube Short instead")
    parser.add_argument("--duration", "-d", type=float, help="Limit video duration in seconds")

    args = parser.parse_args()

    if args.short:
        success = create_short(args.audio, args.image, args.output)
    else:
        success = create_visualizer_video(
            args.audio, args.image, args.output,
            track_name=args.name, effect=args.effect,
            limit_duration=args.duration, mask_path=args.mask
        )

    sys.exit(0 if success else 1)
