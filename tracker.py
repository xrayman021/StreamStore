# python
import os
import json
import logging
from confluent_kafka import Consumer

logging.basicConfig(level=logging.INFO)
consumer_config = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP', 'localhost:9092'),
    'group.id': "order-tracker",
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_config)
consumer.subscribe(["orders"])

logging.info("Consumer is running and subscribed to topic `orders`")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logging.error("Consumer error: %s", msg.error())
            continue
        try:
            value = msg.value().decode('utf-8')
            order = json.loads(value)
        except Exception:
            logging.exception("Failed to parse message, skipping")
            continue
        logging.info("Received order: %s x %s from %s", order.get('quantity'), order.get('price'), order.get('user'))
        consumer.commit(asynchronous=False)
except KeyboardInterrupt:
    logging.info("Stopping consumer")
finally:
    consumer.close()
