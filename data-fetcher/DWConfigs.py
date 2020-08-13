import logging
import os

import requests

logging.basicConfig(filename='output.log', level=logging.INFO)
os.environ["DW_SERVER"] = '132.187.226.20:8080'


class DWConfigs:
    class __DWConfigs:
        def __init__(self):
            # in seconds
            self.fallback_fetch_interval = 300.0
            self.fallback_health_ping_interval = 60.0

    instance = None

    def __init__(self):
        if not DWConfigs.instance:
            DWConfigs.instance = DWConfigs.__DWConfigs()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_interval_data(self, topic):
        try:
            result = requests.get(os.environ["DW_SERVER"] + "/fetch_interval/" + topic).text

            if result is None:
                logging.error("Using fallback values")
                raise ValueError('Error')

            logging.info("Using real values")
            return float(result)
        except Exception:
            return self.fallback_fetch_interval

    def get_fetch_interval(self, topic):
        return self.get_interval_data(topic)

    def get_health_ping_interval(self, topic):
        val = self.fallback_health_ping_interval
        try:
            if topic != "":
                result = requests.get(os.environ["DW_SERVER"] + "/health_ping_interval").text
                val = float(result)
        except Exception:
            val = self.fallback_health_ping_interval
            logging.error("Failed to receive health ping interval")
        finally:
            return val
