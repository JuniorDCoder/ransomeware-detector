# ─────────────────────────────────────────────────────────────────────────────
#  Ransomware Detector — Dockerfile
#  Builds a single image that runs both the API server and the dashboard.
#  Ports: 5000 (API server), 5001 (dashboard)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# System deps for watchdog / psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies ───────────────────────────────────────────────
COPY requirements.runtime.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.runtime.txt

# ── Copy application ──────────────────────────────────────────────────────────
COPY . .

RUN pip install --no-cache-dir -e .

# ── Config defaults ───────────────────────────────────────────────────────────
RUN cp config.example.json config.json

# ── Expose ports ──────────────────────────────────────────────────────────────
EXPOSE 5000 5001

ENV RDS_SERVER_HOST=0.0.0.0 \
    RDS_DASHBOARD_HOST=0.0.0.0 \
    RDS_SERVER_PORT=5000 \
    RDS_DASHBOARD_PORT=5001

# ── Launcher ──────────────────────────────────────────────────────────────────
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
