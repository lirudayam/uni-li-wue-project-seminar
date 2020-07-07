import json
import os

from GeneralUtils import on_send_success, on_send_error
from kafka import KafkaProducer

os.environ["KAFKA_BOOTSTRAP_SERVER"] = '132.187.226.20:9092'


# Singleton class for handling any connection and sending to Kafka
# WARNING: since python 3.7 async is a keyword, so a different package is required
# Install kafka package via: pip install kafka-python

class KafkaConnector:
    class __KafkaConnector:
        def __init__(self):
            self.producer = KafkaProducer(bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')],
                                          value_serializer=lambda m: json.dumps(m).encode('ascii'))

    instance = None

    def __init__(self):
        if not KafkaConnector.instance:
            KafkaConnector.instance = KafkaConnector.__KafkaConnector()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def send_to_kafka(self, topic, dict_elm):
        self.producer.send(topic, dict_elm).add_callback(on_send_success).add_errback(on_send_error)
        self.producer.flush()

    def forward_error(self, error):
        self.producer.send('RAW_FETCH_ERRORS', error).add_callback(on_send_success).add_errback(on_send_error)
        self.producer.flush()

    def send_health_ping(self, fetcher_name):
        self.producer.send('RAW_HEALTH_CHECKS', fetcher_name).add_callback(on_send_success).add_errback(on_send_error)
        self.producer.flush()


# Sample how to use it
# KafkaConnector().send_to_kafka("my-test-kafka", {"abc": "def"})
