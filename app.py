import streamlit as st
import tempfile
import os
import traceback
import subprocess
import re
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
st.info("💡 YouTube → najpierw napisy (szybciej), potem audio fallback")

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
# 🔹 YOUTUBE → SUBTITLES
# --------------------------
def get_youtube_transcript(url):
    try:
        ydl_opts = {
            'skip_download': True,
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        subtitles = info.get("subtitles") or info.get("automatic_captions")

        if not subtitles:
            return None

        # preferuj PL → EN
        for lang in ["pl", "en"]:
            if lang in subtitles:
                sub_url = subtitles[lang][0]["url"]

                import requests
                response = requests.get(sub_url)
                return response.text

        # fallback: pierwszy dostępny
        first_lang = list(subtitles.keys())[0]
        sub_url = subtitles[first_lang][0]["url"]

        import requests
        response = requests.get(sub_url)
        return response.text

    except Exception:
        return None
# --------------------------
# 🔹 CLEAN SUBTITLES
# --------------------------
def clean_subtitles(text):
    text = re.sub(r'\d{2}:\d{2}:\d{2}.*', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text

# --------------------------
# 🔹 YOUTUBE → AUDIO (fallback)
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
        return None

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

1. Krótkie streszczenie
2. Najważniejsze wnioski
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
        # ==========================
        # 🔥 TRY: YOUTUBE SUBTITLES
        # ==========================
        if youtube_url:
            with st.spinner("📄 Pobieranie napisów..."):
                text = get_youtube_transcript(youtube_url)

            if text:
                st.success("✅ Użyto napisów (szybciej i bez limitów)")
                text = clean_subtitles(text)

            else:
                st.warning("⚠️ Brak napisów → fallback do audio")

                with st.spinner("📥 Pobieranie audio..."):
                    file_path = download_audio_from_youtube(youtube_url)

                if not file_path:
                    st.error("❌ YouTube blokuje pobieranie")
                    st.stop()

                audio_path = extract_audio(file_path)

                size_mb = os.path.getsize(audio_path) / 1_000_000
                st.write(f"📦 Rozmiar: {round(size_mb,2)} MB")

                if size_mb > 25:
                    st.error("❌ Plik za duży (limit 25MB)")
                    st.stop()

                with st.spinner("📝 Transkrypcja..."):
                    text = transcribe_audio(audio_path)

        # ==========================
        # 🔥 UPLOAD FILE
        # ==========================
        elif uploaded_file:
            file_path = save_uploaded_file(uploaded_file)
            audio_path = extract_audio(file_path)

            size_mb = os.path.getsize(audio_path) / 1_000_000
            st.write(f"📦 Rozmiar: {round(size_mb,2)} MB")

            if size_mb > 25:
                st.error("❌ Plik za duży (limit 25MB)")
                st.stop()

            with st.spinner("📝 Transkrypcja..."):
                text = transcribe_audio(audio_path)

        else:
            st.error("❗ Wrzuć plik lub podaj link")
            st.stop()

        # ==========================
        # 🔥 ANALIZA
        # ==========================
        st.subheader("📄 Tekst")
        st.write(text)

        chunks = split_text(text)
        summaries = []

        with st.spinner("🧠 Analiza..."):
            for chunk in chunks:
                summaries.append(analyze_podcast(chunk))

        final_summary = analyze_podcast("\n".join(summaries))

        st.subheader("📊 Podsumowanie")
        st.write(final_summary)

    except Exception:
        st.error("❌ FULL ERROR:")
        st.text(traceback.format_exc())