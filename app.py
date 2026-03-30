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
def extract_audio(video_path, output_path="output.mp3"):
    try:
        audio = AudioSegment.from_file(video_path)
        audio.export(output_path, format="mp3")
        return output_path
    except Exception as e:
        st.error(f"Błąd przy wyodrębnianiu audio: {e}")
        return None

def transcribe(audio_path):
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

uploaded_file = st.file_uploader("Wgraj plik audio (mp3, wav) lub wideo (mp4)", type=["mp3", "wav", "mp4"])

if uploaded_file:
    st.success(f"Plik {uploaded_file.name} wczytany!")

    # Obsługa audio
    if uploaded_file.type.startswith("audio"):
        st.audio(uploaded_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            tmp_audio.write(uploaded_file.read())
            audio_path = tmp_audio.name

    # Obsługa wideo
    elif uploaded_file.type.startswith("video"):
        st.video(uploaded_file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
            tmp_video.write(uploaded_file.read())
            video_path = tmp_video.name
        audio_path = extract_audio(video_path)
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