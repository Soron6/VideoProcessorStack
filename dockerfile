# Verwenden des offiziellen Python 3.11 Images
FROM python:3.11

# Setzen des Arbeitsverzeichnisses
WORKDIR /app

# Installieren von ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Kopieren der Abhängigkeitsliste und Installation der Python-Pakete
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren Ihrer Skripte (HTTP-Server und Videoverarbeitung)
COPY *.py ./

# Starten des HTTP-Servers
CMD ["python", "server.py"]
