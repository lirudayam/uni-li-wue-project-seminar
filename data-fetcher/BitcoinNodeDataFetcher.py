import logging
import sys

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, KafkaConnector

headers = {
    'Accept': 'application/json; indent=4',
}
logging.basicConfig(filename='output.log', level=logging.INFO)


class BitcoinNodeDataFetcher(BaseFetcher):
    fetcher_name = "Bitcoin Node Data Fetcher"
    kafka_topic = "RAW_G_NODE_DISTRIBUTION"

    def __init__(self):
        self.response = None
        self.node_list = None
        self.only_nodes = None
        self.node_count = None
        self.timestamp = None
        self.countries_nodes = {}
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def request_data_from_bitcoinnode(self):
        try:
            self.response = requests.get("https://bitnodes.io/api/v1/snapshots/latest/", headers=headers)
            if self.response.status_code != 200:
                try:
                    snapshot_request = requests.get("https://bitnodes.io/api/v1/snapshots/", headers=headers)
                    latest_snapshot_url = snapshot_request.json()["results"][0]["url"]
                    self.response = requests.get(latest_snapshot_url, headers=headers)
                except Exception:
                    catch_request_error({
                        "type": ErrorTypes.FETCH_ERROR,
                        "error": "No snapshot available"
                    }, self.kafka_topic)
                    pass
                except:
                    pass

            self.node_list = self.response.json()
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

        except(ConnectionError, Timeout, TooManyRedirects):
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
            pass
        except:
            pass

    def process_data_fetch(self):
        self.request_data_from_bitcoinnode()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": self.timestamp,
                "nodeCount": self.node_count,
                "countries": self.countries_nodes,
                "coin": 'BTC'
            })
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
        finally:
            self.run_app()


BitcoinNodeDataFetcher()
