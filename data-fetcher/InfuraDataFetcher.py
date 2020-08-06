import logging
import os

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import KafkaConnector, catch_request_error, get_unix_timestamp

os.environ["WEB3_INFURA_PROJECT_ID"] = \
    HashiVaultCredentialStorage().get_credentials("Infura", "WEB3_INFURA_PROJECT_ID")[0]

from web3 import Web3
from web3.auto.infura import w3

logging.basicConfig(filename='output.log', level=logging.INFO)


class InfuraDataFetcher(BaseFetcher):
    latest_identifier = 0
    fetcher_name = "INFURA API"
    kafka_topic = "RAW_E_BLOCK"

    def __init__(self):
        self.web3 = False
        self.get_connection()
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_connection(self):
        # init connection
        if not self.web3:
            self.web3 = Web3(Web3.WebsocketProvider(
                "wss://mainnet.infura.io/ws/v3/" + HashiVaultCredentialStorage().get_credentials("Infura",
                                                                                                 "WEB3_INFURA_PROJECT_ID")[
                    0]))

        # check for connection
        if self.web3.isConnected():
            return self.web3
        else:
            catch_request_error({
                "type": ErrorTypes.GENERAL_ERROR,
                "error": "No Connection anymore"
            }, self.kafka_topic)
            self.web3 = False

    def process_data_fetch(self):
        self.get_connection()
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
