#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def get_video_duration(video_file):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        duration_str = result.stdout.strip()
        print("[DEBUG] ffprobe duration output:", duration_str)
        return float(duration_str)
    except Exception as e:
        print(f"Error getting duration of {video_file}: {e}")
        sys.exit(1)

def add_audio_to_video(input_video, music_file, output_video, fade_duration=2.0):
    # Get the duration of the input video in seconds
    video_duration = get_video_duration(input_video)
    # Calculate when the fade should start (video_duration - fade_duration)
    fade_start = video_duration - fade_duration
    print(f"[DEBUG] Video duration: {video_duration} seconds. Audio fade-out will start at: {fade_start} seconds.")

    # Build the filter_complex to trim the audio to video's duration and fade out the audio in the last seconds.
    filter_complex = (
        f"[1:a]atrim=duration={video_duration},"
        f"afade=t=out:st={fade_start}:d={fade_duration}[a]"
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-i", music_file,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",  # Copy video stream without re-encoding.
        "-shortest",     # Stop when the shortest stream ends.
        output_video
    ]

    print("[DEBUG] Running ffmpeg with the following command:")
    print(" ".join(ffmpeg_cmd))
    
    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print("Error running ffmpeg command:")
        print(proc.stderr)
        sys.exit(1)
    else:
        print("[DEBUG] ffmpeg output:", proc.stdout)
        print("Finished:", output_video)

def main():
    parser = argparse.ArgumentParser(description="Add an audio track with fade-out effect to a video.")
    parser.add_argument('--input_video', '-v', type=str, required=True,
                        help="Path to the input video file.")
    parser.add_argument('--music_file', '-a', type=str, required=True,
                        help="Path to the input audio/music file.")
    parser.add_argument('--output_video', '-o', type=str, required=True,
                        help="Path where the output video will be saved.")
    parser.add_argument('--fade_duration', '-f', type=float, default=2.0,
                        help="Duration in seconds for the audio fade-out (default: 2.0 seconds).")
    
    args = parser.parse_args()
    
    # Basic file existence check
    if not os.path.exists(args.input_video):
        print(f"Error: Input video file '{args.input_video}' does not exist.")
        sys.exit(1)
    if not os.path.exists(args.music_file):
        print(f"Error: Audio file '{args.music_file}' does not exist.")
        sys.exit(1)
    
    add_audio_to_video(args.input_video, args.music_file, args.output_video, args.fade_duration)

if __name__ == "__main__":
    main()