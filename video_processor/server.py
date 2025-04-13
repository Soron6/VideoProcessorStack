from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/create_video', methods=['POST'])
def create_video():
    data = request.json

    # Parameter extrahieren
    input_file = data.get('input_file')
    output_file = data.get('output_file')
    parameters = data.get('parameters', {})

    # Zusammenstellen des ffmpeg-Befehls
    cmd = ['ffmpeg', '-i', input_file]
    for key, value in parameters.items():
        cmd.extend([f'-{key}', value])
    cmd.append(output_file)

    # Ausführen des Befehls (ohne shell=True zur Vermeidung von Injection)
    try:
        subprocess.run(cmd, check=True)
        return jsonify({"status": "success", "output_file": output_file})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/create_video', methods=['POST'])
def create_video():
    data = request.json

    # Extract parameters from JSON payload
    input_file       = data.get('input')           # corresponds to --input
    text             = data.get('text', [])        # corresponds to --text (expecting a list of strings)
    font             = data.get('font')            # corresponds to --font
    align            = data.get('align')           # corresponds to --align
    tag              = data.get('tag')             # corresponds to --tag
    text_color       = data.get('text_color')      # corresponds to --text_color
    text_brightness  = data.get('text_brightness') # corresponds to --text_brightness
    text_saturation  = data.get('text_saturation') # corresponds to --text_saturation
    drop_shadow      = data.get('drop_shadow')     # corresponds to --drop_shadow

    # Build the command that calls /data/paws_and_quotes/scripts/GENERATE_IT.py
    cmd = ['python', '/data/paws_and_quotes/scripts/GENERATE_IT.py']

    if input_file:
        cmd.extend(["--input", input_file])
    if text:
        # Expect text to be a list; if not, convert it into a list
        if not isinstance(text, list):
            text = [text]
        cmd.append("--text")
        cmd.extend(text)
    if font:
        cmd.extend(["--font", font])
    if align:
        cmd.extend(["--align", align])
    if tag:
        cmd.extend(["--tag", tag])
    if text_color:
        cmd.extend(["--text_color", text_color])
    if text_brightness:
        cmd.extend(["--text_brightness", str(text_brightness)])
    if text_saturation:
        cmd.extend(["--text_saturation", str(text_saturation)])
    if drop_shadow:
        cmd.extend(["--drop_shadow", drop_shadow])

    # Debug: print the full command line
    print("Running command:", " ".join(cmd))
    
    # Execute the command via subprocess without using shell=True to avoid injection issues.
    try:
        subprocess.run(cmd, check=True)
        return jsonify({"status": "success", "command": " ".join(cmd)})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


