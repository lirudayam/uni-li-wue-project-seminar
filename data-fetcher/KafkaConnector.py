import json
import logging

from kafka import KafkaProducer


# Singleton class for handling any connection and sending to Kafka
# WARNING: since python 3.7 async is a keyword, so a different package is required
# Install kafka package via: pip install kafka-python

class KafkaConnector:
    class __KafkaConnector:
        def __init__(self):
            self.producer = KafkaProducer(bootstrap_servers=['132.187.226.20:9092'],
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


def on_send_success(record_metadata):
    logging.info('Successful sending to Kafka (' + record_metadata.topic + ')')


def on_send_error(exception):
    logging.error('Error while sending to Kafka', exc_info=exception)
    KafkaConnector().forward_error(exception)

# Sample how to use it
# KafkaConnector().send_to_kafka("my-test-kafka", {"abc": "def"})
