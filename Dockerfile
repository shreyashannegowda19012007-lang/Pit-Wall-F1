# Production Dockerfile for Pitwall F1 Platform
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and platform assets
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/
COPY track_cache/ ./track_cache/
COPY frontend/dist/ ./frontend/dist/
COPY run_app.py ./run_app.py
COPY .env.example .env

# Expose port for unified FastAPI + SPA (8000)
EXPOSE 8000

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Default command launches unified production server
CMD ["python", "run_app.py", "--prod", "--host", "0.0.0.0", "--port", "8000"]
