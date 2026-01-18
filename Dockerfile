# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set metadata
LABEL description="Discord Bot"
LABEL version="1.1"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CONFIG_FILE=info/info.json

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p soundboard info youtube temp voices

# Create volumes for persistent data
VOLUME ["/app/soundboard", "/app/info"]

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Run the bot with configurable JSON file (override CONFIG_FILE env var to change config)
CMD ["sh", "-c", "python3 BotHead.py --json ${CONFIG_FILE}"]
