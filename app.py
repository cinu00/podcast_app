import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# 🔹 ustawienia strony (TYLKO RAZ!)
st.set_page_config(page_title="Podcast Analyzer AI")

# 🔹 API key
load_dotenv()
api_key = st.text_input("Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Musisz podać swój klucz API!")
    st.stop()

client = OpenAI(api_key=api_key)

st.title("🎙️ Podcast Analyzer AI")

st.info("💡 Jeśli YouTube nie działa, wrzuć plik MP3 ręcznie")

# --------------------------
# UI
# --------------------------
uploaded_file = st.file_uploader("Wrzuć podcast (audio/video)", type=["mp3", "wav", "mp4"])
youtube_url = st.text_input("🔗 Lub wklej link do YouTube")

# --------------------------
# VIDEO → AUDIO
# --------------------------
def extract_audio_from_video(video_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(video_file.read())
            tmp_video_path = tmp_video.name

        audio = AudioSegment.from_file(tmp_video_path, format="mp4")
        tmp_audio_path = tmp_video_path.replace(".mp4", ".wav")
        audio.export(tmp_audio_path, format="wav")

        return tmp_audio_path

    except Exception as e:
        st.error("❌ Błąd przy konwersji video → audio")
        st.write(str(e))
        st.stop()

# --------------------------
# YOUTUBE
# --------------------------
def download_audio_from_youtube(url):
    try:
        output_path = "podcast.%(ext)s"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return filename

    except Exception as e:
        st.error("❌ Nie udało się pobrać audio z YouTube")
        st.write(str(e))
        st.stop()

# --------------------------
# TRANSKRYPCJA
# --------------------------
def transcribe_audio(file_path):
    try:
        with open(file_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcription.text

    except Exception as e:
        st.error("❌ Błąd transkrypcji")
        st.write(str(e))
        st.stop()

# --------------------------
# ANALIZA
# --------------------------
def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def analyze_podcast(text):
    try:
        PROMPT = """
Przeanalizuj podcast i przygotuj:
1. Krótkie streszczenie
2. Najważniejsze wnioski
3. Kluczowe tematy
4. 3 cytaty
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od podcastów."},
                {"role": "user", "content": PROMPT + text}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error("❌ Błąd analizy")
        st.write(str(e))
        st.stop()

# --------------------------
# MAIN
# --------------------------
if st.button("🚀 Analizuj podcast"):
    try:
        # AUDIO
        if youtube_url:
            with st.spinner("📥 Pobieranie z YouTube..."):
                audio_path = download_audio_from_youtube(youtube_url)

        elif uploaded_file:
            if "video" in uploaded_file.type:
                audio_path = extract_audio_from_video(uploaded_file)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(uploaded_file.read())
                    audio_path = tmp.name
        else:
            st.error("Wrzuć plik lub link!")
            st.stop()

        # TRANSKRYPCJA
        with st.spinner("📝 Transkrypcja..."):
            text = transcribe_audio(audio_path)

        st.subheader("📄 Transkrypcja")
        st.write(text)

        # ANALIZA
        chunks = split_text(text)
        summaries = []

        with st.spinner("🧠 Analiza..."):
            for chunk in chunks:
                summaries.append(analyze_podcast(chunk))

        final_text = "\n".join(summaries)
        final_summary = analyze_podcast(final_text)

        st.subheader("📊 Podsumowanie")
        st.write(final_summary)

        os.remove(audio_path)

    except Exception as e:
        st.error("❌ Coś poszło nie tak")
        st.write(str(e))