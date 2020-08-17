import json
import logging
from json import JSONDecodeError

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from urllib3 import Retry
from urllib3.exceptions import NewConnectionError

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class CryptowatDataFetcher(BaseFetcher):
    fetcher_name = "CRYPTOWATCH API"
    kafka_topic = "RAW_G_PRICE_VOLA"

    def __init__(self):
        self.session = Session()

        self.request_endpoints = {
            'BTC': {
                'Binance': 'market:binance:btcusdt',
                'Bitstamp': 'market:bitstamp:btcusd',
                'Huobi': 'market:huobi:btcusdt',
                'Kraken': 'market:kraken:btcusdt',
                'Okex': 'market:okex:btcusdt'
            },
            'ETH': {
                'Binance': 'market:binance:ethusdt',
                'Bitstamp': 'market:bitstamp:ethusd',
                'Huobi': 'market:huobi:ethusdt',
                'Kraken': 'market:kraken:ethusdt',
                'Okex': 'market:okex:ethusdt'
            }
        }

        self.stock_market_mappings = {
            'Binance': 'BIN',
            'Bitstamp': 'BIT',
            'Huobi': 'HUO',
            'Kraken': 'KRA',
            'Okex': 'OKE'
        }

        self.request_url = 'https://api.cryptowat.ch/markets/prices'

        self.session = Session()
        retries = Retry(total=2,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def get_data_from_cryptowat(self):
        try:
            response = self.session.get(self.request_url)
            json_payload = json.loads(response.text)
            timestamp = get_unix_timestamp()

            items = []
            for coin in self.request_endpoints:
                for stock_market in self.request_endpoints[coin]:
                    try:
                        items.append({
                            "timestamp": timestamp,
                            "coin": coin,
                            "stockMarket": self.stock_market_mappings[stock_market],
                            "price": json_payload["result"][self.request_endpoints[coin][stock_market]]
                        })
                    except KeyError:
                        catch_request_error({
                            "error": "Stock Market not found in result"
                        }, self.kafka_topic)
                        pass
            return items
        except (NewConnectionError, ConnectionError, Timeout, TooManyRedirects) as e:
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
        items = self.get_data_from_cryptowat()
        try:
            for entry in items:
                KafkaConnector().send_to_kafka(self.kafka_topic, entry)
        except Exception:
            catch_request_error({
                "error": "msg"
            }, self.kafka_topic)
        finally:
            self.run_app()


CryptowatDataFetcher()
