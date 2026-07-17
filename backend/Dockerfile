FROM python:3.14.6-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml README.md ./
COPY app ./app
RUN python -m pip install --prefix=/install .

FROM python:3.14.6-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/home/parkshield/.local/bin:$PATH
RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        ca-certificates \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system parkshield \
    && useradd --system --gid parkshield --create-home parkshield
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=parkshield:parkshield app ./app
COPY --chown=parkshield:parkshield migrations ./migrations
COPY --chown=parkshield:parkshield alembic.ini ./alembic.ini
USER parkshield
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
