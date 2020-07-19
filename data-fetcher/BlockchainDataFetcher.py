import logging
import threading

from DWConfigs import DWConfigs
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

from requests import Session, Request
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': '0ef3ae36-7d23-4451-b552-4e0108c1a9a9',
}


class BlockchainDataFetcher:
    fetcher_name = "BlockchainCom Data Fetcher"
    kafka_topic = "RAW_G_BLOCK_STATS"

    def __init__(self):
        self.url = 'https://api.blockchain.info/stats'
        self.session = Session()
        self.session.headers.update(headers)
        self.trigger_health_pings()
        self.process_data_fetch()
        self.output = None
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_data_from_blockchain(self):
        try:
            response = self.session.get(self.url)
            self.output = json.loads(response.text)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


    def process_data_fetch(self):
        self.get_data_from_blockchain()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "blocktime": self.output['minutes_between_blocks'],
                "nextretarget": self.output['nextretarget'],
                "difficulty": self.output['difficulty'],
                "estimated_btc_sent": self.output['estimated_btc_sent'],
                "miners_revenue_btc": self.output['miners_revenue_btc'],
            })
            print({
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "blocktime": self.output['minutes_between_blocks'],
                "nextretarget": self.output['nextretarget'],
                "difficulty": self.output['difficulty'],
                "estimated_btc_sent": self.output['estimated_btc_sent'],
                "miners_revenue_btc": self.output['miners_revenue_btc'],
            })
        except:
            catch_request_error({
                "error": "ERROR"
            })
        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


BlockchainDataFetcher()
