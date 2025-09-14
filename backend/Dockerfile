# backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системні залежності (за потреби додай build-essential, gcc тощо)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо залежності
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копіюємо код бекенду
COPY backend /app/backend

# За замовчанням Railway задає PORT
ENV PORT=8000 \
    HOST=0.0.0.0

# Команда запуску
CMD ["bash", "-lc", "uvicorn backend.app.main:app --host ${HOST} --port ${PORT}"]
