import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# 🔹 1. ustawienia strony
st.set_page_config(page_title="Podcast Analyzer AI")

# 🔹 2. Wczytanie zmiennych środowiskowych
load_dotenv()

# 🔹 3. Klucz OpenAI
api_key = st.text_input("Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.warning("Musisz podać swój klucz API!")
    st.stop()

# 🔹 4. Klient OpenAI
client = OpenAI(api_key=api_key)

# 🔹 5. Ścieżki do ffmpeg/ffprobe w DigitalOcean
AudioSegment.converter = "/layers/digitalocean_apt/apt/usr/bin/ffmpeg"
AudioSegment.ffprobe   = "/layers/digitalocean_apt/apt/usr/bin/ffprobe"

# --------------------------
# UI: upload pliku lub link
# --------------------------
uploaded_file = st.file_uploader(
    "Wrzuć podcast (audio/video)", type=["mp3", "wav", "mp4"]
)
youtube_url = st.text_input("🔗 Lub wklej link do YouTube")

# --------------------------
# Funkcja: video -> audio
# --------------------------
def extract_audio_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    if not os.path.exists(tmp_video_path) or os.path.getsize(tmp_video_path) == 0:
        raise ValueError("Przesłany plik jest pusty lub nie został zapisany poprawnie!")

    try:
        audio = AudioSegment.from_file(tmp_video_path)
    except Exception as e:
        raise RuntimeError(f"Nie udało się odczytać audio z pliku: {e}")

    tmp_audio_path = tmp_video_path.rsplit(".", 1)[0] + ".wav"
    audio.export(tmp_audio_path, format="wav")
    return tmp_audio_path

# --------------------------
# Funkcja: pobieranie audio z YouTube
# --------------------------
def download_audio_from_youtube(url):
    output_path = "podcast.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename

# --------------------------
# Funkcja: transkrypcja
# --------------------------
def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcription.text

# --------------------------
# Funkcja: dzielenie tekstu
# --------------------------
def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# --------------------------
# Funkcja: analiza podcastu
# --------------------------
def analyze_podcast(text):
    PROMPT = """
Przeanalizuj poniższy podcast i przygotuj:

1. Krótkie streszczenie (max 5 zdań)
2. Najważniejsze wnioski (bullet points)
3. Kluczowe tematy rozmowy
4. 3 najciekawsze cytaty

Tekst:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Jesteś ekspertem od analizy podcastów."},
            {"role": "user", "content": PROMPT + text}
        ]
    )
    return response.choices[0].message.content

# --------------------------
# Główny flow aplikacji
# --------------------------
if st.button("🚀 Analizuj podcast"):

    # 1️⃣ przygotowanie audio
    try:
        if youtube_url:
            with st.spinner("📥 Pobieranie audio z YouTube..."):
                audio_path = download_audio_from_youtube(youtube_url)

        elif uploaded_file:
            if uploaded_file.type.startswith("video"):
                audio_path = extract_audio_from_video(uploaded_file)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(uploaded_file.read())
                    audio_path = tmp.name
        else:
            st.error("Wrzuć plik lub podaj link do YouTube!")
            st.stop()
    except Exception as e:
        st.error(f"Nie udało się przygotować audio: {e}")
        st.stop()

    # 2️⃣ transkrypcja
    try:
        with st.spinner("📝 Transkrypcja..."):
            text = transcribe_audio(audio_path)
    except Exception as e:
        st.error(f"Błąd transkrypcji: {e}")
        st.stop()

    st.subheader("📄 Transkrypcja")
    st.write(text)

    # 3️⃣ chunking
    chunks = split_text(text)
    summaries = []
    with st.spinner("🧠 Analiza podcastu..."):
        for chunk in chunks:
            summaries.append(analyze_podcast(chunk))

    # 4️⃣ finalna analiza
    final_text = "\n".join(summaries)
    final_summary = analyze_podcast(final_text)

    st.subheader("📊 Finalna analiza")
    st.write(final_summary)

    # 5️⃣ sprzątanie pliku tymczasowego
    try:
        os.remove(audio_path)
    except:
        pass