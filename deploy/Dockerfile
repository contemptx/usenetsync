# Dockerfile for UsenetSync Unified System
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash usenetsync

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Create necessary directories
RUN mkdir -p /data /logs /config && \
    chown -R usenetsync:usenetsync /app /data /logs /config

# Switch to non-root user
USER usenetsync

# Environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data
ENV LOG_DIR=/logs
ENV CONFIG_DIR=/config

# Expose ports
EXPOSE 8000  # API
EXPOSE 9090  # Prometheus metrics

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.unified.unified_system import UnifiedSystem; print('OK')" || exit 1

# Default command
CMD ["python", "src/unified/main.py", "--config", "/config/usenetsync.conf"]