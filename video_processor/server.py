import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/create_video', methods=['POST'])
def create_video():
    data = request.json
    print("Received JSON:", data)  # Log the payload

    # Extract parameters from JSON payload
    input_file      = data.get('input')           # corresponds to --input
    text            = data.get('text', [])        # corresponds to --text (expecting a list)
    font            = data.get('font')            # corresponds to --font
    align           = data.get('align')           # corresponds to --align
    tag             = data.get('tag')             # corresponds to --tag
    text_color      = data.get('text_color')      # corresponds to --text_color
    text_brightness = data.get('text_brightness') # corresponds to --text_brightness
    text_saturation = data.get('text_saturation') # corresponds to --text_saturation
    drop_shadow     = data.get('drop_shadow')     # corresponds to --drop_shadow

    # Build the command that calls the script
    cmd = ['python', '/data/paws_and_quotes/scripts/GENERATE_IT.py']
    if input_file:
        cmd.extend(["--input", input_file])
    if text:
        # Make sure text is a list
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

    # Debug: log the full command line
    command_str = " ".join(cmd)
    print("Running command:", command_str)
    
    try:
        # Capture stdout and stderr
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Command stdout:", result.stdout)
        print("Command stderr:", result.stderr)
        return jsonify({"status": "success", "command": command_str})
    except subprocess.CalledProcessError as e:
        # Log detailed error information for troubleshooting
        print("Command failed with return code:", e.returncode)
        print("Command stdout:", e.stdout)
        print("Command stderr:", e.stderr)
        return jsonify({
            "status": "error",
            "message": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500

if __name__ == '__main__':
    # Consider running in debug mode for development:
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

