import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# --------------------------
# 🔹 CONFIG (MUSI BYĆ NA GÓRZE)
# --------------------------
st.set_page_config(page_title="Podcast Analyzer AI")

# --------------------------
# 🔹 API KEY
# --------------------------
load_dotenv()

api_key = st.text_input("🔑 Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("❗ Podaj klucz OpenAI aby korzystać z aplikacji")
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------------
# 🔹 UI
# --------------------------
st.title("🎙️ Podcast Analyzer AI")

st.info("💡 Jeśli YouTube nie działa — wrzuć plik MP3 lub MP4")

st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        color: #ffffff;
    }

    .stButton>button {
        background-color: #6c5ce7;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.6em 1.2em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------
# 🔹 INPUT
# --------------------------
uploaded_file = st.file_uploader(
    "📂 Wrzuć podcast",
    type=["mp3", "wav", "mp4", "m4a"]
)

youtube_url = st.text_input("🔗 Lub wklej link do YouTube")

# --------------------------
# 🔹 VIDEO → AUDIO
# --------------------------
def extract_audio_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    audio = AudioSegment.from_file(tmp_video_path)
    tmp_audio_path = tmp_video_path.replace(".mp4", ".wav")
    audio.export(tmp_audio_path, format="wav")

    return tmp_audio_path

# --------------------------
# 🔹 YOUTUBE → AUDIO (WAV)
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
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return filename.rsplit('.', 1)[0] + ".wav"

    except Exception as e:
        st.error("❌ Nie udało się pobrać audio z YouTube")
        st.write(str(e))
        st.stop()

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
Przeanalizuj poniższy podcast i przygotuj:

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
# 🔹 MAIN FLOW
# --------------------------
if st.button("🚀 Analizuj podcast"):

    try:
        # --------------------------
        # 1. AUDIO SOURCE
        # --------------------------
        if youtube_url:
            with st.spinner("📥 Pobieranie z YouTube..."):
                audio_path = download_audio_from_youtube(youtube_url)

        elif uploaded_file:
            if "video" in uploaded_file.type:
                audio_path = extract_audio_from_video(uploaded_file)
            else:
                audio = AudioSegment.from_file(uploaded_file)
                tmp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                audio.export(tmp_audio_path, format="wav")
                audio_path = tmp_audio_path
        else:
            st.error("❗ Wrzuć plik lub podaj link")
            st.stop()

        # --------------------------
        # 2. TRANSKRYPCJA
        # --------------------------
        with st.spinner("📝 Transkrypcja..."):
            text = transcribe_audio(audio_path)

        st.subheader("📄 Transkrypcja")
        st.write(text)

        # --------------------------
        # 3. ANALIZA
        # --------------------------
        chunks = split_text(text)
        summaries = []

        with st.spinner("🧠 Analiza..."):
            for chunk in chunks:
                summaries.append(analyze_podcast(chunk))

        final_summary = analyze_podcast("\n".join(summaries))

        st.subheader("📊 Podsumowanie")
        st.write(final_summary)

        # --------------------------
        # CLEANUP
        # --------------------------
        os.remove(audio_path)

    except Exception as e:
        st.error("❌ Coś poszło nie tak")
        st.write(str(e))