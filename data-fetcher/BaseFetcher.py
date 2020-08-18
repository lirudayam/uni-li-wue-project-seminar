import logging
import threading

from DWConfigs import DWConfigs
import time
from threading import Timer

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class BaseFetcher:

    class RepeatedTimer(object):
        def __init__(self, interval, function, *args, **kwargs):
            self._timer = None
            self.interval = interval
            self.function = function
            self.args = args
            self.kwargs = kwargs
            self.is_running = False
            self.start()

        def _run(self):
            self.is_running = False
            self.start()
            self.function(*self.args, **self.kwargs)

        def start(self):
            if not self.is_running:
                self._timer = Timer(self.interval, self._run)
                self._timer.start()
                self.is_running = True

        def stop(self):
            self._timer.cancel()
            self.is_running = False

    def __init__(self, kafka_topic, health_ping_fn, process_fn):
        # define them as attributes to reuse in methods
        self._kafka_topic = kafka_topic
        self._health_ping_fn = health_ping_fn
        self._process_fn = process_fn

        self._health_interval = DWConfigs().get_health_ping_interval(self._kafka_topic)
        self._app_interval = DWConfigs().get_fetch_interval(self._kafka_topic)

        # define the base timers
        self.health_timer = self.RepeatedTimer(self._health_interval, self._health_ping_fn)
        self.app_timer = self.RepeatedTimer(self._app_interval, self._process_fn)

        logging.info('Successful init of timers')

    def run_health(self):
        if DWConfigs().get_health_ping_interval(self._kafka_topic) != self._health_interval:
            self.health_timer.stop()
            self._health_interval = DWConfigs().get_health_ping_interval(self._kafka_topic)
            self.health_timer = self.RepeatedTimer(self._health_interval, self._health_ping_fn)

    def run_app(self):
        if DWConfigs().get_fetch_interval(self._kafka_topic) != self._app_interval:
            self.app_timer.stop()
            self._app_interval = DWConfigs().get_fetch_interval(self._kafka_topic)
            self.app_timer = self.RepeatedTimer(self._app_interval, self._process_fn)
