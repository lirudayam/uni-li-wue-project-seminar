import re
import re
import sys
from datetime import datetime

import nltk
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from BaseFetcher import BaseFetcher
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector

nltk.download('vader_lexicon')


# noinspection PyMethodMayBeStatic
class StocktwitsDataFetcher(BaseFetcher):
    fetcher_name = "Stocktwits Fetcher Skeleton"
    kafka_topic = "RAW_G_STOCKTWITS_FETCHER"

    def __init__(self):
        self.list_ids_btc = []
        self.list_ids_eth = []
        self.complete_btcdataset = []
        self.complete_ethdataset = []
        BaseFetcher.__init__(self, self.kafka_topic, self.send_health_pings, self.process_data_fetch)

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.run_health()

    def process_data_fetch(self):
        self.get_data()
        try:
            for item in self.complete_btcdataset:
                if hasattr(item, 'id') and hasattr(item, 'sentiment') and hasattr(item, 'msg_sentimentscore') and hasattr(item, 'weighted_score'):
                    KafkaConnector().send_async_to_kafka(self.kafka_topic, {
                        "timestamp": item["created_at"],
                        "msgId": item["id"],
                        "sentiment": item["sentiment"],
                        "sentimentScore": item["msg_sentimentscore"],
                        "weightedScore": item["weighted_score"],
                        "coin": "BTC"
                    })

            for item in self.complete_ethdataset:
                if hasattr(item, 'id') and hasattr(item, 'sentiment') and hasattr(item, 'msg_sentimentscore') and hasattr(item, 'weighted_score'):
                    KafkaConnector().send_async_to_kafka(self.kafka_topic, {
                        "timestamp": item["created_at"],
                        "msgId": item["id"],
                        "sentiment": item["sentiment"],
                        "sentimentScore": item["msg_sentimentscore"],
                        "weightedScore": item["weighted_score"],
                        "coin": "ETH"
                    })
        except Exception:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)
            pass
        finally:
            KafkaConnector().flush()
            self.run_app()

    # -------------------------------------------------------------

    def query_request(self, ticker):
        url = "https://api.stocktwits.com/api/2/streams/symbol/%s.json" % ticker
        response = requests.get(url)
        return response.json()

    def sentiment(self, message):
        try:
            if message['entities']['sentiment'] is None:
                sentiment_value = 0
            else:
                msg = message['entities']['sentiment']['basic']
                if msg == "Bullish":
                    sentiment_value = 1
                else:
                    sentiment_value = -1
        except Exception:
            sentiment_value = 0
        finally:
            return sentiment_value

    def sentiment_analysis_score(self, text):
        return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]

    def clean_message(self, text):
        text = re.sub("[0-9]+", "number", text)
        text = re.sub("(\#|\n|@[^\s]+|(http|https):\/\/[^\s]*|[^\s]+@[^\s]+|[^a-z A-Z]+)", '', text)
        return text

    def get_data_line(self, ticker):
        data = self.query_request(ticker)

        # nested dictionary
        complete_dataset = []
        # copy global list (kafka)
        copy_list_ids = []
        if ticker == "BTC.X":
            copy_list_ids = self.list_ids_btc
        elif ticker == "ETH.X":
            copy_list_ids = self.list_ids_eth
        list_ids = []

        for message in data['messages']:
            dataset = {}
            text = self.clean_message(message['body'])
            sent = self.sentiment(message)
            sentiment_score = self.sentiment_analysis_score(text)
            # calculate the weighted score
            weighted_score = (sent + sentiment_score) / 2

            if message['id'] not in copy_list_ids:
                list_ids.append(message['id'])
                # Dictionary befüllen --> jeder Datensatz der 30
                dataset["id"] = message['id']
                dataset["sentiment"] = sent
                dataset["msg_sentimentscore"] = sentiment_score
                dataset["weighted_score"] = weighted_score
                dataset["created_at"] = datetime.datetime.strptime(message['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                # Enter dataset into the whole collection
                complete_dataset.append(dataset)
            else:
                print("nope")
                # check whether deletion of list is accurate

        # if within for or not - to be checked
        if ticker == "BTC.X":
            self.complete_btcdataset = complete_dataset
            self.list_ids_btc = list_ids
        elif ticker == "ETH.X":
            self.complete_ethdataset = complete_dataset
            self.list_ids_eth = list_ids

    def get_data(self):
        self.get_data_line("BTC.X")
        self.get_data_line("ETH.X")


StocktwitsDataFetcher()
