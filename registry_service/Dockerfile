# GDB Service Registry — Service Discovery pattern (port 8010).
# Build context is the REPO ROOT so the shared libs/ package is reachable:
#   docker build -f registry_service/Dockerfile -t gdb/registry .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY libs /libs
COPY registry_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY registry_service/app ./app

EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
