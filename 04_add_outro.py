#!/usr/bin/env python3
import subprocess
import sys
import json

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
        print("[DEBUG] ffprobe Dauer Ausgabe:", duration_str)
        return float(duration_str)
    except Exception as e:
        print(f"Fehler beim Ermitteln der Dauer von {video_file}: {e}")
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
        print("[DEBUG] ffprobe Auflösungs Ausgabe:", result.stdout)
        info = json.loads(result.stdout)
        streams = info.get("streams")
        if not streams or len(streams) == 0:
            print(f"Keine Videostreams in {video_file} gefunden.")
            sys.exit(1)
        stream = streams[0]
        width = int(stream["width"])
        height = int(stream["height"])
        print(f"[DEBUG] Ermittelte Auflösung: {width}x{height}")
        return width, height
    except Exception as e:
        print(f"Fehler beim Ermitteln der Auflösung von {video_file}: {e}")
        sys.exit(1)

def run_ffmpeg(video1, video2, part1_end, width, height, fps):
    # Parameter für den Übergang:
    transition_duration = 1.5

    # Für die harte Kante von Video 02 (Vordergrund)
    fgmask_expr = f"if(lt(X,((T/{transition_duration})*{width})),255,0)"

    # Parameter für den weißen Balken:
    white_bar_width = 40            # Basiskomponente (rechts des Balkens)
    white_feather = 60              # Rechtsseitiges Fade-Out des Balkens
    white_bar_extension = 100       # Zusätzliche Ausdehnung des Balkens nach links
    total_left_gradient = white_bar_width + white_bar_extension
    fadeout_duration = 0.3          # Dauer des Fade-Outs (rechts des Balkens)

    white_mask_expr = (
        f"if(lt(X,((T/{transition_duration})*{width}-{total_left_gradient})),0,"  # links transparent
        f"if(lt(X,((T/{transition_duration})*{width})),"
        f"255*((X-((T/{transition_duration})*{width}-{total_left_gradient}))/ {total_left_gradient}),"
        f"if(lt(X,((T/{transition_duration})*{width}+{white_feather})),"
        f"255*((((T/{transition_duration})*{width}+{white_feather})-X)/{white_feather}),0)))"
    )
    
    fade_expr = (
        f"if(lt(T,{transition_duration - fadeout_duration}),255,"
        f"255*(({transition_duration}-T)/{fadeout_duration}))"
    )
    white_alpha_expr = f"({white_mask_expr})*({fade_expr})/255"

    filter_complex = (
        # 01.mp4 in zwei Segmente teilen: part1 (unverändert) und part2 (Übergangssegment)
        f"[0:v]trim=duration={part1_end},setpts=PTS-STARTPTS,scale={width}:{height},format=rgba[part1]; "
        f"[0:v]trim=start={part1_end}:duration={transition_duration},setpts=PTS-STARTPTS,scale={width}:{height},format=rgba[part2]; "
        # 02.mp4 in zwei Segmente teilen: intro2 (für Übergang) und rest2 (Rest)
        f"[1:v]trim=duration={transition_duration},setpts=PTS-STARTPTS,scale={width}:{height},format=rgba[intro2]; "
        f"[1:v]trim=start={transition_duration},setpts=PTS-STARTPTS,scale={width}:{height},format=rgba[rest2]; "
        # Übergangssegmente vorbereiten:
        f"[part2]setpts=PTS-STARTPTS[bg_trans]; "
        f"[intro2]setpts=PTS-STARTPTS[fg_trans]; "
        f"nullsrc=size={width}x{height}:duration={transition_duration}:rate={fps}[base]; "
        # Erzeugen der harten Maske für Video 02:
        f"[base]geq=lum='{fgmask_expr}':a='{fgmask_expr}'[mask_fg_tmp]; "
        f"[mask_fg_tmp]format=gray[mask_fg]; "
        f"[fg_trans][mask_fg]alphamerge[fg_applied]; "
        # Erzeugen der weißen Fläche:
        f"color=white:s={width}x{height}:d={transition_duration}:r={fps}[white]; "
        # Erzeugen der Maske für den weißen Balken:
        f"[base]geq=lum='{white_alpha_expr}':a='{white_alpha_expr}'[mask_white_tmp]; "
        f"[mask_white_tmp]format=gray[mask_white]; "
        f"[white][mask_white]alphamerge[white_bar]; "
        # Zusammensetzen: Overlay von Video 02 (maskiert) über Video 01:
        f"[bg_trans][fg_applied]overlay=shortest=1:format=auto[tmp]; "
        # Overlay des weißen Balkens:
        f"[tmp][white_bar]overlay=shortest=1:format=auto[transition]; "
        # Verkettung: part1 (unverändert 01.mp4) + Übergang + rest2 (ab 1.5s 02.mp4):
        f"[part1][transition][rest2]concat=n=3:v=1:a=0[outv]"
    )
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-loglevel", "debug",
        "-i", video1,
        "-i", video2,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-an",
        "full_video.mp4"
    ]
    
    print("[DEBUG] Starte FFmpeg mit folgendem Befehl:")
    print(" ".join(ffmpeg_cmd))
    
    proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print("FEHLER bei FFmpeg:")
        print(proc.stderr)
        sys.exit(1)
    else:
        print("[DEBUG] FFmpeg Ausgabe:", proc.stdout)
        print("Fertig: output.mp4")

def main():
    if len(sys.argv) != 3:
        print("Usage: {} <first_video_file> <second_video_file>".format(sys.argv[0]))
        sys.exit(1)
    
    video1 = sys.argv[1]
    video2 = sys.argv[2]
    
    print("[DEBUG] Starte Analyse von", video1)
    duration = get_video_duration(video1)
    print("[DEBUG] Dauer von", video1, ":", duration, "Sekunden")
    
    width, height = get_video_resolution(video1)
    transition_duration = 1.5
    if duration <= transition_duration:
        print(f"{video1} ist zu kurz für den Übergang.")
        sys.exit(1)
    
    part1_end = duration - transition_duration
    fps = 24
    print("[DEBUG] part1_end:", part1_end, "Sekunden, FPS:", fps)
    run_ffmpeg(video1, video2, part1_end, width, height, fps)

if __name__ == "__main__":
    main()