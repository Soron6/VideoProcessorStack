#!/usr/bin/env python3
"""
Combined Typewriter Animation Script

This script creates a typewriter-style text animation overlay and composites it
onto an input image or video. The canvas for the animation is calculated based on
the input media dimensions (half the width and the same height as the input) and the
specified margins. The script accepts the following parameters:

  --input: Path to input image or video file.
  --text: List of text lines to render.
  --font: (Optional) Path to the font file.
  --align: (Optional) Alignment of the text overlay ("left" or "right"; default: left).
  --tag: (Optional) A tag used to create subfolders for storing output (default: "default").
  --debug: (Optional) Enable debugging messages.
  
Additionally, the following parameters have been added to adjust the text appearance:
  --text_color: Hex color for text (e.g. "#B9E8A8")
  --text_brightness: Brightness factor for text color (e.g. 0.85)
  --text_saturation: Saturation factor for text color (e.g. 0.7)
  --drop_shadow: Hex color for text drop shadow (e.g. "#4A7D3B")

The final output is stored under:
  /results/%tag/pics  for image input and 
  /results/%tag/vids  for video input.
The output filename is generated based on the current timestamp (e.g. 20230407153000.mp4).

Usage example:
  python animate.py --input pic.png --text "Line one" "Line two" --font myfont.ttf --align right --tag dogs --debug --text_color "#B9E8A8" --text_brightness 0.85 --text_saturation 0.7 --drop_shadow "#4A7D3B"
"""

import os
import sys
import argparse
import numpy as np
import colorsys       # For adjusting brightness and saturation
from moviepy import VideoClip, CompositeVideoClip, VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime

# Global debug flag (can be enabled with the --debug argument)
DEBUG = False

def debug(msg):
    if DEBUG:
        print("[DEBUG]", msg)

# Patch for Pillow 10+ compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# Constants for text animation
LETTER_DURATION = 0.125  # Duration in seconds for each letter fade-in
LINE_SPACING = 20        # Vertical spacing between lines in pixels

# ------------------------------------------------------------------------------
# Utility function to convert hex color to an RGB tuple.
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# ------------------------------------------------------------------------------
# Utility function to adjust brightness and saturation.
def adjust_color(rgb, brightness, saturation):
    # Convert RGB (0-255) to HLS (where L is lightness, S is saturation)
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # Adjust brightness (lightness) and saturation
    l = max(0, min(1, l * brightness))
    s = max(0, min(1, s * saturation))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))

# ------------------------------------------------------------------------------
# Helper function: draw_text_with_effects
def draw_text_with_effects(base_image, text, pos, font, opacity=1.0,
                           stroke_width=2, shadow_offset=(3, 3), shadow_opacity=150,
                           text_color=(255, 255, 255), outline_color=(0, 0, 0),
                           drop_shadow=(0, 0, 0), brightness=1.0, saturation=1.0):
    if not text:
        return base_image

    # Adjust the text color based on brightness and saturation
    adjusted_text_color = adjust_color(text_color, brightness, saturation)
    
    # Create a transparent overlay the same size as base_image
    overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw drop shadow using the provided drop_shadow color
    shadow_color = drop_shadow + (int(shadow_opacity * opacity),)
    shadow_pos = (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1])
    draw.text(shadow_pos, text, font=font, fill=shadow_color,
              stroke_width=stroke_width, stroke_fill=shadow_color)
    
    # Apply Gaussian blur to soften the shadow
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Draw the main text with outline on the overlay
    draw = ImageDraw.Draw(overlay)
    main_fill = adjusted_text_color + (int(255 * opacity),)
    main_outline = outline_color + (int(255 * opacity),)
    draw.text(pos, text, font=font, fill=main_fill,
              stroke_width=stroke_width, stroke_fill=main_outline)
    
    # Composite the overlay onto the base image using alpha blending
    combined = Image.alpha_composite(base_image, overlay)
    return combined

# ------------------------------------------------------------------------------
# Helper function: get_text_size
def get_text_size(text, font):
    try:
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return (width, height)
    except Exception:
        return font.getsize(text)

# ------------------------------------------------------------------------------
# Function: make_text_overlay_frame
def make_text_overlay_frame(t, canvas_size, lines, line_timings, line_positions, font,
                            text_color, drop_shadow, brightness, saturation):
    """
    Parameters:
      t: Current time in seconds.
      canvas_size: Tuple (width, height) for the text overlay canvas.
      lines: List of text lines to render.
      line_timings: List of (start, end) times for each line.
      line_positions: List of (x, y) positions for each line.
      font: The ImageFont instance to use.
      text_color: RGB tuple for the text color.
      drop_shadow: RGB tuple for the drop shadow color.
      brightness: Factor to adjust brightness of text color.
      saturation: Factor to adjust saturation of text color.
    Returns:
      A PIL.Image with the text overlay rendered.
    """
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    for i, line in enumerate(lines):
        start, end = line_timings[i]
        pos = line_positions[i]
        if t < start:
            continue
        elif t >= end:
            # Draw the full line with text effects
            canvas = draw_text_with_effects(canvas, line, pos, font,
                                            text_color=text_color,
                                            drop_shadow=drop_shadow,
                                            brightness=brightness,
                                            saturation=saturation)
        else:
            # Determine how many characters to show and the fade-in for the next character
            elapsed = t - start
            n_full = int(elapsed / LETTER_DURATION)
            n_full = min(n_full, len(line))
            full_text = line[:n_full]
            if full_text:
                canvas = draw_text_with_effects(canvas, full_text, pos, font,
                                                text_color=text_color,
                                                drop_shadow=drop_shadow,
                                                brightness=brightness,
                                                saturation=saturation)
            if n_full < len(line):
                fraction = (elapsed - n_full * LETTER_DURATION) / LETTER_DURATION
                offset_x = get_text_size(full_text, font)[0] if full_text else 0
                current_char_pos = (pos[0] + offset_x, pos[1])
                canvas = draw_text_with_effects(canvas, line[n_full], current_char_pos, font,
                                                opacity=fraction,
                                                text_color=text_color,
                                                drop_shadow=drop_shadow,
                                                brightness=brightness,
                                                saturation=saturation)
    return canvas

# ------------------------------------------------------------------------------
# Main processing function: process_media
def process_media(input_path, lines, font_path=None, align="left", tag="default", debug_flag=False,
                  text_color_hex="#FFFFFF", text_brightness=1.0, text_saturation=1.0, drop_shadow_hex="#000000"):
    global DEBUG
    DEBUG = debug_flag
    debug("Starting process_media")

    # Verify input file exists
    if not os.path.exists(input_path):
        print(f"Input file '{input_path}' not found.")
        sys.exit(1)

    # Determine input type from file extension
    ext = os.path.splitext(input_path)[1].lower()
    is_video = ext in [".mp4", ".mov", ".avi", ".mkv"]
    is_image = ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
    if not (is_video or is_image):
        print("Unsupported file type. Supported image types: png, jpg, jpeg, bmp, gif. Supported video types: mp4, mov, avi, mkv.")
        sys.exit(1)
    debug(f"Input file type - Video: {is_video}, Image: {is_image}")

    # Load the base media and get its resolution
    if is_image:
        try:
            base_img = Image.open(input_path).convert("RGBA")
            base_width, base_height = base_img.size
            debug(f"Loaded image with resolution: {base_width}x{base_height}")
        except Exception as e:
            print(f"Error loading image: {e}")
            sys.exit(1)
    else:
        try:
            video_clip = VideoFileClip(input_path)
            base_width, base_height = video_clip.size
            debug(f"Loaded video with resolution: {base_width}x{base_height}, duration: {video_clip.duration}")
        except Exception as e:
            print(f"Error loading video: {e}")
            sys.exit(1)

    # Calculate canvas size: half the base width and the same height
    canvas_width = base_width // 2
    canvas_height = base_height
    canvas_size = (canvas_width, canvas_height)
    debug(f"Calculated text overlay canvas size: {canvas_size}")

    # Define margin (default 20 pixels)
    margin = 20

    # Load the font, using provided path or a default fallback.
    INITIAL_FONT_SIZE = 50
    if font_path is None or not os.path.exists(font_path):
        debug("Font path not provided or not found. Using default 'arial.ttf'.")
        try:
            font = ImageFont.truetype("arial.ttf", INITIAL_FONT_SIZE)
        except Exception as e:
            debug(f"Error loading default font: {e}. Using PIL default font.")
            font = ImageFont.load_default()
    else:
        try:
            font = ImageFont.truetype(font_path, INITIAL_FONT_SIZE)
        except Exception as e:
            debug(f"Error loading font from {font_path}: {e}. Using default PIL font.")
            font = ImageFont.load_default()

    # Scale the font so that the longest text line fits within the canvas (considering margins)
    initial_line_sizes = [get_text_size(line, font) for line in lines]
    max_line_width = max(width for width, _ in initial_line_sizes)
    available_width = canvas_width - 2 * margin
    scale_factor = available_width / max_line_width
    new_font_size = max(1, int(INITIAL_FONT_SIZE * scale_factor))
    debug(f"Scale factor: {scale_factor}, new font size: {new_font_size}")
    try:
        if font_path is None or not os.path.exists(font_path):
            font = ImageFont.truetype("arial.ttf", new_font_size)
        else:
            font = ImageFont.truetype(font_path, new_font_size)
    except Exception as e:
        debug(f"Error reloading font with new size: {e}. Using default PIL font.")
        font = ImageFont.load_default()

    # Calculate the timing for each text line (typewriter effect)
    line_timings = []
    cumulative_time = 0
    for line in lines:
        duration_line = len(line) * LETTER_DURATION
        line_timings.append((cumulative_time, cumulative_time + duration_line))
        cumulative_time += duration_line
    total_duration = cumulative_time
    debug(f"Total animation duration: {total_duration} seconds")

    # Determine text positions on the canvas: center each line horizontally
    line_positions = []
    current_y = margin
    for (w, h) in [get_text_size(line, font) for line in lines]:
        x = (canvas_width - w) // 2
        line_positions.append((x, current_y))
        current_y += h + LINE_SPACING
    debug(f"Calculated text line positions on canvas: {line_positions}")

    # Convert passed hex colors to RGB tuples
    proc_text_color = hex_to_rgb(text_color_hex)
    proc_drop_shadow = hex_to_rgb(drop_shadow_hex)

    # Updated function to generate the text overlay frame.
    def make_overlay_frame(t):
        overlay_img = make_text_overlay_frame(t, canvas_size, lines, line_timings, line_positions, font,
                                                text_color=proc_text_color, drop_shadow=proc_drop_shadow,
                                                brightness=text_brightness, saturation=text_saturation)
        return np.array(overlay_img.convert("RGBA"))

    # Function to composite the text overlay onto the base media frame.
    def make_composite_frame(t):
        overlay_img = Image.fromarray(make_overlay_frame(t))
        if is_image:
            base_frame = base_img.copy()
        else:
            frame = video_clip.get_frame(t)
            base_frame = Image.fromarray(frame).convert("RGBA")
        if align.lower() == "right":
            x_pos = base_width - canvas_width - margin
        else:
            x_pos = margin
        y_pos = margin
        debug(f"At time {t:.2f}s, pasting overlay at position: ({x_pos}, {y_pos})")
        base_frame.paste(overlay_img, (x_pos, y_pos), overlay_img)
        return np.array(base_frame.convert("RGB"))

    # Build output file paths based on tag and media type.
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_results_dir = os.path.join("results", tag)
    output_dir = os.path.join(base_results_dir, "vids" if is_video else "pics")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"{timestamp}.mp4")
    debug(f"Output file will be saved as: {output_filename}")

    # Create the background clip.
    if is_image:
        bg_clip = ImageClip(np.array(base_img.convert("RGBA"))).with_duration(total_duration)
    else:
        if video_clip.duration < total_duration:
            remainder = total_duration - video_clip.duration
            second_last_time = video_clip.duration - (1.0 / video_clip.fps) - 1e-6
            second_last_frame = video_clip.get_frame(second_last_time)
            freeze_clip = ImageClip(second_last_frame).with_duration(remainder)
            bg_clip = concatenate_videoclips([video_clip, freeze_clip])
        else:
            bg_clip = video_clip.subclipped(0, total_duration)

    text_overlay_clip = VideoClip(make_composite_frame, duration=total_duration)
    final_clip = text_overlay_clip.with_fps(24)
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio=(not is_image), threads=1)
    debug("Video creation complete.")
    print(f"Output saved to: {output_filename}")

# ------------------------------------------------------------------------------
# Main: Parse arguments and execute processing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Typewriter Text Animation Overlay on Image/Video\n\n"
                    "This script creates a typewriter-style text animation overlay and composites it onto an "
                    "input image or video. The canvas is set to half the width and full height of the input, with margins. "
                    "Additional parameters allow you to control text color, brightness, saturation, and drop shadow.",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--input", required=True, help="Path to input image or video file")
    parser.add_argument("--text", nargs='+', required=True,
                        help="Text lines to render (each line provided as a separate argument)")
    parser.add_argument("--font", default=None, help="Path to the font file (optional)")
    parser.add_argument("--align", choices=["left", "right"], default="left",
                        help="Alignment of the text overlay on the base (default: left)")
    parser.add_argument("--tag", default="default", help="Tag for output subfolder (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debugging messages")
    # Additional parameters for text styling.
    parser.add_argument("--text_color", default="#FFFFFF", help="Hex color for text (e.g. '#B9E8A8')")
    parser.add_argument("--text_brightness", type=float, default=1.0, help="Brightness factor for text color (e.g. 0.85)")
    parser.add_argument("--text_saturation", type=float, default=1.0, help="Saturation factor for text color (e.g. 0.7)")
    parser.add_argument("--drop_shadow", default="#000000", help="Hex color for text drop shadow (e.g. '#4A7D3B')")
    parser.add_argument("-help", action="help", help="Show this help message and exit.")
    
    args = parser.parse_args()
    process_media(args.input, args.text, font_path=args.font, align=args.align, tag=args.tag,
                  debug_flag=args.debug,
                  text_color_hex=args.text_color,
                  text_brightness=args.text_brightness,
                  text_saturation=args.text_saturation,
                  drop_shadow_hex=args.drop_shadow)