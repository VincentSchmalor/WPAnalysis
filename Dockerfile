FROM python:3.13.3-slim
WORKDIR /app

# Optional: Falls requirements.txt existiert
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Inhalt des aktuellen Verzeichnisses in das Container-Verzeichnis
COPY . /app/

# Setze den PYTHONPATH, damit Python den Ordner /app als Modul-Verzeichnis erkennt
ENV PYTHONPATH=/app

# Zeitzone setzen
ENV TZ=Europe/Berlin
RUN apt-get update && apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/Europe/Berlin /etc/localtime && echo "Europe/Berlin" > /etc/timezone

# Starte die Anwendung
CMD ["python", "app/app.py"]