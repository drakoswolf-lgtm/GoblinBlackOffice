# Dockerfile — Ledgergut self-hosted deployment
# Builds a container image with Python, Tesseract, and Gunicorn.
FROM python:3.12-slim

RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir flask pillow pytesseract gunicorn

COPY app/ ./app/

# All persistent data (receipts, images, any future app data) lives under /data.
# Mount a named volume at /data to persist across container restarts.
ENV LEDGERGUT_RUNTIME=/data

EXPOSE 8080

CMD ["gunicorn", "app.ledgergut.web:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "120"]
