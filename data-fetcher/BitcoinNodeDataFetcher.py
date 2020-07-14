import logging
import sys
import threading

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, KafkaConnector

headers = {
    'Accept': 'application/json; indent=4',
}


class BitcoinNodeDataFetcher:
    fetcher_name = "Bitcoin Node Data Fetcher"
    kafka_topic = "RAW_G_NODE_DISTRIBUTION"

    def __init__(self):
        self.trigger_health_pings()
        self.process_data_fetch()
        self.response_list = None
        self.node_list = None
        self.only_nodes = None
        self.node_count = None
        self.timestamp = None
        self.countries_nodes = {}
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def request_data_from_bitcoinnode(self):
        try:
            self.response_list = requests.get("https://bitnodes.io/api/v1/snapshots/latest/", headers=headers)
            self.node_list = self.response_list.json()
            self.only_nodes = self.node_list["nodes"]
            # return node count and corresponding timestamp
            self.node_count = self.node_list["total_nodes"]
            self.timestamp = self.node_list["timestamp"]
            # create list with country symbols
            self.countries_nodes = {}
            for i in self.only_nodes.values():
                # exists in list
                if i[7] in self.countries_nodes:
                    self.countries_nodes[i[7]] += 1
                else:
                    self.countries_nodes[i[7]] = 1
            del self.countries_nodes[None]

        except(ConnectionError, Timeout, TooManyRedirects) as e:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)

    def process_data_fetch(self):
        self.request_data_from_bitcoinnode()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": self.timestamp,
                "nodeCount": self.node_count,
                "countries": self.countries_nodes,
                "coin": 'BTC'
            })
            print({
                "timestamp": self.timestamp,
                "nodeCount": self.node_count,
                "countries": self.countries_nodes
            })
        except:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


BitcoinNodeDataFetcher()
