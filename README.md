#  Podcast Analyzer AI

## Opis projektu

Podcast Analyzer AI to aplikacja stworzona w Pythonie z wykorzystaniem biblioteki Streamlit oraz modeli OpenAI.

Jej zadaniem jest automatyczna transkrypcja oraz analiza podcastów dostarczonych przez użytkownika w postaci plików audio, plików wideo lub linków do serwisu YouTube.

## Główne funkcjonalności

- przesyłanie plików MP3, WAV oraz MP4,
- automatyczna konwersja plików wideo do formatu audio,
- transkrypcja nagrań z wykorzystaniem modelu Whisper,
- analiza treści przy użyciu modelu GPT-4o,
- generowanie:
  - krótkiego streszczenia,
  - najważniejszych wniosków,
  - kluczowych tematów,
  - najciekawszych cytatów.

## Wykorzystane technologie

- Python
- Streamlit
- OpenAI API (Whisper, GPT-4o)
- FFmpeg
- yt-dlp
- Pydub

## Plan rozwoju

W kolejnych etapach planowane jest:

- poprawa obsługi filmów z YouTube,
- zwiększenie odporności aplikacji na błędy,
- możliwość eksportu analizy do pliku PDF,
- rozbudowa interfejsu użytkownika.
