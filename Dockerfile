# Use lightweight Python 3.11
FROM public.ecr.aws/docker/library/python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# We need build tools for some packages (like pycares)
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (pandas-ta-openbb now included in requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables if needed (or rely on .env pass-through)
# ENV PYTHONUNBUFFERED=1

# Command to run the bot (Async version)
CMD ["python", "nexus_loader.py"]
