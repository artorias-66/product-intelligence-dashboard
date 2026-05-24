FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (ffmpeg is needed for video extraction, tesseract for OCR, libgl1 for OpenCV)
RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr libgl1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
