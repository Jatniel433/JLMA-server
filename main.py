from flask import Flask, request, jsonify, Response
import requests
import yt_dlp
import os
import tempfile

app = Flask(__name__)

# Instancias de Invidious para realizar las búsquedas
INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
    "https://invidious.f5.si"
]


@app.route("/")
def inicio():
    return "JMLA Downloader Server funcionando"


# =========================================================
# BUSCAR CANCIONES
# =========================================================

@app.route("/search")
def buscar():
    consulta = request.args.get("q", "").strip()

    if not consulta:
        return jsonify({"resultados": []})

    headers = {
        "User-Agent": "JMLA-Downloader/1.0"
    }

    for instancia in INVIDIOUS_INSTANCES:

        try:
            url = instancia + "/api/v1/search"

            parametros = {
                "q": consulta,
                "page": 1,
                "type": "video",
                "sort": "relevance",
                "region": "DO"
            }

            respuesta = requests.get(
                url,
                params=parametros,
                headers=headers,
                timeout=10
            )

            if respuesta.status_code != 200:
                continue

            datos = respuesta.json()

            resultados = []

            for video in datos:

                if video.get("type") != "video":
                    continue

                video_id = video.get("videoId")

                if not video_id:
                    continue

                titulo = video.get("title", "Sin título")
                artista = video.get("author", "Desconocido")

                # Construimos nosotros mismos la miniatura
                imagen = (
                    "https://i.ytimg.com/vi/"
                    + video_id
                    + "/hqdefault.jpg"
                )

                resultados.append({
                    "titulo": titulo,
                    "artista": artista,
                    "imagen": imagen,
                    "url": "https://www.youtube.com/watch?v=" + video_id
                })

                # Solo queremos 10 resultados
                if len(resultados) >= 10:
                    break

            return jsonify({
                "resultados": resultados
            })

        except Exception as e:
            print("Error con Invidious:", instancia)
            print(e)
            continue

    return jsonify({
        "error": "No se pudo realizar la búsqueda"
    }), 500


# =========================================================
# DESCARGAR MP3
# =========================================================

@app.route("/download", methods=["POST"])
def descargar():

    datos = request.get_json()

    if not datos or "url" not in datos:
        return jsonify({
            "error": "Falta la URL"
        }), 400

    video_url = datos["url"]

    archivo_temporal = tempfile.NamedTemporaryFile(
        suffix=".%(ext)s",
        delete=False
    )

    archivo_temporal.close()

    ruta_salida = archivo_temporal.name

    try:

        opciones = {
            "format": "bestaudio/best",

            "outtmpl": ruta_salida,

            "noplaylist": True,

            "quiet": False,

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

        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([video_url])

        archivo_mp3 = ruta_salida.rsplit(".", 1)[0] + ".mp3"

        if not os.path.exists(archivo_mp3):
            return jsonify({
                "error": "No se pudo crear el MP3"
            }), 500

        with open(archivo_mp3, "rb") as archivo:
            contenido = archivo.read()

        return Response(
            contenido,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=cancion.mp3"
            }
        )

    except Exception as e:

        print("ERROR DESCARGANDO:")
        print(e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Intentamos eliminar archivos temporales
        try:
            if os.path.exists(ruta_salida):
                os.remove(ruta_salida)
        except:
            pass

        try:
            if os.path.exists(
                ruta_salida.rsplit(".", 1)[0] + ".mp3"
            ):
                os.remove(
                    ruta_salida.rsplit(".", 1)[0] + ".mp3"
                )
        except:
            pass