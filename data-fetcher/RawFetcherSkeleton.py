import logging
import threading

from DWConfigs import DWConfigs
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

from requests import Session, Request
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json



class CoinMarketCap_DataFetcher:
    fetcher_name = "CoinMarketCap Data Fetcher"
    kafka_topic = "RAW_G_PRICES"

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
