import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# --------------------------
# 1️⃣ Ustawienia strony
# --------------------------
st.set_page_config(page_title="Podcast Analyzer AI")
load_dotenv()  # Wczytanie zmiennych środowiskowych

# --------------------------
# 2️⃣ Klucz API OpenAI
# --------------------------
api_key = st.text_input("Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.warning("Musisz podać swój klucz API, aby korzystać z aplikacji!")
    st.stop()
client = OpenAI(api_key=api_key)

# --------------------------
# 3️⃣ UI: Upload / YouTube
# --------------------------
uploaded_file = st.file_uploader("Wrzuć podcast (audio/video)", type=["mp3", "wav", "mp4"])
youtube_url = st.text_input("🔗 Lub wklej link do YouTube")

# --------------------------
# 4️⃣ Funkcja: video -> audio
# --------------------------
def extract_audio_from_video(video_file):
    video_file.seek(0)  # 🔹 Ważne: przewijamy do początku
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    if not os.path.exists(tmp_video_path) or os.path.getsize(tmp_video_path) == 0:
        raise ValueError("Przesłany plik jest pusty lub nie zapisany poprawnie!")

    try:
        audio = AudioSegment.from_file(tmp_video_path)
    except Exception as e:
        raise RuntimeError(f"Nie udało się odczytać audio z pliku: {e}")

    tmp_audio_path = tmp_video_path.rsplit(".", 1)[0] + ".wav"
    audio.export(tmp_audio_path, format="wav")
    return tmp_audio_path

# --------------------------
# 5️⃣ Funkcja: YouTube -> audio
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
# 6️⃣ Funkcja: transkrypcja
# --------------------------
def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcription.text

# --------------------------
# 7️⃣ Funkcja: dzielenie tekstu
# --------------------------
def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# --------------------------
# 8️⃣ Funkcja: analiza podcastu
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
# 9️⃣ Główny flow aplikacji
# --------------------------
if st.button("🚀 Analizuj podcast"):
    try:
        # 🔹 Przygotowanie audio
        if youtube_url:
            with st.spinner("📥 Pobieranie audio z YouTube..."):
                audio_path = download_audio_from_youtube(youtube_url)
        elif uploaded_file:
            if "video" in uploaded_file.type:
                audio_path = extract_audio_from_video(uploaded_file)
            else:
                uploaded_file.seek(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(uploaded_file.read())
                    audio_path = tmp.name
        else:
            st.error("Wrzuć plik lub podaj link do YouTube!")
            st.stop()

        # 🔹 Transkrypcja
        with st.spinner("📝 Transkrypcja..."):
            text = transcribe_audio(audio_path)
        st.subheader("📄 Transkrypcja")
        st.write(text)

        # 🔹 Chunking i analiza
        chunks = split_text(text)
        summaries = []
        with st.spinner("🧠 Analiza podcastu..."):
            for chunk in chunks:
                summaries.append(analyze_podcast(chunk))

        # 🔹 Finalna analiza
        final_text = "\n".join(summaries)
        final_summary = analyze_podcast(final_text)
        st.subheader("📊 Finalna analiza")
        st.write(final_summary)

    except Exception as e:
        st.error(f"Nie udało się przygotować audio: {e}")

    finally:
        # 🔹 Sprzątanie plików tymczasowych
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)