FROM python:3.11-slim

LABEL maintainer="UsenetSync Team"
LABEL description="UsenetSync - Secure Usenet Folder Synchronization"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash usenetsync

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN pip install -e .

# Create necessary directories
RUN mkdir -p data logs temp && \
    chown -R usenetsync:usenetsync /app

# Switch to app user
USER usenetsync

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from main import UsenetSync; app = UsenetSync(); print('OK')" || exit 1

# Default command
CMD ["python", "cli.py", "daemon"]
