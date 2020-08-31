import json
import logging

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class BlockchainDataFetcher(BaseFetcher):
    fetcher_name = "BlockchainCom Data Fetcher"
    kafka_topic = "RAW_B_BLOCK"

    def __init__(self):
        self.url = 'https://api.blockchain.info/stats'
        self.session = Session()
        self.output = None
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_data_from_blockchain(self):
        try:
            self.session.headers.update({
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': HashiVaultCredentialStorage().get_credentials("Bitcoin", "X-CMC_PRO_API_KEY")[0]
            })
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
                "timestamp": float(self.output['timestamp']) / 1000,
                "blockTime": float(self.output['minutes_between_blocks']),
                "nextRetarget": float(self.output['nextretarget']),
                "difficulty": float(self.output['difficulty']),
                "estimatedSent": float(self.output['estimated_btc_sent']),
                "minersRevenue": float(self.output['miners_revenue_btc']),
                "blockSize": int(self.output['blocks_size'])
            })
        except Exception:
            catch_request_error({
                "error": "ERROR"
            }, self.kafka_topic)
        finally:
            self.run_app()


BlockchainDataFetcher()
