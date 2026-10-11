# GDB API Gateway — API Gateway pattern (single public entry point, port 8000).
# Build context is the REPO ROOT so the shared libs/ package is reachable:
#   docker build -f central_gateway_service/Dockerfile -t gdb/gateway .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY libs /libs
COPY central_gateway_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY central_gateway_service/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
