# Use lightweight Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# Note: pandas_ta is commented out in requirements.txt (incompatible with 3.14 locally), 
# but if needed for 3.11, it can be uncommented. 
# For now, we install what is active.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables if needed (or rely on .env pass-through)
# ENV PYTHONUNBUFFERED=1

# Command to run the bot
CMD ["python", "main.py"]
