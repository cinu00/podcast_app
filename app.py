import streamlit as st
import subprocess

FFMPEG_PATH = "/layers/digitalocean_apt/apt/usr/bin/ffmpeg"

def extract_audio(uploaded_file):
    uploaded_file.seek(0)

    with open("temp.mp4", "wb") as f:
        f.write(uploaded_file.read())

    command = [
        FFMPEG_PATH,
        "-i", "temp.mp4",
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "audio.wav"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    print("FFMPEG STDERR:", result.stderr)

    return "audio.wav"


st.title("Aplikacja do przetwarzania multimediów")

uploaded_file = st.file_uploader("Prześlij plik audio lub wideo", type=["mp3", "mp4", "wav"])

if uploaded_file is not None:
    file_type = uploaded_file.type.split('/')[0]

    if file_type == 'audio':
        st.audio(uploaded_file, format=uploaded_file.type)

    elif file_type == 'video':
        st.video(uploaded_file)

        if st.button("Wyodrębnij audio z wideo"):
            audio_file_path = extract_audio(uploaded_file)
            st.success(f"Audio wyodrębnione pomyślnie! {audio_file_path}")
            st.audio(audio_file_path, format="audio/wav")