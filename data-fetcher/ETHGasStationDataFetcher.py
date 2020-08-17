import json
import logging
import sys
from json.decoder import JSONDecodeError

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, KafkaConnector

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class ETHGasStationDataFetcher(BaseFetcher):
    fetcher_name = "Eth Gas Station Data Fetcher"
    kafka_topic = "RAW_E_GASSTATION"

    def __init__(self):
        self.url = "https://ethgasstation.info/api/ethgasAPI.json"
        self.session = Session()
        self.request_output = None
        self.last_block_no = None
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_data_from_gasstation(self):
        try:
            response = self.session.get(self.url)
            self.request_output = json.loads(response.text)
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
        self.get_data_from_gasstation()
        try:
            if self.last_block_no != self.request_output["blockNum"]:
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "safeGasPrice": self.request_output["safeLow"],
                    # this unit divided by 10 = Gwei (Gwei to Ether = divide by 10^9)
                    # then convert to USD according to current rate
                    "blockNumber": self.request_output["blockNum"],
                    "blockTime": self.request_output["block_time"]
                })
            self.last_block_no = self.request_output["blockNum"]
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
        finally:
            self.run_app()


ETHGasStationDataFetcher()
