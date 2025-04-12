#!/usr/bin/env python3
import subprocess
import sys
import json

def get_video_duration(video_file):
    """
    Ermittelt die Dauer des Videos (in Sekunden) mithilfe von ffprobe.
    """
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
        duration = float(duration_str)
        return duration
    except Exception as e:
        print(f"Fehler beim Ermitteln der Dauer von {video_file}: {e}")
        sys.exit(1)

def get_video_resolution(video_file):
    """
    Ermittelt die Auflösung eines Videos (Breite und Höhe) mithilfe von ffprobe.
    """
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
        info = json.loads(result.stdout)
        stream = info.get("streams", [{}])[0]
        width = int(stream.get("width", 0))
        height = int(stream.get("height", 0))
        if width == 0 or height == 0:
            raise ValueError("Auflösung konnte nicht ermittelt werden.")
        return width, height
    except Exception as e:
        print(f"Fehler beim Ermitteln der Auflösung von {video_file}: {e}")
        sys.exit(1)

def run_ffmpeg(video1, video2, offset, width, height, fps):
    """
    Führt den ffmpeg-Befehl aus, um die beiden Videos mit einem kreisförmigen
    Übergang (circleopen) zusammenzufügen.

    Dabei werden beide Eingangsströme zuerst auf die gewünschte Auflösung (width x height)
    skaliert, ins Format yuv420p konvertiert, die Zeitstempel zurückgesetzt und der Frame‑Rate
    mittels fps‑Filter (z. B. 24 fps) fixiert.
    
    Der Filtergraph lautet:
      [0:v]scale={w}:{h},format=yuv420p,setpts=PTS-STARTPTS,fps=fps={fps}[va];
      [1:v]scale={w}:{h},format=yuv420p,setpts=PTS-STARTPTS,fps=fps={fps}[vb];
      [va][vb]xfade=transition=circleopen:duration=3:offset={offset}[tmp];
      [tmp]format=yuv420p[vout]
    
    Zusätzlich wird der globale Parameter -pix_fmt yuv420p gesetzt.
    """
    filter_chain = (
        f"[0:v]scale={width}:{height},format=yuv420p,setpts=PTS-STARTPTS,fps=fps={fps}[va]; "
        f"[1:v]scale={width}:{height},format=yuv420p,setpts=PTS-STARTPTS,fps=fps={fps}[vb]; "
        f"[va][vb]xfade=transition=circleopen:duration=3:offset={offset}[tmp]; "
        f"[tmp]format=yuv420p[vout]"
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",                           # vorhandene Dateien überschreiben
        "-loglevel", "debug",           # ausführliches Logging
        "-i", video1,
        "-i", video2,
        "-filter_complex", filter_chain,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",          # globale Einstellung, um yuv420p sicherzustellen
        "-an",                         # keine Audioverarbeitung
        "intro_and_quote.mp4"
    ]
    
    print("Starte ffmpeg mit folgendem Befehl:")
    print(" ".join(ffmpeg_cmd))
    
    try:
        proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("===== ffmpeg STDOUT =====")
        print(proc.stdout)
        print("===== ffmpeg STDERR =====")
        print(proc.stderr)
        
        if proc.returncode != 0:
            print(f"ffmpeg returned with Fehlercode {proc.returncode}")
            sys.exit(1)
        else:
            print("Das Ausgabevideo wurde als 'output.mp4' gespeichert.")
            
    except Exception as e:
        print("Fehler bei der Ausführung von ffmpeg:")
        print(e)
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: {} <first_video_file> <second_video_file>".format(sys.argv[0]))
        sys.exit(1)

    video1 = sys.argv[1]
    video2 = sys.argv[2]

    duration = get_video_duration(video1)
    print(f"Dauer von {video1}: {duration:.2f} Sekunden")
    
    width, height = get_video_resolution(video1)
    print(f"Auflösung von {video1}: {width}x{height}")
    
    # Für die Übergangsdauer
    transition_duration = 3.0
    if duration <= transition_duration:
        print("Fehler: Das erste Video muss länger als 3 Sekunden sein, um den Übergang zu ermöglichen.")
        sys.exit(1)
    
    # Der Übergang soll so platziert werden, dass er am Ende von video1 endet.
    offset = duration - transition_duration
    print(f"Berechneter Offset für den Übergang: {offset:.2f} Sekunden")
    
    # Annahme: Beide Videos haben 24 fps (aus dem ffprobe-Output erkennbar)
    fps = 24
    run_ffmpeg(video1, video2, offset, width, height, fps)

if __name__ == "__main__":
    main()
