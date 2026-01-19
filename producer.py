# python
import os
import json
import uuid
import logging
from confluent_kafka import Producer

logging.basicConfig(level=logging.INFO)
producer_config = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092'),
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err:
        logging.error("Delivery failed: %s", err)
    else:
        key = msg.key().decode('utf-8') if msg.key() else None
        logging.info("Delivered key=%s to %s [%d] at offset %d", key, msg.topic(), msg.partition(), msg.offset())

def send_order(order):
    value = json.dumps(order).encode('utf-8')
    key = order.get('order_id')
    try:
        producer.produce(topic='orders', key=key, value=value, callback=delivery_report)
        producer.poll(0)  # serve callbacks
    except BufferError:
        logging.warning("Local producer queue full, flushing and retrying")
        producer.flush()
        producer.produce(topic='orders', key=key, value=value, callback=delivery_report)
    producer.flush(timeout=10)

if __name__ == '__main__':
    order = {
        "order_id": uuid.uuid4().hex,
        "user": "chase",
        "item": "sausage pizza",
        "price": 100,
        "quantity": 2
    }
    send_order(order)
