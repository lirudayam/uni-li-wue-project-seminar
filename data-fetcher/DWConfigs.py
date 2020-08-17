import logging
import os

import requests

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
os.environ["DW_SERVER"] = 'http://132.187.226.20:8080'


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
        except Exception as e:
            logging.error("Failed to receive fetch interval due to {0}".format(e))
            return self.fallback_fetch_interval

    def get_fetch_interval(self, topic):
        return self.get_interval_data(topic)

    def get_health_ping_interval(self, topic):
        val = self.fallback_health_ping_interval
        try:
            if topic != "":
                result = requests.get(os.environ["DW_SERVER"] + "/health_ping_interval")
                if result.status_code == 200:
                    result = result.text
                else:
                    result = self.fallback_fetch_interval
                    logging.error("health ping endpoint returned {0}".format(result.status_code))
        except Exception as e:
            val = self.fallback_health_ping_interval
            logging.error("Failed to receive health ping interval due to {0}".format(e))
            pass
        else:
            val = float(result)
        finally:
            return val
