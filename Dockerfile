FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps required by confluent-kafka
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    librdkafka-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# copy scripts and UI
COPY producer.py tracker.py api.py ui/ /app/

# install python deps
RUN pip install --no-cache-dir confluent-kafka fastapi "uvicorn[standard]"

# default (can be overridden by docker-compose)
CMD ["python", "producer.py"]