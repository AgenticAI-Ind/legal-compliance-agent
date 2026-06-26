# Multi-stage Dockerfile for Legal & Compliance Agent

# Stage 1: Base image with dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Stage 3: Application
FROM dependencies as application

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: Development
FROM application as development

USER root

# Install development tools
RUN pip install \
    pytest-watch \
    ipython \
    jupyter

USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 5: Production
FROM application as production

# Optimize for production
ENV ENVIRONMENT=production

# Use gunicorn for production
USER root
RUN pip install gunicorn

USER appuser

CMD ["gunicorn", "src.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
