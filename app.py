import streamlit as st
from pydub import AudioSegment

import shutil
print("ffmpeg:", shutil.which("ffmpeg"))

def extract_audio(video_file):
    """Funkcja do wyodrębniania audio z pliku wideo"""
    audio = AudioSegment.from_file(video_file)
    audio_file_path = "extracted_audio.mp3"
    audio.export(audio_file_path, format="mp3")
    return audio_file_path

st.title("Aplikacja do przetwarzania multimediów")

uploaded_file = st.file_uploader("Prześlij plik audio lub wideo", type=["mp3", "mp4", "wav"])

if uploaded_file is not None:
    file_type = uploaded_file.type.split('/')[0]

    # Wyświetlanie audio
    if file_type == 'audio':
        st.audio(uploaded_file, format=uploaded_file.type)

    # Wyświetlanie wideo z możliwością ekstrakcji audio
    elif file_type == 'video':
        st.video(uploaded_file)

        if st.button("Wyodrębnij audio z wideo"):
            audio_file_path = extract_audio(uploaded_file)
            st.success(f"Audio wyodrębnione pomyślnie! {audio_file_path}")
            st.audio(audio_file_path, format="audio/mp3")