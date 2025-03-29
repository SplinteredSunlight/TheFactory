FROM python:3.10-slim AS base

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Dagger SDK
RUN pip install --no-cache-dir dagger-io>=0.8.1 pydagger>=0.3.0

# Install monitoring and logging tools
RUN pip install --no-cache-dir \
    prometheus-client>=0.16.0 \
    structlog>=23.1.0 \
    opentelemetry-distro>=0.50b0 \
    opentelemetry-exporter-otlp-proto-http>=1.29.0

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p /app/workflows /app/logs

# Set permissions
RUN chmod +x /app/deploy/entrypoint.sh

# Expose ports
EXPOSE 8000

# Run the application
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]