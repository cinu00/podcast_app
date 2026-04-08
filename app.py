import streamlit as st
from pydub import AudioSegment
import subprocess


import shutil

print("FFMPEG:", shutil.which("ffmpeg"))
print("FFPROBE:", shutil.which("ffprobe"))

from pydub import AudioSegment

def extract_audio(uploaded_file):
    # upewnij się, że czytamy od początku
    uploaded_file.seek(0)

    # zapis pliku na dysk
    with open("temp.mp4", "wb") as f:
        f.write(uploaded_file.read())

    # 🔍 DEBUG - sprawdzamy co widzi ffprobe
    result = subprocess.run(
        ["ffprobe", "temp.mp4"],
        capture_output=True,
        text=True
    )
    print("FFPROBE OUTPUT:", result.stdout)
    print("FFPROBE ERR:", result.stderr)

    # konwersja audio
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