import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# 🔥 musi być pierwsze
st.set_page_config(page_title="Podcast Analyzer AI")

# 🔑 API
load_dotenv()

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")


if not api_key:
    st.error("Brak klucza API!")
    st.stop()

client = OpenAI(api_key=api_key)

st.set_page_config(page_title="Podcast Analyzer AI")
st.title("🎙️ Podcast Analyzer AI")


st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        color: #ffffff;
    }

    .main {
        background-color: rgba(0,0,0,0);
    }

    .block-container {
        padding-top: 2rem;
    }

    h1, h2, h3 {
        color: #ffffff;
    }

    .stButton>button {
        background-color: #6c5ce7;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.6em 1.2em;
    }

    .stButton>button:hover {
        background-color: #a29bfe;
        transform: scale(1.05);
    }

    .card {
        background-color: rgba(255,255,255,0.08);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)



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

    audio = AudioSegment.from_file(tmp_video_path, format="mp4")
    tmp_audio_path = tmp_video_path.replace(".mp4", ".wav")
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
# Funkcja: dzielenie tekstu (chunking)
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
2. Najważniejsze wnioski w formie bullet points
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
    if youtube_url:
        with st.spinner("📥 Pobieranie audio z YouTube..."):
            audio_path = download_audio_from_youtube(youtube_url)

    elif uploaded_file:
        if "video" in uploaded_file.type:
            audio_path = extract_audio_from_video(uploaded_file)
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file.read())
                audio_path = tmp.name
    else:
        st.error("Wrzuć plik lub podaj link do YouTube!")
        st.stop()

    # 2️⃣ transkrypcja
    with st.spinner("📝 Transkrypcja..."):
        text = transcribe_audio(audio_path)

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
    os.remove(audio_path)