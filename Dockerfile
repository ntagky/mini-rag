# Build Next.js
FROM oven/bun:1 AS frontend-builder

WORKDIR /frontend

COPY frontend .

RUN bun install

RUN bun run build


# Python Runtime
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libxcb1 \
    libgl1  \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py .

COPY .assets ./.assets
COPY documents ./documents

COPY --from=frontend-builder /frontend/out ./frontend/out

EXPOSE 8000

CMD ["python", "main.py", "api"]
