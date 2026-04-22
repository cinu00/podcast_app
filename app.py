import streamlit as st
import tempfile
import os
import traceback
import subprocess
from dotenv import load_dotenv
from openai import OpenAI
import yt_dlp

# --------------------------
# 🔹 CONFIG
# --------------------------
st.set_page_config(page_title="Podcast Analyzer AI")

# --------------------------
# 🔹 API KEY
# --------------------------
load_dotenv()

api_key = st.text_input("🔑 Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("❗ Podaj klucz OpenAI")
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------------
# 🔹 UI
# --------------------------
st.title("🎙️ Podcast Analyzer AI")
st.info("💡 Możesz wrzucić MP3/MP4 lub wkleić link YouTube")

uploaded_file = st.file_uploader(
    "📂 Wrzuć podcast",
    type=["mp3", "wav", "mp4", "m4a"]
)

youtube_url = st.text_input("🔗 Lub wklej link do YouTube")

# --------------------------
# 🔹 SAVE FILE
# --------------------------
def save_uploaded_file(uploaded_file):
    suffix = ".mp4" if uploaded_file.type.startswith("video") else ".mp3"
    data = uploaded_file.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        return tmp.name

# --------------------------
# 🔹 MP4 → MP3 (FFMPEG)
# --------------------------
def extract_audio(file_path):
    if file_path.endswith(".mp4"):
        audio_path = file_path.replace(".mp4", ".mp3")

        try:
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if result.returncode != 0:
                st.error("❌ Błąd ffmpeg:\n" + result.stderr.decode())
                return None

            return audio_path

        except Exception:
            st.error("❌ FFmpeg crash:")
            st.text(traceback.format_exc())
            return None
    else:
        return file_path

# --------------------------
# 🔹 YOUTUBE → MP3
# --------------------------
def download_audio_from_youtube(url):
    try:
        output_path = "podcast.%(ext)s"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return filename.rsplit('.', 1)[0] + ".mp3"

    except Exception:
        st.error("❌ YouTube error:")
        st.text(traceback.format_exc())
        raise

# --------------------------
# 🔹 TRANSKRYPCJA
# --------------------------
def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcription.text

# --------------------------
# 🔹 CHUNKING
# --------------------------
def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# --------------------------
# 🔹 ANALIZA
# --------------------------
def analyze_podcast(text):
    PROMPT = """
Przeanalizuj podcast i przygotuj:

1. Krótkie streszczenie (max 5 zdań)
2. Najważniejsze wnioski (bullet points)
3. Kluczowe tematy
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
# 🔹 MAIN
# --------------------------
if st.button("🚀 Analizuj podcast"):

    try:
        # 1️⃣ ŹRÓDŁO AUDIO
        if youtube_url:
            with st.spinner("📥 Pobieranie z YouTube..."):
                file_path = download_audio_from_youtube(youtube_url)
        elif uploaded_file:
            file_path = save_uploaded_file(uploaded_file)
        else:
            st.error("❗ Wrzuć plik lub podaj link")
            st.stop()

        # 2️⃣ KONWERSJA MP4 → MP3
        audio_path = extract_audio(file_path)

        if not audio_path:
            st.stop()

        # 3️⃣ CHECK SIZE
        size_mb = os.path.getsize(audio_path) / 1_000_000
        st.write(f"📦 Rozmiar pliku: {round(size_mb,2)} MB")

        if size_mb > 25:
            st.error("❌ Plik za duży (limit 25MB)")
            st.stop()

        # 4️⃣ TRANSKRYPCJA
        with st.spinner("📝 Transkrypcja..."):
            text = transcribe_audio(audio_path)

        st.subheader("📄 Transkrypcja")
        st.write(text)

        # 5️⃣ ANALIZA
        chunks = split_text(text)
        summaries = []

        with st.spinner("🧠 Analiza..."):
            for chunk in chunks:
                summaries.append(analyze_podcast(chunk))

        final_summary = analyze_podcast("\n".join(summaries))

        st.subheader("📊 Podsumowanie")
        st.write(final_summary)

        # 6️⃣ CLEANUP
        os.remove(audio_path)

    except Exception:
        st.error("❌ FULL ERROR:")
        st.text(traceback.format_exc())