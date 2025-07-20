# Multi-stage build for CashCow application
# Stage 1: Build the frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY src/cashcow/web/frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY src/cashcow/web/frontend/ ./

# Build the frontend
RUN npm run build

# Stage 2: Python application
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --without dev

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY entities/ ./entities/
COPY scenarios/ ./scenarios/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./src/cashcow/web/frontend/build

# Create necessary directories
RUN mkdir -p /app/logs /app/reports /app/data

# Set environment variables
ENV PYTHONPATH=/app/src
ENV CASHCOW_CONFIG_DIR=/app/config
ENV CASHCOW_ENTITIES_DIR=/app/entities
ENV CASHCOW_SCENARIOS_DIR=/app/scenarios
ENV DEVELOPMENT_MODE=false

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "cashcow.web.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]