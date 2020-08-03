import logging
import threading

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

from requests import Session, Request
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


class BlockchainDataFetcher:
    fetcher_name = "BlockchainCom Data Fetcher"
    kafka_topic = "RAW_B_BLOCK"

    def __init__(self):
        self.url = 'https://api.blockchain.info/stats'
        self.session = Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': HashiVaultCredentialStorage().get_credentials("Bitcoin", "X-CMC_PRO_API_KEY")[0]
        })
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
            catch_request_error({
                "type": ErrorTypes.API_LIMIT_EXCEED,
                "error": e
            }, self.kafka_topic)
            pass

    def process_data_fetch(self):
        self.get_data_from_blockchain()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "blockTime": self.output['minutes_between_blocks'],
                "nextRetarget": self.output['nextretarget'],
                "difficulty": self.output['difficulty'],
                "estimatedSent": self.output['estimated_btc_sent'],
                "minersRevenue": self.output['miners_revenue_btc'],
            })
        except:
            catch_request_error({
                "error": "ERROR"
            })
        finally:
            s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
            s.start()


BlockchainDataFetcher()
