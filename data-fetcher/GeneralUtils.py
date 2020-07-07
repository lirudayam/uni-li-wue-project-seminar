import logging
from datetime import time

from KafkaConnector import KafkaConnector


def get_unix_timestamp():
    return int(time.time())


def catch_request_error(error):
    logging.error('Error while fetching', exc_info=error)
    KafkaConnector().forward_error(error)


def on_send_success(record_metadata):
    logging.info('Successful sending to Kafka (' + record_metadata.topic + ')')


def on_send_error(exception):
    logging.error('Error while sending to Kafka', exc_info=exception)
    KafkaConnector().forward_error(exception)
