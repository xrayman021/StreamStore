# python
import os
import sys
import json
import uuid
import logging
import socket
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def parse_bootstrap(bootstrap: str):
    return [s.strip() for s in bootstrap.split(",") if s.strip()]

def host_resolves(endpoint: str) -> bool:
    host = endpoint.split(":", 1)[0]
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False

# Read bootstrap from env so it's easy to override locally
bootstrap_env = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
endpoints = parse_bootstrap(bootstrap_env)

# Validate resolution early to produce a helpful error instead of silent retries
unresolved = [e for e in endpoints if not host_resolves(e)]
if unresolved:
    logging.error("Kafka bootstrap hosts not resolvable from this host: %s", unresolved)
    logging.error("Options: set `KAFKA_BOOTSTRAP` to a reachable address (e.g. localhost:9092) or run inside the Kafka network.")
    sys.exit(1)

producer_config = {"bootstrap.servers": bootstrap_env}
producer = Producer(producer_config)
logging.info("Producer configured with bootstrap.servers=%s", bootstrap_env)

def delivery_report(err, msg):
    if err:
        logging.error("Delivery failed: %s", err)
    else:
        key = msg.key().decode("utf-8") if msg.key() else None
        logging.info("Delivered key=%s to %s [%d] at offset %d", key, msg.topic(), msg.partition(), msg.offset())

def send_order(order: dict):
    value = json.dumps(order).encode("utf-8")
    key = order.get("order_id")
    try:
        producer.produce(topic="orders", key=key, value=value, callback=delivery_report)
        producer.poll(0)
    except BufferError:
        logging.warning("Local producer queue full, flushing and retrying")
        try:
            producer.flush(timeout=2)
        except Exception as e:
            logging.error("Flush failed after BufferError: %s", e)
        producer.produce(topic="orders", key=key, value=value, callback=delivery_report)

    try:
        producer.flush(timeout=5)
    except Exception as e:
        logging.error("producer.flush failed: %s", e)

if __name__ == "__main__":
    order = {
        "order_id": uuid.uuid4().hex,
        "user": "chase",
        "item": "sausage pizza",
        "price": 100,
        "quantity": 2,
    }
    try:
        send_order(order)
    except KeyboardInterrupt:
        logging.info("Interrupted by user, exiting")
        try:
            producer.flush(timeout=1)
        except Exception:
            pass
        raise
