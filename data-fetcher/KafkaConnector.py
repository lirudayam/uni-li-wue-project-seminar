import json
import logging
import os
import time
from json.decoder import JSONDecodeError

from kafka import KafkaProducer

os.environ["KAFKA_BOOTSTRAP_SERVER"] = '132.187.226.20:9092'
logging.basicConfig(filename='output.log', level=logging.ERROR)


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
        try:
            self.producer.send(topic, dict_elm).add_callback(on_send_success).add_errback(on_send_error)
            self.producer.flush()
        except JSONDecodeError as e:
            self.forward_error({
                "error": "Failed to send to Kafka"
            })

    def forward_error(self, error):
        self.producer.send('RAW_FETCH_ERRORS', error).add_callback(on_send_success).add_errback(on_send_error)
        self.producer.flush()

    def send_health_ping(self, fetcher_name):
        self.producer.send('RAW_HEALTH_CHECKS', fetcher_name).add_callback(on_send_success).add_errback(on_send_error)
        self.producer.flush()


def get_unix_timestamp():
    return int(time.time())


def catch_request_error(error, kafka_topic):
    logging.error('Error while fetching', exc_info=error)
    error['topic'] = kafka_topic
    error['timestamp'] = get_unix_timestamp()
    KafkaConnector().forward_error(error)


def on_send_success(record_metadata):
    logging.info('Successful sending to Kafka (' + record_metadata.topic + ')')


def on_send_error(exception):
    logging.error('Error while sending to Kafka', exc_info=exception)
    KafkaConnector().forward_error(exception)

# Sample how to use it
# KafkaConnector().send_to_kafka("my-test-kafka", {"abc": "def"})
