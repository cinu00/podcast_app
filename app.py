import streamlit as st
from pydub import AudioSegment

import shutil

print("FFMPEG:", shutil.which("ffmpeg"))
print("FFPROBE:", shutil.which("ffprobe"))

from pydub import AudioSegment

def extract_audio(uploaded_file):
    # Zapisz plik tymczasowy
    uploaded_file.seek(0)  # ustaw wskaźnik na początek
    with open("temp.mp4", "wb") as f:
        f.write(uploaded_file.read())

    # Konwersja do audio
    audio = AudioSegment.from_file("temp.mp4")

    audio.export("audio.wav", format="wav")
    return "audio.wav"

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