FROM python:3.11

# instalacja ffmpeg + brakujących bibliotek
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpulse0 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean

# katalog aplikacji
WORKDIR /app

# kopiowanie plików
COPY . /app

# instalacja zależności Pythona
RUN pip install --no-cache-dir \
    streamlit \
    pydub \
    openai==1.47.0 \
    python-dotenv

# port dla Streamlit (ważne dla chmury)
EXPOSE 8080

# uruchomienie aplikacji
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]