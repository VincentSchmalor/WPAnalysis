FROM python:3.11-slim
WORKDIR /app

# Optional: falls requirements.txt existiert
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . .

CMD ["python", "app.py"]
