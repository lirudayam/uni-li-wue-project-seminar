import json
import logging
import sys

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

logging.basicConfig(filename='output.log', level=logging.INFO)


class CoinMarketCapDataFetcher(BaseFetcher):
    fetcher_name = "CoinMarketCap Data Fetcher"
    kafka_topic = "RAW_G_PRICES"

    def __init__(self):
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        self.parameters = {'slug': "bitcoin,ethereum,ren"}
        self.session = Session()
        self.bitcoin = None
        self.ethereum = None
        self.ren = None
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_data_from_coinmarketcap(self):
        try:
            self.session.headers.update({
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY':
                    HashiVaultCredentialStorage().get_credentials("CoinMarketCap", "X-CMC_PRO_API_KEY")[0]
            })
            response = self.session.get(self.url, params=self.parameters)
            output = json.loads(response.text)
            btc_raw = output["data"]["1"]
            eth_raw = output["data"]["1027"]
            ren_raw = output["data"]["2539"]

            self.bitcoin = btc_raw["quote"]
            self.ethereum = eth_raw["quote"]
            self.ren = ren_raw["quote"]

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            catch_request_error({
                "type": ErrorTypes.API_LIMIT_EXCEED,
                "error": e
            }, self.kafka_topic)
            pass
        except:
            pass

    def process_data_fetch(self):
        self.get_data_from_coinmarketcap()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "price": self.bitcoin["USD"]["price"],
                "marketCap": self.bitcoin["USD"]["market_cap"],
                "volume24h": self.bitcoin["USD"]["volume_24h"],
                "change24h": self.bitcoin["USD"]["percent_change_24h"] / 100
            })
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "price": self.ethereum["USD"]["price"],
                "marketCap": self.ethereum["USD"]["market_cap"],
                "volume24h": self.ethereum["USD"]["volume_24h"],
                "change24h": self.ethereum["USD"]["percent_change_24h"] / 100
            })
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "REN",
                "price": self.ren["USD"]["price"],
                "marketCap": self.ren["USD"]["market_cap"],
                "volume24h": self.ren["USD"]["volume_24h"],
                "change24h": self.ren["USD"]["percent_change_24h"] / 100
            })
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
            pass
        finally:
            self.run_app()


CoinMarketCapDataFetcher()
