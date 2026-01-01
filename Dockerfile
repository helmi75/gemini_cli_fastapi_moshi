FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Avoid interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for secrets
RUN mkdir -p /app/secrets

# Default port
EXPOSE 8000

# Set environment variables for the app
ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]
