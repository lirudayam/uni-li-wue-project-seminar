import logging
import threading

from DWConfigs import DWConfigs
import time

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class BaseFetcher:
    def __init__(self, kafka_topic, health_ping_fn, process_fn):
        # define them as attributes to reuse in methods
        self._kafka_topic = kafka_topic
        self._health_ping_fn = health_ping_fn
        self._process_fn = process_fn

        self._health_interval = DWConfigs().get_health_ping_interval(self._kafka_topic)
        self._app_interval = DWConfigs().get_fetch_interval(self._kafka_topic)

        # define the base timers
        self.health_timer = threading.Timer(self._health_interval, self._health_ping_fn)
        self.app_timer = threading.Timer(self._app_interval, self._process_fn)

        logging.info('Successful init of timers')

        # fire threads
        self.health_timer.start()
        self.app_timer.start()

        # keep alive method
        while True:
            time.sleep(2)  # 2 second delay

    def run_health(self):
        if DWConfigs().get_health_ping_interval(self._kafka_topic) != self._health_interval:
            self.health_timer.cancel()
            self._health_interval = DWConfigs().get_health_ping_interval(self._kafka_topic)
            self.health_timer = threading.Timer(self._health_interval, self._health_ping_fn, [], {})
            self.health_timer.start()

    def run_app(self):
        if DWConfigs().get_fetch_interval(self._kafka_topic) != self._app_interval:
            self.app_timer.cancel()
            self.app_timer = threading.Timer(
                DWConfigs().get_fetch_interval(self._kafka_topic), self._process_fn, [], {})
            self.app_timer.start()
