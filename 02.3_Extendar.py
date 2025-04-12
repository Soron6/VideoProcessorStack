#!/usr/bin/env python3
import subprocess
import sys
import json
import math

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

def get_video_resolution(video_file):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json",
                video_file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("[DEBUG] ffprobe resolution output:", result.stdout)
        info = json.loads(result.stdout)
        streams = info.get("streams")
        if not streams or len(streams) == 0:
            print(f"No video streams found in {video_file}.")
            sys.exit(1)
        stream = streams[0]
        width = int(stream["width"])
        height = int(stream["height"])
        print(f"[DEBUG] Resolution: {width}x{height}")
        return width, height
    except Exception as e:
        print(f"Error getting resolution of {video_file}: {e}")
        sys.exit(1)

def extract_second_last_frame(video_file, fps):
    duration = get_video_duration(video_file)
    extract_time = duration - (2 / fps)
    if extract_time < 0:
        print("Video is too short to extract the second last frame.")
        sys.exit(1)
    print(f"[DEBUG] Extraction time for second last frame: {extract_time} seconds")
    out_image = "second_last.png"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-ss", str(extract_time),
        "-i", video_file,
        "-vframes", "1",
        out_image
    ]
    print("[DEBUG] Running ffmpeg to extract frame:")
    print(" ".join(ffmpeg_cmd))
    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print("Error extracting second last frame:")
        print(proc.stderr)
        sys.exit(1)
    else:
        print(f"[DEBUG] Extracted frame saved as {out_image}")
    return out_image

def run_ffmpeg(still_image, diag, line_thickness, fps):
    """
    Creates an animated overlay (a white, blurred bar) on the still image.
    In this modified version:
      - The overall video duration is 4 seconds.
      - The overlay animation starts at 0.75 seconds and lasts for 0.75 seconds (until 1.5 seconds).
      - The parts before and after the animation remain in the final 4-second video.
    """
    half_th = line_thickness  
    center_x = diag / 2.0

    # Blur settings for a smoother edge on the white bar.
    blur_x = 20
    blur_y = 20

    # The filter_complex creates the animation.
    # 1. The white bar is generated from a color source of dimensions diag x diag.
    # 2. The 'geq' filter paints a vertical white strip at the horizontal center,
    #    where the alpha channel is 255 (opaque) for pixels within half_th distance from center_x,
    #    and 0 (transparent) elsewhere.
    # 3. The strip is softened with a boxblur.
    # 4. It is then rotated by 135° (2.35619 radians) so that it is perpendicular to the motion path.
    # 5. The overlay is animated with a quadratic easing function, moving from off-screen on the left-bottom
    #    to the top-right over the time interval t=0.75 to t=1.5.
    filter_complex = (
        f"[1:v]format=rgba,"
        # Create a vertical white strip at the horizontal center.
        f"geq=r='255':g='255':b='255':"
        f"a='if( lt(abs(X-{center_x}),{half_th}), 255, 0 )',"
        f"boxblur={blur_x}:{blur_y},"
        # Rotate 135° (2.35619 radians) to align the strip along the diagonal.
        f"rotate=2.35619:ow=rotw(iw):oh=roth(ih):c=0x00000000[feathered_line]; "

        f"[0:v]format=rgba[base]; "
        f"[base][feathered_line]overlay="
        # Animate using quadratic easing:
        # The x offset moves from -overlay_w (left off-screen) to main_w (right off-screen)
        # and the y offset moves from main_h (bottom off-screen) to -overlay_h (top off-screen)
        # during the period between t=0.75 and t=1.5 seconds.
        f"x='-overlay_w+(main_w+overlay_w)*(((t-0.75)/0.75)^2)':"
        f"y='main_h-(main_h+overlay_h)*(((t-0.75)/0.75)^2)':"
        f"enable='between(t,0.75,1.5)'[out]"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        # The still image (background) is looped for 4 seconds.
        "-loop", "1",
        "-t", "4",
        "-i", still_image,
        "-f", "lavfi",
        # Generate the white color overlay video,
        # now with duration d=0.75 seconds to match the animation timing.
        "-i", f"color=white:s={diag}x{diag}:d=0.75:rate={fps}",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "output.mp4"
    ]

    print("[DEBUG] Running ffmpeg to create final output:")
    print(" ".join(ffmpeg_cmd))
    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print("Error running final ffmpeg command:")
        print(proc.stderr)
        sys.exit(1)
    else:
        print("[DEBUG] ffmpeg output:", proc.stdout)
        print("Finished: output.mp4")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <video_file>")
        sys.exit(1)
    input_video = sys.argv[1]
    fps = 24
    print("[DEBUG] Analyzing video:", input_video)
    width, height = get_video_resolution(input_video)

    still_image = extract_second_last_frame(input_video, fps)
    
    diag = int(math.ceil(math.sqrt(width**2 + height**2)))
    print(f"[DEBUG] Computed diagonal: {diag}")

    line_thickness = 20
    run_ffmpeg(still_image, diag, line_thickness, fps)

if __name__ == "__main__":
    main()