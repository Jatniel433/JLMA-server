from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid


app = Flask(__name__)


# ==========================================
# CARPETA DE DESCARGAS
# ==========================================

DOWNLOAD_DIR = "/tmp/downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# ==========================================
# PAGINA PRINCIPAL
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

        # No descargar el vídeo
        "skip_download": True,

        # Buscar resultados sin intentar
        # extraer todos sus datos
        "extract_flat": True,

        # No buscar listas de reproducción
        "noplaylist": True,

        # Si un resultado falla,
        # continuar con los demás
        "ignoreerrors": True,

        # Mantener silencioso el servidor
        "quiet": True,

        # Usar Deno para los desafíos
        # de JavaScript de YouTube
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


        if not resultados:

            return jsonify({

                "resultados": []

            })


        entradas = resultados.get(
            "entries",
            []
        )


        for video in entradas:

            # Algunos resultados pueden
            # venir vacíos si YouTube
            # los bloquea.
            if not video:
                continue


            video_id = video.get("id")


            if not video_id:
                continue


            titulo = video.get(

                "title",

                "Sin título"

            )


            artista = video.get(

                "channel",

                video.get(

                    "uploader",

                    "Desconocido"

                )

            )


            # ==================================
            # MINIATURA
            # ==================================

            imagen = (

                "https://i.ytimg.com/vi/"

                + video_id

                + "/hqdefault.jpg"

            )


            # ==================================
            # URL DEL VIDEO
            # ==================================

            url = (

                "https://www.youtube.com/watch?v="

                + video_id

            )


            canciones.append({

                "titulo": titulo,

                "artista": artista,

                "imagen": imagen,

                "url": url

            })


        return jsonify({

            "resultados": canciones

        })


    except Exception as e:

        # IMPORTANTE:
        #
        # Si YouTube devuelve 429 o bloquea
        # una consulta, no queremos que
        # la aplicación se caiga.
        #
        # Devolvemos una respuesta válida
        # al Android.

        print(
            "ERROR EN BUSQUEDA:",
            str(e)
        )


        return jsonify({

            "resultados": [],

            "error": (
                "YouTube no permitió realizar "
                "la búsqueda en este momento."
            )

        })


# ==========================================
# DESCARGAR CANCION
# ==========================================

@app.route("/download", methods=["POST"])
def descargar():

    data = request.get_json()


    if not data:

        return jsonify({

            "error": "No se recibieron datos"

        }), 400


    if "url" not in data:

        return jsonify({

            "error": "Falta la URL"

        }), 400


    url = data["url"]


    if not url:

        return jsonify({

            "error": "La URL está vacía"

        }), 400


    # ==========================================
    # NOMBRE TEMPORAL
    # ==========================================

    nombre = str(
        uuid.uuid4()
    )


    salida = os.path.join(

        DOWNLOAD_DIR,

        nombre + ".%(ext)s"

    )


    # ==========================================
    # OPCIONES DE YT-DLP
    # ==========================================

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

                "key":
                    "FFmpegExtractAudio",

                "preferredcodec":
                    "mp3",

                "preferredquality":
                    "192"

            }

        ]

    }


    try:

        with yt_dlp.YoutubeDL(
            opciones
        ) as ydl:

            info = ydl.extract_info(

                url,

                download=True

            )


        # ==========================================
        # COMPROBAR MP3
        # ==========================================

        archivo = os.path.join(

            DOWNLOAD_DIR,

            nombre + ".mp3"

        )


        if not os.path.exists(archivo):

            return jsonify({

                "error":
                    "No se pudo crear el MP3"

            }), 500


        # ==========================================
        # NOMBRE DE LA CANCION
        # ==========================================

        titulo = info.get(

            "title",

            "cancion"

        )


        # Evitar caracteres problemáticos
        # en el nombre del archivo

        caracteres_invalidos = [

            "/",
            "\\",
            ":",
            "*",
            "?",
            "\"",
            "<",
            ">",
            "|"

        ]


        for caracter in caracteres_invalidos:

            titulo = titulo.replace(
                caracter,
                "_"
            )


        # ==========================================
        # ENVIAR MP3
        # ==========================================

        return send_file(

            archivo,

            as_attachment=True,

            download_name=
                titulo + ".mp3",

            mimetype=
                "audio/mpeg"

        )


    except Exception as e:

        print(
            "ERROR EN DESCARGA:",
            str(e)
        )


        return jsonify({

            "error": str(e)

        }), 500


# ==========================================
# SERVIDOR
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