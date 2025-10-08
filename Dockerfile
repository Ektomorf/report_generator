# Multi-stage Dockerfile for Test Results Archive System
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY schema.sql ./
COPY web/ ./web/

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/logs

# Expose ports
# 8000 for FastAPI backend
# 8080 for web frontend (served by Python's http.server)
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/stats/summary')" || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
