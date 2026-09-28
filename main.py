from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@app.route("/")
def inicio():
    return jsonify({
        "status": "ok",
        "server": "JMLA Downloader"
    })


@app.route("/download", methods=["POST"])
def download():

    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "error": "Falta la URL"
        }), 400

    url = data["url"]

    nombre = str(uuid.uuid4())

    salida = os.path.join(
        DOWNLOAD_DIR,
        nombre + ".%(ext)s"
    )

    opciones = {
        "format": "bestaudio/best",
        "outtmpl": salida,
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ]
    }

    try:

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)

        archivo = os.path.join(
            DOWNLOAD_DIR,
            nombre + ".mp3"
        )

        if not os.path.exists(archivo):
            return jsonify({
                "error": "No se pudo crear el MP3"
            }), 500

        return send_file(
            archivo,
            as_attachment=True,
            download_name=info.get("title", "cancion") + ".mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":

    puerto = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=puerto
    )