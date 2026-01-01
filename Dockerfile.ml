# Railway ML Training Dockerfile
# Optimized for ML workloads with GPU support consideration

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for ML and data science
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    wget \
    libgomp1 \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    wget \
    libgomp1 \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-railway.txt .

# Install Python dependencies in layers for better caching
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core scientific libraries first (less likely to change)
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    pandas==2.0.3 \
    scipy==1.11.3

# Install ML libraries
RUN pip install --no-cache-dir \
    scikit-learn==1.3.0 \
    xgboost==1.7.6 \
    joblib==1.3.2

# CACHE_BUST: 20260101-1416 - Force rebuild with tarball instead of git clone
# Install data and API libraries (using ta instead of pandas-ta/TA-Lib)
RUN pip install --no-cache-dir \
    ta==0.11.0 \
    yfinance==0.2.18 \
    python-binance==1.0.19 \
    requests==2.31.0

# Install Flask and utilities
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    werkzeug==2.3.7 \
    tqdm==4.65.0 \
    python-dotenv==1.0.0 \
    gunicorn==21.2.0

# Copy source code
COPY railway_ml_train.py .
COPY ml_training_client.py .
COPY ta_compat.py .
COPY test_startup.py .
COPY src/ ./src/
COPY system_directive.py .
COPY compatibility_imports.py .

# Create necessary directories
RUN mkdir -p nexus_system/memory_archives training_logs

# Set proper permissions
RUN chmod +x railway_ml_train.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command (temporarily using test script for debugging)
CMD ["python", "test_startup.py"]
