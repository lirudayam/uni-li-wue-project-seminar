import logging
import threading

from DWConfigs import DWConfigs
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

from requests import Session, Request
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': 'ef16ee68-9b87-48f2-9287-4e0899ff6d07',
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
            print(e)


    def process_data_fetch(self):
        self.get_data_from_coinmarketcap()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "BitcoinPrice": self.Bitcoin["USD"]["price"],
                "BitcoinMarketCap": self.Bitcoin["USD"]["market_cap"],
                "BitcoinVolume24h": self.Bitcoin["USD"]["volume_24h"],
                "BitcoinChange24h": self.Bitcoin["USD"]["percent_change_24h"]
            })
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "EthereumPrice": self.Ethereum["USD"]["price"],
                "EthereumMarketCap": self.Ethereum["USD"]["market_cap"],
                "EthereumVolume24h": self.Ethereum["USD"]["volume_24h"],
                "EthereumChange24h": self.Ethereum["USD"]["percent_change_24h"]
            })
            print({
                "timestamp": get_unix_timestamp(),
                "BitcoinPrice": self.Bitcoin["USD"]["price"],
                "EthereumPrice": self.Ethereum["USD"]["price"],
                "BitcoinMarketCap": self.Bitcoin["USD"]["market_cap"],
                "EthereumMarketCap": self.Ethereum["USD"]["market_cap"],
                "BitcoinVolume24h": self.Bitcoin["USD"]["volume_24h"],
                "EthereumVolume24h": self.Ethereum["USD"]["volume_24h"],
                "BitcoinChange24h": self.Bitcoin["USD"]["percent_change_24h"],
                "EthereumChange24h": self.Ethereum["USD"]["percent_change_24h"]
            })
        except:
            catch_request_error({
                "error": "ERROR"
            })


        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


CoinMarketCapDataFetcher()
