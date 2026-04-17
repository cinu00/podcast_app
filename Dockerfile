# bazowy obraz
FROM python:3.11-slim

# instalacja ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# ustaw katalog roboczy
WORKDIR /app

# kopiuj pliki
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# port streamlit
EXPOSE 8501

# uruchomienie appki
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]