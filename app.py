import streamlit as st
from pydub import AudioSegment
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv
import subprocess  # <- potrzebne do sprawdzenia ffmpeg

# --------------------
# Sprawdzenie ffmpeg
# --------------------
try:
    version = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    st.write("✅ FFmpeg jest dostępny w środowisku!")
    st.text(version.stdout)
except Exception as e:
    st.error("❌ FFmpeg NIE jest dostępny w środowisku!")
    st.text(str(e))

# --------------------
# Ładowanie klucza OpenAI
# --------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))





import streamlit as st
from pydub import AudioSegment
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv

# --------------------
# Ładowanie klucza OpenAI
# --------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------
# Funkcje pomocnicze
# --------------------
def save_uploaded_file(uploaded_file):
    import tempfile

    suffix = ".mp4" if uploaded_file.type.startswith("video") else ".mp3"

    data = uploaded_file.getvalue()  # 🔥 KLUCZOWA ZMIANA

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        return tmp.name

def extract_audio(file_path):
    import os
    import subprocess

    if os.path.getsize(file_path) == 0:
        st.error("Plik jest pusty ❌")
        return None

    if file_path.endswith(".mp4"):
        audio_path = file_path.replace(".mp4", ".mp3")

        try:
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", audio_path, "-y"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if result.returncode != 0:
                st.error("Błąd ffmpeg:\n" + result.stderr.decode())
                return None

            return audio_path

        except Exception as e:
            st.error(f"Błąd przy wywołaniu ffmpeg: {e}")
            return None
    else:
        return file_path
def transcribe(audio_path):
    """Transkrypcja audio przy użyciu Whisper."""
    try:
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text
    except Exception as e:
        st.error(f"Błąd przy transkrypcji: {e}")
        return ""

def summarize(text):
    """Generowanie podsumowania przy użyciu GPT-4o."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Streszcz podany tekst w kilku punktach."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Błąd przy generowaniu podsumowania: {e}")
        return ""

# --------------------
# UI Streamlit
# --------------------
st.title("🎧 Audio/Video Transcriber & Summarizer")
st.write("Wgraj plik audio lub wideo, a aplikacja przetranskrybuje go i zrobi podsumowanie.")

uploaded_file = st.file_uploader(
    "Wgraj plik audio (mp3, wav) lub wideo (mp4)", 
    type=["mp3", "wav", "mp4"]
)

if uploaded_file:
    st.success(f"Plik {uploaded_file.name} wczytany!")

    # Zapis i przygotowanie pliku audio
    tmp_path = save_uploaded_file(uploaded_file)
    audio_path = extract_audio(tmp_path)
    st.audio(audio_path)

    import os
    st.write("Ścieżka pliku:", tmp_path)
    st.write("Rozmiar pliku (bajty):", os.path.getsize(tmp_path))

    # Dopiero potem przetwarzanie
    audio_path = extract_audio(tmp_path)

    if audio_path:
        st.audio(audio_path)

    # Transkrypcja i podsumowanie
    if st.button("Transkrybuj i podsumuj"):
        with st.spinner("Transkrypcja w toku..."):
            text = transcribe(audio_path)
            st.subheader("📝 Transkrypcja")
            st.text_area("Transkrypcja", text, height=200)

        with st.spinner("Generowanie podsumowania..."):
            summary = summarize(text)
            st.subheader("📌 Podsumowanie")
            st.text_area("Podsumowanie", summary, height=150)