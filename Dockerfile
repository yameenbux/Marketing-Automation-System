# UNTESTED in the build environment (no Docker daemon was available). See docs/operations.md.
FROM python:3.12-slim

RUN apt-get update -q && apt-get install -y -q --no-install-recommends ffmpeg fonts-inter git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 mas
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[tts]" playwright==1.56.0 && python -m playwright install --with-deps chromium
COPY config ./config
COPY data ./data
COPY scripts ./scripts
RUN chown -R mas:mas /app
USER mas
ENV MAS_ROOT=/app PYTHONUNBUFFERED=1
# Calls `mas tick` every 15 minutes; tick decides what is due in Europe/London time.
CMD ["sh", "-c", "while true; do mas tick; sleep 900; done"]
