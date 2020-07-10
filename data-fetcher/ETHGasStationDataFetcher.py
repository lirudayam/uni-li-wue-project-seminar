import json
import logging
import threading

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector


class ETHGasStationDataFetcher:
    fetcher_name = "Eth Gas Station Data Fetcher"
    kafka_topic = "RAW_E_GASSTATION"

    def __init__(self):
        self.url = "https://ethgasstation.info/api/ethgasAPI.json"
        self.session = Session()
        self.trigger_health_pings()
        self.process_data_fetch()
        self.x10Gwei = None
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_data_from_gasstation(self):
        try:
            response = self.session.get(self.url)
            self.output = json.loads(response.text)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)

    def x10gweitoether(gwei):
        ether = (gwei / 10 ** 10)
        return ether

    def process_data_fetch(self):
        self.get_data_from_gasstation()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "safeGasPrice": self.output["safeLow"],  #this unit divided by 10 = Gwei (Gwei to Ether = divide by 10^9) --> then convert to USD according to current rate
                "blockNumber": self.output["blockNum"],
                "blockTime": self.output["block_time"]
            })
            print({
                "timestamp": get_unix_timestamp(),
                "safeGasPrice": self.output["safeLow"],
                "blockNumber": self.output["blockNum"],
                "blockTime": self.output["block_time"]
            })
        except:
            catch_request_error({
                "error": "ERROR"
            })


        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


ETHGasStationDataFetcher()
