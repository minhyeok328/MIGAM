FROM node:24.15.0-bookworm-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN node node_modules/typescript/bin/tsc --noEmit \
    && node node_modules/vite/bin/vite.js build --mode demo

FROM ghcr.io/astral-sh/uv:0.12.0 AS uv
FROM python:3.11-slim-bookworm AS python-build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-cache --no-install-project

FROM python:3.11-slim-bookworm AS demo
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:$PATH"
WORKDIR /app
RUN groupadd --gid 10001 migam && useradd --uid 10001 --gid migam --no-create-home migam
COPY --from=python-build /app/backend/.venv /app/backend/.venv
COPY backend/ /app/backend/
COPY sources.yaml /app/sources.yaml
COPY scripts/run_local_demo.py /app/scripts/run_local_demo.py
COPY --from=web /app/frontend/dist /app/frontend/dist
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).close()"
CMD ["python", "scripts/run_local_demo.py", "--dist", "frontend/dist", "--container", "--port", "8080"]
