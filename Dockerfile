FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./

# Install Python dependencies (including dev dependencies for testing)
RUN uv pip install --system -e ".[dev]"

# Copy source code and tests
COPY src/ ./src/
COPY tests/ ./tests/

# Copy scripts directory
COPY scripts/ ./scripts/

# Copy Alembic migration files
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set Python path to include /app so src.* imports work
ENV PYTHONPATH=/app

# Keep working directory at /app
WORKDIR /app

# Expose port
EXPOSE 8000

# Default command - run from /app with src.main module
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
