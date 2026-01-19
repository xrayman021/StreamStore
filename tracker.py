import json
import uuid

from confluent_kafka import Consumer, Producer

consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': "order-tracker",
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(consumer_config)

consumer.subscribe(["orders"])

print("Consumer is running and subscribed to topic 'orders'")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))

        value = msg.value().decode('utf-8')
        order = json.loads(value)
        print(f"Received order: {order['quantity']} x {order['price']} from {order['user']}")

except KeyboardInterrupt:
    print("Stopping consumer")

finally:
    consumer.close()