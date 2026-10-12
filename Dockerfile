FROM python:3.14-slim AS build
WORKDIR /app
RUN pip install --no-cache-dir uv==0.11.7
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
COPY scripts ./scripts
RUN .venv/bin/music-ml generate && .venv/bin/music-ml train

FROM python:3.14-slim AS runtime
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/artifacts /app/artifacts
ENV PATH="/app/.venv/bin:$PATH" MODEL_PATH=/app/artifacts/model.json PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"
CMD ["uvicorn", "music_ml.api:app", "--host", "0.0.0.0", "--port", "8000"]
