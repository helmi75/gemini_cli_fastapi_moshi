FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Avoid interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    curl \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

WORKDIR /app

# Ensure python3 points to python3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Install dependencies
COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for secrets
RUN mkdir -p /app/secrets

# Default port
EXPOSE 8000

# Set environment variables for the app
ENV PYTHONUNBUFFERED=1

CMD ["python3.11", "main.py"]
