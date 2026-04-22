import streamlit as st
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv
import subprocess

# --------------------
# Ładowanie klucza OpenAI
# --------------------
load_dotenv()
# --------------------
# Klucz OpenAI (z UI)
# --------------------
api_key = st.text_input(
    "🔑 Wpisz swój OpenAI API Key",
    type="password"
)

if not api_key:
    st.warning("Podaj klucz API, aby kontynuować")
    st.stop()

client = OpenAI(api_key=api_key)

# --------------------
# Funkcje pomocnicze
# --------------------
def save_uploaded_file(uploaded_file):
    """Zapisuje plik do systemu tymczasowego"""
    suffix = ".mp4" if uploaded_file.type.startswith("video") else ".mp3"
    data = uploaded_file.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        return tmp.name


def extract_audio(file_path):
    """Wyodrębnia audio z wideo przy użyciu ffmpeg"""
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
            st.error(f"Błąd ffmpeg: {e}")
            return None
    else:
        return file_path


def transcribe(audio_path):
    """Transkrypcja audio (Whisper)"""
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
    """Podsumowanie tekstu (GPT-4o)"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Streszcz tekst w kilku punktach."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Błąd przy podsumowaniu: {e}")
        return ""


# --------------------
# UI Streamlit
# --------------------
st.title("🎧 Audio/Video Transcriber & Summarizer")
st.write("Wgraj plik audio lub wideo, a aplikacja zrobi transkrypcję i podsumowanie.")

uploaded_file = st.file_uploader(
    "Wgraj plik (mp3, wav, mp4)",
    type=["mp3", "wav", "mp4"]
)

if uploaded_file:
    st.success(f"Plik {uploaded_file.name} wczytany!")

    # zapis pliku
    tmp_path = save_uploaded_file(uploaded_file)

    # ekstrakcja audio
    audio_path = extract_audio(tmp_path)

    if audio_path:
        st.audio(audio_path)

        # przycisk
        if st.button("Transkrybuj i podsumuj"):
            with st.spinner("🔄 Transkrypcja..."):
                text = transcribe(audio_path)

            st.subheader("📝 Transkrypcja")
            st.text_area("Tekst", text, height=200)

            with st.spinner("✨ Generowanie podsumowania..."):
                summary = summarize(text)

            st.subheader("📌 Podsumowanie")
            st.text_area("Podsumowanie", summary, height=150)