import asyncio
import logging
import os
import threading

from DWConfigs import DWConfigs
from KafkaConnector import KafkaConnector, catch_request_error, get_unix_timestamp

os.environ["WEB3_INFURA_PROJECT_ID"] = "37e2249c8d5e41488a9fa7b67b7335b3"

from web3 import Web3
from web3.auto.infura import w3


class InfuraDataFetcher:
    latest_identifier = 0
    fetcher_name = "INFURA API"
    kafka_topic = "RAW_G_LATEST_BLOCK"

    def __init__(self):
        self.url = "wss://mainnet.infura.io/ws/v3/37e2249c8d5e41488a9fa7b67b7335b3"
        self.web3 = False

        self.trigger_health_pings()
        self.get_connection()
        self.register_listener_for_new_block()
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_connection(self):
        # init connection
        if not self.web3:
            self.web3 = Web3(Web3.WebsocketProvider(self.url))
            self.register_listener_for_new_block()

        # check for connection
        if self.web3.isConnected():
            return self.web3
        else:
            catch_request_error("No connection")
            self.web3 = False

    def register_listener_for_new_block(self):
        block_filter = w3.eth.filter('latest')
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    self.log_loop(block_filter, 2)))
        finally:
            loop.close()

    async def log_loop(self, event_filter, poll_interval):
        while True:
            for event in event_filter.get_new_entries():
                self.handle_new_block()
            await asyncio.sleep(poll_interval)

    def handle_new_block(self):
        latest_block = dict(w3.eth.getBlock("latest"))

        if self.latest_identifier != latest_block['number']:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "identifier": latest_block['number'],
                "size": latest_block['size'],
                "difficulty": latest_block['difficulty'],
                "gasLimit": latest_block['gasLimit'],
                "gasUsed": latest_block['gasUsed'],
                "noOfTransactions": len(latest_block["transactions"])
            })
            print({
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "identifier": latest_block['number'],
                "size": latest_block['size'],
                "difficulty": latest_block['difficulty'],
                "gasLimit": latest_block['gasLimit'],
                "gasUsed": latest_block['gasUsed'],
                "noOfTransactions": len(latest_block["transactions"])
            })
            self.latest_identifier = latest_block['number']

InfuraDataFetcher()
