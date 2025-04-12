#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description="Wrapper for running test_color_quote2.py and other video processing steps.")
    parser.add_argument("--input", required=True,
                        help="Path to input video file (e.g., input/Cat_Animation.mp4)")
    parser.add_argument("--text", required=True, nargs='+',
                        help="One or more text arguments (e.g., 'Es gibt zwei' 'Möglichkeiten, dem' ...)")
    parser.add_argument("--font", required=True,
                        help="Path to the font file (e.g., PatricksHand.ttf)")
    parser.add_argument("--align", required=True,/paws_and_quotes/cats/Intro_Outro/
                        help="Text alignment (e.g., left or right)")
    parser.add_argument("--tag", required=True,
                        help="Tag to create output subfolder (e.g., cats)")
    parser.add_argument("--text_color", required=True,
                        help="Hex color code for text (e.g., #ECEFB8)")
    parser.add_argument("--text_brightness", required=True,
                        help="Text brightness factor (e.g., 0.9)")
    parser.add_argument("--text_saturation", required=True,
                        help="Text saturation factor (e.g., 0.7)")
    parser.add_argument("--drop_shadow", required=True,
                        help="Hex color code for drop shadow (e.g., #4A4C2F)")

    args = parser.parse_args()

    # Build command for test_color_quote2.py using the provided arguments.
    cmd1 = [
        "python", "/data/paws_and_quotes/scripts/test_color_quote2.py",
        "--input", args.input,
        "--font", args.font,
        "--align", args.align,
        "--tag", args.tag,
        "--text_color", args.text_color,
        "--text_brightness", args.text_brightness,
        "--text_saturation", args.text_saturation,
        "--drop_shadow", args.drop_shadow
    ]
    # Append the text arguments after the "--text" flag.
    cmd1.extend(["--text"] + args.text)

    print("[DEBUG] Running test_color_quote2.py with parameters:")
    print(" ".join(cmd1))
    subprocess.run(cmd1, check=True)

    # Run generate_video/02.3_Extendar.py with the corresponding input file.
    cmd2 = [
        "python", "/data/paws_and_quotes/scripts/02.3_Extendar.py",
        "/data/results/temp/quote.mp4"
    ]
    subprocess.run(cmd2, check=True)

    # Run 02.5_concat.py to concatenate video parts./data/results/temp/intro_and_quote.mp4
    cmd3 = [
        "python", "/data/paws_and_quotes/scripts/02.5_concat.py",
        "/data/results/temp/quote.mp4",
        "/data/results/temp/extended_quote.mp4"
    ]
    subprocess.run(cmd3, check=True)

    # Combine intro and quote using 03_combine_intro_and_quote.py.
    cmd4 = [
        "python", "/data/paws_and_quotes/scripts/03_combine_intro_and_quote.py",
        "/paws_and_quotes/cats/Intro_Outro/intro.mp4",
        "quote_complete.mp4"
    ]
    subprocess.run(cmd4, check=True)

    # Add the outro with 04_add_outro.py.
    cmd5 = [
        "python", "/data/paws_and_quotes/scripts/04_add_outro.py",
        "intro_and_quote.mp4",
        "/paws_and_quotes/cats/Intro_Outro/outro.mp4"
    ]
    subprocess.run(cmd5, check=True)

    # Finally, add music using generate_video/05.1_add_music.py.
    cmd6 = [
        "python", "/data/paws_and_quotes/scripts/05.1_add_music.py",
        "--input_video", "full_video.mp4",
        "--music_file", "/paws_and_quotes/cats/Intro_Outro/music.mp3",
        "--output_video", "finalized.mp4"
    ]
    subprocess.run(cmd6, check=True)

if __name__ == "__main__":
    main()
