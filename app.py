import streamlit as st
import tempfile
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import yt_dlp

# 🔹 1. Ustawienia strony
st.set_page_config(page_title="Podcast Analyzer AI")
st.title("🎙️ Podcast Analyzer AI")

st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #1f1c2c, #928dab);
    color: #ffffff;
}
.block-container {
    padding-top: 2rem;
}
.stButton>button {
    background-color: #6c5ce7;
    color: white;
    font-weight: bold;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# 🔹 2. ENV
load_dotenv()

# 🔹 3. API KEY
api_key = st.text_input("Wklej swój OpenAI API Key:", type="password") or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Podaj klucz API")
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------------
# INPUT
# --------------------------
uploaded_file = st.file_uploader("Wrzuć podcast", type=["mp3", "wav", "mp4"])
youtube_url = st.text_input("🔗 Link YouTube")

# --------------------------
# VIDEO -> AUDIO
# --------------------------
def extract_audio_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name

    audio = AudioSegment.from_file(video_path)
    audio_path = video_path.replace(".mp4", ".wav")
    audio.export(audio_path, format="wav")

    return audio_path

# --------------------------
# YOUTUBE DOWNLOAD (SAFE)
# --------------------------
def download_audio_from_youtube(url):
    output_path = "podcast.%(ext)s"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if not info:
                raise Exception("Nie znaleziono video")

            filename = ydl.prepare_filename(info)
            return filename

    except Exception as e:
        st.error("❌ Błąd pobierania YouTube")
        st.text(str(e))
        return None

# --------------------------
# KONWERSJA DO WAV
# --------------------------
def convert_to_wav(input_file):
    audio = AudioSegment.from_file(input_file)
    output_file = input_file.split(".")[0] + ".wav"
    audio.export(output_file, format="wav")
    return output_file

# --------------------------
# TRANSKRYPCJA
# --------------------------
def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcription.text

# --------------------------
# CHUNKING
# --------------------------
def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# --------------------------
# ANALIZA
# --------------------------
def analyze_podcast(text):
    prompt = f"""
Przeanalizuj podcast:

1. Streszczenie (max 5 zdań)
2. Wnioski (bullet points)
3. Tematy
4. 3 cytaty

Tekst:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ekspert od podcastów"},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# --------------------------
# MAIN
# --------------------------
if st.button("🚀 Analizuj"):
    
    # 1️⃣ AUDIO
    if youtube_url:
        with st.spinner("📥 Pobieranie..."):
            audio_path = download_audio_from_youtube(youtube_url)

        if not audio_path:
            st.stop()

        audio_path = convert_to_wav(audio_path)

    elif uploaded_file:
        if "video" in uploaded_file.type:
            audio_path = extract_audio_from_video(uploaded_file)
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file.read())
                audio_path = tmp.name
    else:
        st.error("Dodaj plik lub link")
        st.stop()

    # 2️⃣ TRANSKRYPCJA
    with st.spinner("📝 Transkrypcja..."):
        text = transcribe_audio(audio_path)
        st.subheader("📄 Transkrypcja")
        st.write(text)

    # 3️⃣ ANALIZA (chunk)
    chunks = split_text(text)
    results = []

    with st.spinner("🧠 Analiza..."):
        for chunk in chunks:
            results.append(analyze_podcast(chunk))

    final_text = "\n".join(results)
    final_summary = analyze_podcast(final_text)

    st.subheader("📊 Wynik")
    st.write(final_summary)

    # 4️⃣ CLEANUP
    os.remove(audio_path)