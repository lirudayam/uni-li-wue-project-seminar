import json
import logging
import sys
import threading
from json import JSONDecodeError

import cfscrape
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

logging.basicConfig(filename='output.log', level=logging.INFO)


class EtherscanDataFetcher:
    fetcher_name = "Etherscan Data Fetcher"
    kafka_topic = "RAW_G_NODE_DISTRIBUTION"

    def __init__(self):
        self.url = "https://etherscan.io/stats_nodehandler.ashx?t=1&code=&range=1&additional="
        self.trigger_health_pings()
        self.process_data_fetch()
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_data_from_node_dist_endpoint(self):
        try:
            response = cfscrape.CloudflareScraper().get(self.url)
            json_content = json.loads(response.content)
            countries_list = {}
            node_count = 0
            for country in json_content:
                if country["value"] is not 0:
                    countries_list[country["code"]] = country["value"]
                    node_count += country["value"]
            return countries_list, node_count
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            catch_request_error({
                "type": ErrorTypes.API_LIMIT_EXCEED,
                "error": e
            }, self.kafka_topic)
            pass
        except (TypeError, JSONDecodeError) as e:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": e
            }, self.kafka_topic)
            pass

    def process_data_fetch(self):
        countries_list, node_count = self.get_data_from_node_dist_endpoint()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "nodeCount": node_count,
                "countries": countries_list,
                "coin": 'ETH'
            })
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
        finally:
            s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
            s.start()


EtherscanDataFetcher()
