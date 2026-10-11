# GDB backend microservice — containerized (Python 3.12)
# Built & run by docker-compose.yml. Local (non-Docker) flow is unaffected.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PIP_NO_CACHE_DIR=1

# Build tools for asyncpg / bcrypt wheels + libpq for the Postgres drivers.
RUN apt-get update && apt-get install -y --no-install-recommends         build-essential libpq-dev     && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching).
COPY libs /libs
COPY accounts_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code only (see .dockerignore for what's excluded).
COPY accounts_service/app ./app
RUN mkdir -p /app/logs

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
