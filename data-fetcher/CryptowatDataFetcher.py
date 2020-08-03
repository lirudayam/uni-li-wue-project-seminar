import json
import logging
import threading
from json import JSONDecodeError

from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector


class CryptowatDataFetcher:
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
                    except KeyError as e:
                        catch_request_error({
                            "error": "Stock Market not found in result"
                        })
                        pass
            return items
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
        items = self.get_data_from_cryptowat()
        try:
            for entry in items:
                KafkaConnector().send_to_kafka(self.kafka_topic, entry)
        except:
            catch_request_error({
                "error": "msg"
            })
        finally:
            s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
            s.start()


CryptowatDataFetcher()
