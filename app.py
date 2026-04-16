import streamlit as st
from audiorecorder import audiorecorder
from io import BytesIO
# from dotenv import dotenv_values
from openai import OpenAI, AuthenticationError, OpenAIError
from pydub import AudioSegment
from hashlib import md5

import shutil
import streamlit as st

st.write("ffmpeg:", shutil.which("ffmpeg"))
st.write("ffprobe:", shutil.which("ffprobe"))


# env = dotenv_values('.env')
AUDIO_TRANSCRIBE_MODEL='whisper-1'

def get_openai_client():
    return OpenAI(api_key=st.session_state['openai_api_key'])

def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = 'audio.mp3'
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format='verbose_json'
    )

    return transcript.text

def validate_openai_key(api_key: str) -> bool:
    try:
        client = OpenAI(api_key=api_key.strip())
        client.models.list()
        return True
    except AuthenticationError:
        return False
    except OpenAIError as e:
        st.warning(f"Błąd OpenAI: {e}")
        return False
    
def get_description(text):
    openai_client = get_openai_client()
    prompt = f'Podsumuj poniższy tekst:\n\n{text}'
    response = openai_client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'Jesteś asystentem do podsumowań tekstu.'},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0.1
    )
    summary = str(response.choices[0].message.content).strip()
    return summary

st.markdown('''
# 🎙️ Essenza – Twój osobisty asystent do streszczania audio i wideo  

Masz godzinny podcast, wykład albo nagranie spotkania i brak czasu, by wysłuchać wszystkiego?  
**Essenza zrobi to za Ciebie.**  
''')

tab_1, tab_2 = st.tabs(['Opis aplikacji', 'Aplikacja'])

with tab_1:
    st.markdown('''
    ## ✨ Co potrafi Essenza?  
    - 🔊 **Audio & Podcasty** - szybkie streszczenia rozmów, wykładów i nagrań głosowych.  
    - 🎥 **Wideo & Spotkania** - automatyczne podsumowania webinarów, wideokonferencji i filmów.  
    - ⚡ **Szybkość i precyzja** - w kilka chwil otrzymasz klarowne notatki wraz z transkrypcją.  
    - 🌍 **Wielojęzyczność** - streszczenia w wielu językach, idealne dla globalnych treści.  

    ---

    ## 🚀 Jak to działa?  
    1. **Podaj** swój klucz OpenAI
    2. **Wgraj** plik audio lub wideo lub **Nagraj** się.  
    3. **Otrzymaj** gotowe streszczenie wraz z transkrypcją.  

    ---

    👉 Zamiast tracić czas na przewijanie - poznaj sedno treści w kilka minut.  

    **Essenza - bo liczy się to, co najważniejsze.**
    ''')

with tab_2:
    # --- inicjalizacja klucza API ---
    if not st.session_state.get('openai_api_key'):
        # if "OPENAI_API_KEY" in env:
        #     st.session_state['openai_api_key'] = env["OPENAI_API_KEY"]
        # else: 
        st.info('Żeby korzystać z tej aplikacji potrzebujesz klucza API OpenAI')
        key_input = st.text_input('OpenAI API KEY', type='password')
        if key_input:
            if not validate_openai_key(key_input):
                st.error("Niepoprawny klucz API. Spróbuj ponownie.")
            else:
                st.session_state['openai_api_key'] = key_input.strip()
                st.rerun()
    
    if not st.session_state.get('openai_api_key'):
        st.stop()

    st.toast("Klucz poprawny!")

    st.write('### Nagraj swój głos')

    # --- inicjalizacja session_state ---
    for key, default in {
        "note_md5": None,
        "file_md5": None,
        "audio_to_transcribe": None,
        "note_text": "",
        "file_text": "",
        "note_summary": "",
        "file_summary": ""
    }.items():
        st.session_state.setdefault(key, default)

    source_label = None
    audio_note_bytes = None
    audio_from_file = None

    def save_audio_to_state(audio_bytes, md5_key, text_key, summary_key):
        current_md5 = md5(audio_bytes).hexdigest()
        if st.session_state[md5_key] != current_md5:
            st.session_state[text_key] = ''
            st.session_state[summary_key] = ''
            st.session_state[md5_key] = current_md5
        st.session_state['audio_to_transcribe'] = audio_bytes

    # --- nagrywanie audio ---
    audio_note = audiorecorder('Nagraj wiadomość', 'Zatrzymaj nagrywanie')
    if audio_note:
        audio = BytesIO()
        audio_note.export(audio, 'mp3')
        audio_note_bytes = audio.getvalue()
        save_audio_to_state(audio_note_bytes, 'note_md5', 'note_text', 'note_summary')
        st.audio(audio_note_bytes, format='audio/mp3')
        source_label = 'Nagranie'

    st.write('### lub prześlij plik .mp3 lub .mp4')

    # --- upload pliku ---
    uploaded_file = st.file_uploader('', ['mp3', 'mp4'], False)
    if uploaded_file:
        file_bytes = uploaded_file.read()
        source_label = 'Plik'

        if uploaded_file.type.startswith("audio"):
            st.audio(file_bytes, format=uploaded_file.type)
            audio_from_file = file_bytes
        elif uploaded_file.type.startswith("video"):
            st.video(file_bytes)
            video_file = BytesIO(file_bytes)
            audio_segment = AudioSegment.from_file(video_file, format="mp4")
            audio = BytesIO()
            audio_segment.export(audio, format='mp3')
            audio_from_file = audio.getvalue()

        save_audio_to_state(audio_from_file, 'file_md5', 'file_text', 'file_summary')

    # --- radio do wyboru źródła jeśli oba dostępne ---
    if audio_note and uploaded_file:
        source_label = st.radio(
            'Wybierz z którego źródła mam wygenerować podsumowanie:',
            ['Nagranie', 'Plik']
        )
        st.session_state['audio_to_transcribe'] = (
            audio_note_bytes if source_label == 'Nagranie' else audio_from_file
        )

  # --- generowanie transkrypcji i podsumowania ---
if st.session_state['audio_to_transcribe'] is not None:
    if st.button('Podsumuj'):
        with st.spinner("Trwa generowanie transkrypcji i podsumowania..."):
            if source_label == 'Nagranie':
                st.session_state['note_text'] = transcribe_audio(st.session_state['audio_to_transcribe'])
                if not st.session_state['note_summary']:
                    st.session_state['note_summary'] = get_description(st.session_state['note_text'])
            elif source_label == 'Plik':
                st.session_state['file_text'] = transcribe_audio(st.session_state['audio_to_transcribe'])
                if not st.session_state['file_summary']:
                    st.session_state['file_summary'] = get_description(st.session_state['file_text'])

# --- wyświetlanie transkrypcji i podsumowania ---
if source_label == 'Nagranie' and st.session_state['note_text']:
    st.text_area('Transkrypcja audio (nagranie)',
                 value=st.session_state['note_text'], disabled=True)
    st.text_area('Podsumowanie',
             value=st.session_state['note_summary'], disabled=True, height=200)
elif source_label == 'Plik' and st.session_state['file_text']:
    st.text_area('Transkrypcja audio (plik)',
                 value=st.session_state['file_text'], disabled=True)
    st.text_area('Podsumowanie',
             value=st.session_state['file_summary'], disabled=True, height=200)