import logging
import sys
import threading
import nltk
import requests
import json
import re

from DWConfigs import DWConfigs
from ErrorTypes import ErrorTypes
from KafkaConnector import catch_request_error, get_unix_timestamp, KafkaConnector
from nltk.sentiment.vader import SentimentIntensityAnalyzer
#nltk.downloader.download('vader_lexicon')


class StocktwitsDataFetcher:
    fetcher_name = "Stocktwits Fetcher Skeleton"
    kafka_topic = "RAW_G_STOCKTWITS_FETCHER"

    def __init__(self):
        self.list_ids_btc = []
        self.list_ids_eth = []
        self.complete_btcdataset = []
        self.complete_ethdataset = []
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

    def process_data_fetch(self):
        self.get_data()
        try:
            for i in range(len(self.complete_btcdataset)):
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "timestamp": get_unix_timestamp(),
                    "msgId": self.complete_btcdataset[i]["id"],
                    "sentiment": self.complete_btcdataset[i]["sentiment"],
                    "sentimentScore": self.complete_btcdataset[i]["msg_sentimentscore"],
                    "weightedScore": self.complete_btcdataset[i]["weighted_score"],
                    "coin": "BTC"
                })

            for i in range(len(self.complete_ethdataset)):
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "timestamp": get_unix_timestamp(),
                    "msgId": self.complete_ethdataset[i]["id"],
                    "sentiment": self.complete_ethdataset[i]["sentiment"],
                    "sentimentScore": self.complete_ethdataset[i]["msg_sentimentscore"],
                    "weightedScore": self.complete_ethdataset[i]["weighted_score"],
                    "coin": "ETH"
                })
        except:
            catch_request_error({
                "type": ErrorTypes.FETCH_ERROR,
                "error": sys.exc_info()[0]
            }, self.kafka_topic)

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()

    #-------------------------------------------------------------

    def query_request(self, ticker):
        url = "https://api.stocktwits.com/api/2/streams/symbol/%s.json" % ticker
        response = requests.get(url)
        return json.loads(response.text)

    def sentiment(self, message):
        try:
            msg = message['entities']['sentiment']['basic']
            if msg == "Bullish":
                sentiment_value = 1
            else:
                sentiment_value = -1
        except:
            sentiment_value = 0
        return sentiment_value

    def sentiment_analysis_score(self, text):
        return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]

    def clean_message(self, text):
        text = re.sub("[0-9]+", "number", text)
        text = re.sub("#", "", text)
        text = re.sub("\n", "", text)
        text = re.sub("$[^\s]+", "", text)
        text = re.sub("@[^\s]+", "", text)
        text = re.sub("(http|https)://[^\s]*", "", text)
        text = re.sub("[^\s]+@[^\s]+", "", text)
        text = re.sub('[^a-z A-Z]+', '', text)
        return text

    def get_average_sentiment_score(self, ticker):
        data = self.query_request(ticker)

        sum_score = 0
        length = len(data['messages'])
        for message in data['messages']:
            text = self.clean_message(message['body'])
            sent = self.sentiment(message)
            sentiment_score = self.sentiment_analysis_score(text)
            weighted_score = (sent + sentiment_score) / 2
            sum_score += weighted_score
        average_score = round(sum_score / length, 3)
        return average_score

    def get_data_line(self, ticker):
        data = self.query_request(ticker)
        sum_score = 0
        length = len(data['messages'])

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
            dataset = dict()
            text = self.clean_message(message['body'])
            sent = self.sentiment(message)
            sentiment_score = self.sentiment_analysis_score(text)
            # calculate the weighted score
            weighted_score = (sent + sentiment_score) / 2

            if message['id'] not in copy_list_ids:
                # print("yep")
                list_ids.append(message['id'])
                # Dictionary befüllen --> jeder Datensatz der 30
                dataset["id"] = message['id']
                dataset["sentiment"] = sent
                dataset["msg_sentimentscore"] = sentiment_score
                dataset["weighted_score"] = weighted_score
                # Enter dataset into the whole collection
                complete_dataset.append(dataset)
            else:
                print("nope")
                #check whether deletion of list is accurate

        #if within for or not - to be checked
        if ticker == "BTC.X":
            self.complete_btcdataset = complete_dataset
            self.list_ids_btc = list_ids
        elif ticker == "ETH.X":
            self.complete_ethdataset = complete_dataset
            self.list_ids_eth = list_ids

        #print(list_ids)
        #print(complete_dataset[0]["id"])
        #print(complete_dataset)
        # Return of every element
        # for i in range(complete_dataset):
        # print(complete_dataset[i]["id"])

    def sentiment_results(self, tickers):
        for ticker in tickers:
            print(self.get_average_sentiment_score(ticker))

    def get_data(self):
        self.get_data_line("BTC.X")
        self.get_data_line("ETH.X")


StocktwitsDataFetcher()
