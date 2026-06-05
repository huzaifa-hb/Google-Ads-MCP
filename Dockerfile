FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8080

WORKDIR /app

COPY pyproject.toml README.md ./
COPY docs ./docs
COPY src ./src

RUN pip install --no-cache-dir .

CMD ["python", "-m", "google_ads_mcp"]

