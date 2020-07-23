import json
import logging
import sys
import threading
from json import JSONDecodeError

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from HashiVaultCredentialStorage import HashiVaultCredentialStorage
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector
from urllib.parse import urljoin

class CryptowatDataFetcher:
    fetcher_name = "CRYPTOWATCH API"
    kafka_topic = "RAW_G_PRICE_DIFF"

    def __init__(self):
        self.session = Session()
        url = 'https://api.cryptowat.ch/markets/'
        self.url_kraken_btc = urljoin(url, 'kraken/btcusd/price')
        self.url_binance_btc = urljoin(url, 'binance/btcusdt/price')
        self.url_okex_btc = urljoin(url, 'okex/btcusdt/price')
        self.url_bitstamp_btc = urljoin(url, 'bitstamp/btcusd/price')
        self.url_huobi_btc = urljoin(url, 'huobi/btcusdt/price')
        self.url_kraken_eth = urljoin(url, 'kraken/ethusd/price')
        self.url_binance_eth = urljoin(url, 'binance/ethusdt/price')
        self.url_okex_eth = urljoin(url, 'okex/ethusdt/price')
        self.url_bitstamp_eth = urljoin(url, 'bitstamp/ethusd/price')
        self.url_huobi_eth = urljoin(url, 'huobi/ethusdt/price')
        self.BTCKraken = None
        self.BTCBinance = None
        self.BTCOkex = None
        self.BTCBitmex = None
        self.BTCHuobi = None
        self.ETHKraken = None
        self.ETHBinance = None
        self.ETHOkex = None
        self.ETHBitmex = None
        self.ETHHuobi = None
        self.trigger_health_pings()
        self.process_data_fetch()
        self.session = Session()
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def get_data_from_cryptowat(self):
        try:
            response1 = self.session.get(self.url_kraken_btc)
            self.output1 = json.loads(response1.text)
            self.BTCKraken = self.output1["result"]["price"]
            response2 = self.session.get(self.url_binance_btc)
            self.output2 = json.loads(response2.text)
            self.BTCBinance = self.output2["result"]["price"]
            response3 = self.session.get(self.url_okex_btc)
            self.output3 = json.loads(response3.text)
            self.BTCOkex = self.output3["result"]["price"]
            response4 = self.session.get(self.url_bitstamp_btc)
            self.output4 = json.loads(response4.text)
            self.BTCBitstamp = self.output4["result"]["price"]
            response5 = self.session.get(self.url_huobi_btc)
            self.output5 = json.loads(response5.text)
            self.BTCHuobi = self.output5["result"]["price"]
            response6 = self.session.get(self.url_kraken_eth)
            self.output6 = json.loads(response6.text)
            self.ETHKraken = self.output6["result"]["price"]
            response7 = self.session.get(self.url_binance_eth)
            self.output7 = json.loads(response7.text)
            self.ETHBinance = self.output7["result"]["price"]
            response8 = self.session.get(self.url_okex_eth)
            self.output8 = json.loads(response8.text)
            self.ETHOkex = self.output8["result"]["price"]
            response9 = self.session.get(self.url_bitstamp_eth)
            self.output9 = json.loads(response9.text)
            self.ETHBitstamp = self.output9["result"]["price"]
            response10 = self.session.get(self.url_huobi_eth)
            self.output10 = json.loads(response10.text)
            self.ETHHuobi = self.output10["result"]["price"]
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            catch_request_error({
                "type": ErrorTypes.API_LIMIT_EXCEED,
                "error": e
            }, self.kafka_topic)
        except (TypeError, JSONDecodeError) as e:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": e
            }, self.kafka_topic)



    def process_data_fetch(self):
        self.get_data_from_cryptowat()
        try:
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "priceKraken": self.BTCKraken,
                "priceBinance": self.BTCBinance,
                "priceOkex": self.BTCOkex,
                "priceBitstamp": self.BTCBitstamp,
                "priceHuobi": self.BTCHuobi

            })
            KafkaConnector().send_to_kafka(self.kafka_topic, {
                "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "priceKraken": self.ETHKraken,
                "priceBinance": self.ETHBinance,
                "priceOkex": self.ETHOkex,
                "priceBitstamp": self.ETHBitstamp,
                "priceHuobi": self.ETHHuobi
                })
            print({
                "timestamp": get_unix_timestamp(),
                "coin": "BTC",
                "priceKraken": self.BTCKraken,
                "priceBinance": self.BTCBinance,
                "priceOkex": self.BTCOkex,
                "priceBitstamp": self.BTCBitstamp,
                "priceHuobi": self.BTCHuobi
                })
            print({
               "timestamp": get_unix_timestamp(),
                "coin": "ETH",
                "priceKraken": self.ETHKraken,
                "priceBinance": self.ETHBinance,
                "priceOkex": self.ETHOkex,
                "priceBitstamp": self.ETHBitstamp,
                "priceHuobi": self.ETHHuobi
                })

        except:
            catch_request_error({
                 "error": "msg"
            })

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()

CryptowatDataFetcher()

