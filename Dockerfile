# Image for the read-only API. The data is NOT inside the image: it is mounted at run time,
# read-only, so the same image serves whatever data folder you give it.
#
#   docker build -t bike-monitor-api .
#   docker run --rm -p 8000:8000 -v "${PWD}/data:/app/data:ro" bike-monitor-api

# Exact version: "python:3-slim" would silently become a different Python on a later build.
FROM python:3.14.4-slim

# No .pyc files in the image; logs appear at once instead of sitting in a buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies before code: this layer is rebuilt only when requirements.txt changes,
# not on every code edit, so rebuilding after a code change takes seconds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY collector/ collector/
COPY api/ api/

# Not root: if someone ever broke into the API process, they would not own the container.
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000

# Docker marks the container "unhealthy" if /health stops answering. Python's own urllib,
# because the slim image has no curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"]

# 0.0.0.0: listen on every network interface inside the container. 127.0.0.1 would only
# accept calls from inside the container itself, and the port mapping could not reach it.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
