import logging
import threading

from DWConfigs import DWConfigs
from GeneralUtils import catch_request_error, get_unix_timestamp
from KafkaConnector import KafkaConnector


class RawFetcherSkeleton:
    fetcher_name = "Raw Fetcher Skeleton"
    kafka_topic = "RAW_G_SAMPLE_FETCHER"

    def __init__(self):
        self.trigger_health_pings()
        self.process_data_fetch()
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def process_data_fetch(self):
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "abc": "def"
            })
        except:
            catch_request_error({
                "error": "msg"
            })

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


RawFetcherSkeleton()
