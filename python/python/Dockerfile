# syntax=docker/dockerfile:1
# Stufe 1: Abhängigkeiten aus uv.lock (gesperrt) in eine virtuelle Umgebung installieren
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stufe 2: schlankes Laufzeitabbild, Nicht-Root
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH"
RUN useradd --system --uid 10001 --no-create-home chronos
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY chronos ./chronos
USER 10001
ENTRYPOINT ["python", "-m", "chronos"]
CMD ["web"]
