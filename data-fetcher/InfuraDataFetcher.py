import logging
import os

from BaseFetcher import BaseFetcher
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import KafkaConnector, get_unix_timestamp

os.environ["WEB3_INFURA_PROJECT_ID"] = \
    HashiVaultCredentialStorage().get_credentials("Infura", "WEB3_INFURA_PROJECT_ID")[0]
os.environ["WEB3_INFURA_API_SECRET"] = \
    HashiVaultCredentialStorage().get_credentials("InfuraSecret", "WEB3_INFURA_API_SECRET")[0]

from web3.auto.infura import w3

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class InfuraDataFetcher(BaseFetcher):
    latest_identifier = 0
    fetcher_name = "INFURA API"
    kafka_topic = "RAW_E_BLOCK"

    def __init__(self):
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def process_data_fetch(self):
        if w3.isConnected():
            latest_block = dict(w3.eth.getBlock("latest"))

            if self.latest_identifier != latest_block['number']:
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "timestamp": get_unix_timestamp(),
                    "identifier": latest_block['number'],
                    "size": latest_block['size'],
                    "difficulty": latest_block['difficulty'],
                    "gasLimit": latest_block['gasLimit'],
                    "gasUsed": latest_block['gasUsed'],
                    "noOfTransactions": len(latest_block["transactions"])
                })
                print(latest_block['number'])
                self.latest_identifier = latest_block['number']

        self.run_app()


InfuraDataFetcher()
