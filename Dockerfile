# ============================================================================
# SPCH2TXT Server - Dockerfile
# ============================================================================
# Multi-stage Docker build for the Flask audio processing server
# Includes Whisper transcription and PyAnnote diarization

FROM python:3.13-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    gcc \
    g++ \
    make \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./

# Install Python dependencies for server only
# Note: pyaudio is only needed for client UI, not the server
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask>=3.0.0,\<4.0.0 \
    flask-cors>=5.0.0,\<6.0.0 \
    werkzeug>=3.0.0,\<4.0.0 \
    openai-whisper>=20250625,\<20250626 \
    pyannote-audio==3.1.1 \
    torch==2.8.* \
    torchaudio==2.8.* \
    openai>=2.6.0,\<3.0.0 \
    python-dotenv>=1.1.1,\<2.0.0 \
    ffmpeg-python>=0.2.0,\<0.3.0 \
    requests>=2.32.0,\<3.0.0 \
    watchdog>=4.0.0,\<5.0.0

# Copy application source code
COPY src/ ./src/
COPY .env.example ./.env.example

# Create directories for output files
RUN mkdir -p /app/src/saved_audio /app/src/saved_transcripts /app/src/saved_summary

# Expose Flask server port
EXPOSE 5001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.server.app

# Run the Flask server
CMD ["python", "-m", "src.server.app"]
