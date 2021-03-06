import json
import logging
import sys
from json import JSONDecodeError

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, KafkaConnector

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class EthplorerDataFetcher(BaseFetcher):
    fetcher_name = "Ethplorer Data Fetcher"
    kafka_topic = "RAW_E_TOKEN"

    def __init__(self):
        self.url = "https://api.ethplorer.io/getTopTokens?apiKey="
        self.session = Session()
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_data_from_api(self):
        try:
            api_key = HashiVaultCredentialStorage().get_credentials("Ethplorer", "API_KEY")[0]
            response = self.session.get(self.url + api_key)
            return json.loads(response.text)["tokens"]
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
        tokens = self.get_data_from_api()
        try:
            for token in tokens:
                if token["price"] is not False:
                    try:
                        KafkaConnector().send_to_kafka(self.kafka_topic, {
                            "timestamp": token["price"]["ts"],
                            "token": token["symbol"],
                            "address": token["address"],
                            "name": token["name"],
                            "holdersCount": token["holdersCount"],
                            "issuancesCount": token["issuancesCount"],
                            "txsCount": token["txsCount"],
                            "marketCapUsd": token["price"]["marketCapUsd"],
                            "availableSupply": token["price"]["availableSupply"],
                            "rate": token["price"]["rate"],
                            "volume24h": token["price"]["volume24h"]
                        })
                    except Exception:
                        catch_request_error({
                            "type": ErrorTypes.FETCH_ERROR,
                            "error": sys.exc_info()[0]
                        }, self.kafka_topic)
                        pass
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
        finally:
            KafkaConnector().flush()
            self.run_app()


EthplorerDataFetcher()
