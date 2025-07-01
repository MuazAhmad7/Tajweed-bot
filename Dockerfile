FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    git \
    procps \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -v werkzeug==2.2.3 && \
    pip install --no-cache-dir -v flask==2.2.2 && \
    pip install --no-cache-dir -v -r requirements.txt

# Copy test script first
COPY test_imports.py .

# Run import tests
RUN python test_imports.py

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p recordings temp_audio

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_DEBUG=1
ENV GUNICORN_CMD_ARGS="--log-level debug --timeout 120 --workers 1"

# Command to run the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app --log-level debug --capture-output --access-logfile - --error-logfile - 