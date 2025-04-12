#!/usr/bin/env python3
import subprocess

def main():
    # Execute test_color_quote2.py with the provided arguments
    cmd1 = [
        "python", "test_color_quote2.py",
        "--input", "input/Cat_Animation.mp4",
        "--text", "Es gibt zwei", "Möglichkeiten, dem", "Elend der Welt", "zu entfliehen:", "die Musik", "und die Katzen.",
        "--font", "PatricksHand.ttf",
        "--align", "left",
        "--tag", "cats",
        "--text_color", "#ECEFB8",
        "--text_brightness", "0.9",
        "--text_saturation", "0.7",
        "--drop_shadow", "#4A4C2F"
    ]
    subprocess.run(cmd1, check=True)

    # Run generate_video/02.3_Extendar.py with the corresponding input file
    cmd2 = [
        "python", "generate_video/02.3_Extendar.py",
        "results/cats/vids/20250412095817.mp4"
    ]
    subprocess.run(cmd2, check=True)

    # Run 02.5_concat.py to concatenate video parts
    cmd3 = [
        "python", "02.5_concat.py",
        "results/cats/vids/20250412095817.mp4",
        "output.mp4"
    ]
    subprocess.run(cmd3, check=True)

    # Combine intro and quote using 03_combine_intro_and_quote.py
    cmd4 = [
        "python", "03_combine_intro_and_quote.py",
        "generate_video/_cats/intro_outro/intro.mp4",
        "quote_complete.mp4"
    ]
    subprocess.run(cmd4, check=True)

    # Add the outro with 04_add_outro.py
    cmd5 = [
        "python", "04_add_outro.py",
        "intro_and_quote.mp4",
        "generate_video/_cats/intro_outro/outro.mp4"
    ]
    subprocess.run(cmd5, check=True)

    # Finally, add music using generate_video/05.1_add_music.py
    cmd6 = [
        "python", "generate_video/05.1_add_music.py",
        "--input_video", "full_video.mp4",
        "--music_file", "generate_video/_cats/intro_outro/music.mp3",
        "--output_video", "finalized.mp4"
    ]
    subprocess.run(cmd6, check=True)

if __name__ == "__main__":
    main()