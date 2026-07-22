# ============================================================
# Dockerfile — Multi-stage build for Expense Tracker API
# ============================================================

# ────────────────────────────────────────
# Stage 1: Dependencies
# Install Python packages in a separate stage
# ────────────────────────────────────────
FROM python:3.11-slim AS dependencies

# Set working directory
WORKDIR /install

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install/packages -r requirements.txt


# ────────────────────────────────────────
# Stage 2: Final production image
# Minimal image with only what we need to run
# ────────────────────────────────────────
FROM python:3.11-slim AS final

# Install runtime system dependencies only (no build tools)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /install/packages /usr/local/lib/python3.11/site-packages/

# Copy application source code
COPY src/ ./src/

# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Health check — verify API is responding
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=60s \
    --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "src/main.py"]