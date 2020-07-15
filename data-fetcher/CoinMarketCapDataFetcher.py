import json
import logging
import sys
import threading

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': HashiVaultCredentialStorage().get_credentials("CoinMarketCap", "X-CMC_PRO_API_KEY")[0]
}


class CoinMarketCapDataFetcher:
    fetcher_name = "CoinMarketCap Data Fetcher"
    kafka_topic = "RAW_G_PRICES"

    def __init__(self):
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        self.parameters = {'slug': "bitcoin,ethereum"}
        self.session = Session()
        self.session.headers.update(headers)
        self.trigger_health_pings()
        self.process_data_fetch()
        self.output = None
        self.Bitcoin = None
        self.Ethereum = None
        self.BitcoinRaw = None
        self.EthereumRaw = None
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_data_from_coinmarketcap(self):
        try:
            response = self.session.get(self.url, params=self.parameters)
            self.output = json.loads(response.text)
            self.BitcoinRaw = self.output["data"]["1"]
            self.EthereumRaw = self.output["data"]["1027"]
            self.Bitcoin = self.BitcoinRaw["quote"]
            self.Ethereum = self.EthereumRaw["quote"]

        except (ConnectionError, Timeout, TooManyRedirects) as e:
            catch_request_error({
                "type": ErrorTypes.API_LIMIT_EXCEED,
                "error": e
            }, self.kafka_topic)

    def process_data_fetch(self):
        self.get_data_from_coinmarketcap()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "price": self.Bitcoin["USD"]["price"],
                "marketCap": self.Bitcoin["USD"]["market_cap"],
                "volume24h": self.Bitcoin["USD"]["volume_24h"],
                "change24h": self.Bitcoin["USD"]["percent_change_24h"]
            })
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "price": self.Ethereum["USD"]["price"],
                "marketCap": self.Ethereum["USD"]["market_cap"],
                "volume24h": self.Ethereum["USD"]["volume_24h"],
                "change24h": self.Ethereum["USD"]["percent_change_24h"]
            })
        except:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


CoinMarketCapDataFetcher()
