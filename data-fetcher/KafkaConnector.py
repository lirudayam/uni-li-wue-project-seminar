import json
import logging
import os
import time
from json.decoder import JSONDecodeError

from kafka import KafkaProducer

from ErrorTypes import ErrorTypes

os.environ["KAFKA_BOOTSTRAP_SERVER"] = '132.187.226.20:9092'
logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


# Singleton class for handling any connection and sending to Kafka
# WARNING: since python 3.7 async is a keyword, so a different package is required
# Install kafka package via: pip install kafka-python

class KafkaConnector:
    class __KafkaConnector:
        def __init__(self):
            self.producer = KafkaProducer(bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVER', '132.187.226.20:9092')],
                                          value_serializer=lambda m: json.dumps(m, cls=EnumEncoder).encode('ascii'))

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
        except JSONDecodeError:
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
    logging.error('Error while fetching for %s', kafka_topic)
    logging.error(error)
    error['topic'] = kafka_topic
    error['timestamp'] = get_unix_timestamp()
    KafkaConnector().forward_error(error)


def on_send_success(record_metadata):
    logging.info('Successful sending to Kafka (' + record_metadata.topic + ')')


def on_send_error(exception):
    logging.error('Error while sending to Kafka ' + str(exception))
    KafkaConnector().forward_error(exception)


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in ErrorTypes.values():
            return {"__enum__": str(obj)}
        return json.JSONEncoder.default(self, obj)
