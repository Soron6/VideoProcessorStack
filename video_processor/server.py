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
    app.run(host='0.0.0.0', port=5000)
