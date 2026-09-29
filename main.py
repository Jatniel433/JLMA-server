from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ==========================================
# INICIO DEL SERVIDOR
# ==========================================

@app.route("/")
def inicio():

    return jsonify({
        "status": "ok",
        "server": "JMLA Downloader"
    })


# ==========================================
# BUSCAR CANCIONES
# ==========================================

@app.route("/search", methods=["GET"])
def buscar():

    consulta = request.args.get("q")

    if not consulta:
        return jsonify({
            "error": "Falta la búsqueda"
        }), 400

    opciones = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "noplaylist": True,
        "js_runtimes": {
            "deno": {}
        }
    }

    try:

        with yt_dlp.YoutubeDL(opciones) as ydl:

            resultados = ydl.extract_info(
                "ytsearch10:" + consulta,
                download=False
            )

        canciones = []

        for video in resultados.get("entries", []):

            if not video:
                continue

            canciones.append({

                "titulo": video.get(
                    "title",
                    "Sin título"
                ),

                "artista": video.get(
                    "channel",
                    video.get(
                        "uploader",
                        "Desconocido"
                    )
                ),

                "imagen": video.get(
                    "thumbnail",
                    ""
                ),

                "url": video.get(
                    "webpage_url",
                    video.get(
                        "url",
                        ""
                    )
                )
            })

        return jsonify({
            "resultados": canciones
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# DESCARGAR CANCION
# ==========================================

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

        "js_runtimes": {
            "deno": {}
        },

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

            info = ydl.extract_info(
                url,
                download=True
            )

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

            download_name=info.get(
                "title",
                "cancion"
            ) + ".mp3",

            mimetype="audio/mpeg"
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# EJECUTAR SERVIDOR
# ==========================================

if __name__ == "__main__":

    puerto = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=puerto
    )