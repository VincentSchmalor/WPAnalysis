FROM python:3.13.3-slim
WORKDIR /app

# Optional: Falls requirements.txt existiert
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt || true

# Kopiere den gesamten Inhalt des aktuellen Verzeichnisses in das Container-Verzeichnis
COPY . /app/

# Setze den PYTHONPATH, damit Python den Ordner /app als Modul-Verzeichnis erkennt
ENV PYTHONPATH=/app

# Starte die Anwendung
CMD ["python", "app/app.py"]