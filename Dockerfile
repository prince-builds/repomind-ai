# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables for unbuffered logging and Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/app/repomind/data

WORKDIR /app

# Install git (required for GitPython repository cloning) and ca-certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy core engine and FastAPI backend source code
COPY repomind/ ./repomind/
COPY backend/ ./backend/

# Expose container port
EXPOSE 8000

# Start FastAPI application using Uvicorn, binding to 0.0.0.0 and dynamic $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
