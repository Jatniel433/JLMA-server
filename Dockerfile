FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Instalar Deno
RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="/root/.deno/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD gunicorn --bind 0.0.0.0:$PORT main:app