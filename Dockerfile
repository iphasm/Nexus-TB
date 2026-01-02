# Multi-stage build for Nexus-TB
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set PATH to use the installed packages
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy all critical production files
COPY nexus_loader.py .
COPY main.py .
COPY config.yaml .

# Copy all package directories
COPY handlers/ ./handlers/
COPY nexus_system/ ./nexus_system/
COPY servos/ ./servos/
COPY utils/ ./utils/
COPY models/ ./models/

# Create necessary directories for runtime
RUN mkdir -p logs data cache models/weights

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default entry point
CMD ["python", "main.py"]
