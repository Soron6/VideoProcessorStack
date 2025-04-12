#!/usr/bin/env python3
import sys
import subprocess
import os
import tempfile

def main():
    if len(sys.argv) != 3:
        print("Usage: {} <video_file1> <video_file2>".format(sys.argv[0]))
        sys.exit(1)
    
    video1 = sys.argv[1]
    video2 = sys.argv[2]
    
    # Check if both files exist
    if not os.path.isfile(video1):
        print(f"Error: File '{video1}' does not exist.")
        sys.exit(1)
    if not os.path.isfile(video2):
        print(f"Error: File '{video2}' does not exist.")
        sys.exit(1)
    
    # Create a temporary file list for ffmpeg concat demuxer
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        # Writing the absolute paths inside the file list
        f.write("file '{}'\n".format(os.path.abspath(video1)))
        f.write("file '{}'\n".format(os.path.abspath(video2)))
        list_file = f.name

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",                  # Overwrite output if exists
        "-f", "concat",
        "-safe", "0",          # Allow unsafe file paths
        "-i", list_file,
        "-c", "copy",          # Copy streams without re-encoding
        "quote_complete.mp4"
    ]
    
    print("Running command:")
    print(" ".join(ffmpeg_cmd))
    
    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print("Error during concatenation:")
        print(proc.stderr)
        sys.exit(1)
    else:
        print("Concatenation completed successfully. Output saved as 'quote_complete.mp4'")
    
    # Clean up the temporary file
    os.remove(list_file)

if __name__ == "__main__":
    main()