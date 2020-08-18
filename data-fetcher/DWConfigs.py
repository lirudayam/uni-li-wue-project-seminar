import logging
import os

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(
    filename='output.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class DWConfigs:
    class __DWConfigs:
        def __init__(self):
            # in seconds
            self.fallback_fetch_interval = 300.0
            self.fallback_health_ping_interval = 60.0

            self.session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount('http://', adapter)

            logging.info("using DW at {0}".format(os.environ["DW_SERVER"]))

    instance = None

    def __init__(self):
        if not DWConfigs.instance:
            DWConfigs.instance = DWConfigs.__DWConfigs()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_interval_data(self, topic):
        val = 0
        try:
            result = self.session.get(os.environ["DW_SERVER"] + "/fetch_interval/" + topic, timeout=1).text

            if result is None:
                logging.error("Using fallback values")
                raise ValueError('Error')

            logging.info("Using real values")
            val = float(result)
        except requests.exceptions.ConnectionError:
            val = self.fallback_fetch_interval
        except Exception as e:
            logging.error("Failed to receive fetch interval due to {0}".format(e))
            val = self.fallback_fetch_interval
        finally:
            return val

    def get_fetch_interval(self, topic):
        return self.get_interval_data(topic)

    def get_health_ping_interval(self, topic):
        val = self.fallback_health_ping_interval
        try:
            if topic != "":
                result = self.session.get(os.environ["DW_SERVER"] + "/health_ping_interval", timeout=1)
                if result.status_code == 200:
                    result = result.text
                else:
                    result = self.fallback_fetch_interval
                    logging.error("health ping endpoint returned {0}".format(result.status_code))
        except requests.exceptions.ConnectionError:
            val = self.fallback_health_ping_interval
        except Exception as e:
            val = self.fallback_health_ping_interval
            logging.error("Failed to receive health ping interval due to {0}".format(e))
            pass
        else:
            val = float(result)
        finally:
            return val
