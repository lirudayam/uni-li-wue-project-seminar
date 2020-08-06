import logging
import threading

from DWConfigs import DWConfigs

logging.basicConfig(filename='output.log', level=logging.INFO)


class BaseFetcher:
    def __init__(self, kafka_topic, health_ping_fn, process_fn):
        # define them as attributes to reuse in methods
        self._kafka_topic = kafka_topic
        self._health_ping_fn = health_ping_fn
        self._process_fn = process_fn

        # define the base timers
        self.health_timer = threading.Timer(DWConfigs().get_health_ping_interval(kafka_topic), health_ping_fn, [], {})
        self.app_timer = threading.Timer(DWConfigs().get_fetch_interval(kafka_topic), process_fn, [], {})
        logging.info('Successful init')

        # fire threads
        self.health_timer.start()
        self.app_timer.start()

    def run_health(self):
        self.health_timer.cancel()
        self.health_timer = threading.Timer(
            DWConfigs().get_health_ping_interval(self._kafka_topic), self._health_ping_fn, [], {})
        self.health_timer.start()

    def run_app(self):
        self.app_timer.cancel()
        self.app_timer = threading.Timer(
            DWConfigs().get_fetch_interval(self._kafka_topic), self._process_fn, [], {})
        self.app_timer.start()
