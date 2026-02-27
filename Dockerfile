# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build deps
RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY cvmaker/ cvmaker/

# Install the package + deploy extra (gunicorn)
RUN pip install --no-cache-dir ".[deploy]"

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

# System libraries required by WeasyPrint (Cairo, Pango, GDK-Pixbuf + fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libharfbuzz0b \
        libfontconfig1 \
        shared-mime-info \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY cvmaker/ cvmaker/

# Non-root user for security
RUN useradd -r -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

# 2 workers is plenty for a personal/small-team tool.
# Increase to (2 * CPU cores + 1) for heavier use.
CMD gunicorn \
      --bind "0.0.0.0:${PORT}" \
      --workers 2 \
      --timeout 120 \
      --access-logfile - \
      "cvmaker.web_server:app"
