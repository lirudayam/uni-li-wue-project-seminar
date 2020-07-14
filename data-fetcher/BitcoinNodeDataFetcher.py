import logging
import sys
import threading

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

headers = {
    'Accept': 'application/json; indent=4',
}

class BitcoinNodeDataFetcher:
    fetcher_name = "Bitcoin Node Data Fetcher"
    kafka_topic = "RAW_B_NODES"

    def __init__(self):
        self.trigger_health_pings()
        self.process_data_fetch()
        self.response_list = None
        self.nodeList =None
        self.only_nodes =None
        self.node_count = None
        self.timestamp =None
        self.values = None
        self.countries =None
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
            self.nodeList = self.response_list.json()
            self.only_nodes = self.nodeList["nodes"]
            # return node count and corresponding timestamp
            self.node_count = self.nodeList["total_nodes"]
            self.timestamp = self.nodeList["timestamp"]
            self.values = self.only_nodes.values()
            # create list with country symbols
            self.countries = []
            for i in self.values:
                self.countries.append(i[7])

        except(ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


    def process_data_fetch(self):
        self.request_data_from_bitcoinnode()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": self.timestamp,
                "nodeCount": self.node_count,
                "countries": self.countries
            })
            print({
                "timestamp": self.timestamp,
                "nodeCount": self.node_count,
                "countries": self.countries
            })
        except:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()

BitcoinNodeDataFetcher()