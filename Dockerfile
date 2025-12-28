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

# Note: pandas_ta is commented out in requirements.txt (incompatible with 3.14 locally), 
# but if needed for 3.11, it can be uncommented. 
# For now, we install what is active.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Debug: verify folder exists
RUN ls -la

# Install pandas-ta from local fork (PyPI version requires Python 3.12+)
# Use explicit path with ./
COPY pandas_ta_openbb-0.4.22 ./pandas_ta_openbb-0.4.22
RUN pip install --no-cache-dir ./pandas_ta_openbb-0.4.22

# Set environment variables if needed (or rely on .env pass-through)
# ENV PYTHONUNBUFFERED=1

# Command to run the bot (Async version)
CMD ["python", "nexus_loader.py"]
