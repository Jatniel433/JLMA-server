from flask import Flask, request, jsonify, send_file

import yt_dlp

import os
import uuid

import json
import urllib.parse
import urllib.request


app = Flask(__name__)


# ==========================================
# CARPETA TEMPORAL
# ==========================================

DOWNLOAD_DIR = "/tmp/downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# ==========================================
# INSTANCIAS INVIDIOUS
# ==========================================
#
# El buscador probará una instancia.
# Si falla, probará la siguiente.
#
# Estas son instancias que aparecen
# actualmente en la lista oficial de
# Invidious.
#
# ==========================================

INVIDIOUS_INSTANCES = [

    "https://inv.nadeko.net",

    "https://invidious.nerdvpn.de",

    "https://yt.chocolatemoo53.com",

    "https://invidious.tiekoetter.com",

    "https://invidious.f5.si"

]


# ==========================================
# PAGINA PRINCIPAL
# ==========================================

@app.route("/")
def inicio():

    return jsonify({

        "status": "ok",

        "server": "JMLA Downloader",

        "search": "Invidious",

        "download": "yt-dlp"

    })


# ==========================================
# BUSCAR CANCIONES
# ==========================================
#
# IMPORTANTE:
#
# YA NO UTILIZAMOS yt-dlp PARA BUSCAR.
#
# La búsqueda se hace mediante la API
# pública de Invidious.
#
# ==========================================

@app.route("/search", methods=["GET"])
def buscar():

    consulta = request.args.get("q")


    # ------------------------------------------
    # Comprobar búsqueda
    # ------------------------------------------

    if not consulta:

        return jsonify({

            "error": "Falta la búsqueda"

        }), 400


    consulta = consulta.strip()


    if not consulta:

        return jsonify({

            "error": "La búsqueda está vacía"

        }), 400


    # ==========================================
    # PROBAR INSTANCIAS
    # ==========================================

    ultimo_error = "No se pudo conectar con Invidious"


    for instancia in INVIDIOUS_INSTANCES:

        try:

            # ----------------------------------
            # Parámetros de búsqueda
            # ----------------------------------

            parametros = {

                "q": consulta,

                "page": "1",

                "type": "video",

                "sort": "relevance",

                "region": "DO"

            }


            # ----------------------------------
            # Crear URL
            # ----------------------------------

            url = (

                instancia

                + "/api/v1/search?"

                + urllib.parse.urlencode(
                    parametros
                )

            )


            print(
                "BUSCANDO EN:",
                instancia
            )


            # ----------------------------------
            # Solicitud
            # ----------------------------------

            solicitud = urllib.request.Request(

                url,

                headers={

                    "User-Agent":
                        "JMLA-Downloader/1.0"

                }

            )


            with urllib.request.urlopen(

                solicitud,

                timeout=12

            ) as respuesta:

                contenido = respuesta.read().decode(
                    "utf-8"
                )


            datos = json.loads(
                contenido
            )


            # ----------------------------------
            # Comprobar que recibimos una lista
            # ----------------------------------

            if not isinstance(
                datos,
                list
            ):

                ultimo_error = (
                    "Respuesta inválida de "
                    + instancia
                )

                continue


            # ==================================
            # CONVERTIR RESULTADOS
            # ==================================

            canciones = []


            for resultado in datos:

                # Solo queremos videos
                if resultado.get("type") != "video":

                    continue


                video_id = resultado.get(
                    "videoId"
                )


                if not video_id:

                    continue


                titulo = resultado.get(

                    "title",

                    "Sin título"

                )


                artista = resultado.get(

                    "author",

                    "Desconocido"

                )


                # ==================================
                # MINIATURA
                # ==================================

                miniaturas = resultado.get(

                    "videoThumbnails",

                    []

                )


                imagen = ""


                # Preferimos calidad alta
                for miniatura in miniaturas:

                    calidad = miniatura.get(
                        "quality",
                        ""
                    )

                    if calidad in [
                        "maxres",
                        "maxresdefault",
                        "high"
                    ]:

                        imagen = miniatura.get(
                            "url",
                            ""
                        )

                        if imagen:

                            break


                # Si no encontramos una de alta
                # calidad, utilizamos cualquiera.

                if not imagen:

                    for miniatura in miniaturas:

                        imagen = miniatura.get(
                            "url",
                            ""
                        )

                        if imagen:

                            break


                # ----------------------------------
                # RESPALDO
                # ----------------------------------

                if not imagen:

                    imagen = (

                        "https://i.ytimg.com/vi/"

                        + video_id

                        + "/hqdefault.jpg"

                    )


                # ==================================
                # URL DE YOUTUBE
                # ==================================

                video_url = (

                    "https://www.youtube.com/watch?v="

                    + video_id

                )


                # ==================================
                # AGREGAR RESULTADO
                # ==================================

                canciones.append({

                    "titulo": titulo,

                    "artista": artista,

                    "imagen": imagen,

                    "url": video_url

                })


                # Solo necesitamos 10
                if len(canciones) >= 10:

                    break


            # ==================================
            # DEVOLVER RESULTADOS
            # ==================================

            print(

                "RESULTADOS ENCONTRADOS:",

                len(canciones)

            )


            return jsonify({

                "resultados": canciones

            })


        except Exception as e:

            ultimo_error = str(e)


            print(

                "FALLO EN",

                instancia,

                ":",

                ultimo_error

            )


            # Continuar con la siguiente
            # instancia.
            continue


    # ==========================================
    # TODAS LAS INSTANCIAS FALLARON
    # ==========================================

    return jsonify({

        "resultados": [],

        "error":
            "No se pudo conectar con "
            "ningún servidor de búsqueda."

    }), 503


# ==========================================
# DESCARGAR CANCION
# ==========================================
#
# ESTA PARTE SIGUE UTILIZANDO YT-DLP.
#
# No la estamos cambiando de sistema.
#
# ==========================================

@app.route("/download", methods=["POST"])
def descargar():

    data = request.get_json()


    # ------------------------------------------
    # Comprobar datos
    # ------------------------------------------

    if not data:

        return jsonify({

            "error":
                "No se recibieron datos"

        }), 400


    if "url" not in data:

        return jsonify({

            "error":
                "Falta la URL"

        }), 400


    url = data["url"]


    if not url:

        return jsonify({

            "error":
                "La URL está vacía"

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
    # OPCIONES YT-DLP
    # ==========================================

    opciones = {

        "format":
            "bestaudio/best",

        "outtmpl":
            salida,

        "noplaylist":
            True,

        "quiet":
            True,

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

        # --------------------------------------
        # Descargar
        # --------------------------------------

        with yt_dlp.YoutubeDL(
            opciones
        ) as ydl:

            info = ydl.extract_info(

                url,

                download=True

            )


        # ======================================
        # COMPROBAR MP3
        # ======================================

        archivo = os.path.join(

            DOWNLOAD_DIR,

            nombre + ".mp3"

        )


        if not os.path.exists(
            archivo
        ):

            return jsonify({

                "error":
                    "No se pudo crear el MP3"

            }), 500


        # ======================================
        # TÍTULO
        # ======================================

        titulo = info.get(

            "title",

            "cancion"

        )


        # ======================================
        # LIMPIAR NOMBRE
        # ======================================

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


        # ======================================
        # ENVIAR MP3
        # ======================================

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