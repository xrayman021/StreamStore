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

# copy both scripts into the image
COPY producer.py tracker.py /app/

RUN pip install --no-cache-dir confluent-kafka

# default command (override per-service in Compose)
CMD ["python", "producer.py"]