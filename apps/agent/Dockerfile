# Cloud Run runs this. Python 3.11 to match the ADK toolchain.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so a code change does not reinstall the world.
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
      "google-adk>=2.8.0" \
      "google-cloud-firestore>=2.19.0" \
      "pydantic>=2.9.0" \
      "pyyaml>=6.0.2" \
      "fastapi>=0.115" \
      "uvicorn[standard]>=0.30"

COPY src/ ./src/
COPY data/ ./data/
COPY server.py ./

ENV PYTHONPATH=/app/src

# Cloud Run supplies PORT; default keeps local `docker run` working.
ENV PORT=8080
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT}
