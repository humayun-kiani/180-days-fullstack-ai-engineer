# ============================================================
# Dockerfile — Multi-stage production image for FastAPI
# ============================================================

# ── Stage 1: Dependencies ────────────────────────────────────
FROM python:3.11-slim AS dependencies

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --target=/build/packages -r requirements.txt


# ── Stage 2: Production image ────────────────────────────────
FROM python:3.11-slim AS production

# Metadata
LABEL maintainer="Humayun Kiani"
LABEL day="Day 26 — 180-Day Full Stack AI Engineer Roadmap"

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

# Set working directory
WORKDIR /app

# Copy packages from build stage
COPY --from=dependencies /build/packages /usr/local/lib/python3.11/site-packages/

# Copy application code
COPY app/ ./app/

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root
USER appuser

# Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK \
    --interval=30s \
    --timeout=10s \
    --start-period=60s \
    --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command: gunicorn managing uvicorn workers
# -w 4: 4 worker processes
# -k uvicorn.workers.UvicornWorker: async ASGI workers
# --timeout 120: kill workers that take > 120s
# --access-logfile -: log to stdout
CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keepalive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]