# Use Python 3.10
FROM python:3.10-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the application using Gunicorn for stability
# Replace your old CMD with this one
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]