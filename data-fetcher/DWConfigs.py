import requests

from HashiVaultCredentialStorage import HashiVaultCredentialStorage


class DWConfigs:
    class __DWConfigs:
        def __init__(self):
            # in seconds
            self.fallback_fetch_interval = 300.0
            self.fallback_aggregation_interval = 60.0
            self.fallback_health_ping_interval = 60.0

    instance = None

    def __init__(self):
        if not DWConfigs.instance:
            DWConfigs.instance = DWConfigs.__DWConfigs()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_interval_data(self, topic):
        try:
            service_url = HashiVaultCredentialStorage().get_credentials("DWConfigs", "ODataServiceURL")[0]
            result = requests.get(service_url + "/KPI_CONFIG('" + topic + "')").json()
            if result is None:
                raise ValueError('Error')
            return result
        except Exception:
            return {
                "aggregationInterval": self.fallback_aggregation_interval,
                "fetchInterval": self.fallback_fetch_interval
            }

    def get_fetch_interval(self, topic):
        return self.get_interval_data(topic)['fetchInterval']

    def get_aggregation_interval(self, topic):
        return self.get_interval_data(topic)['aggregationInterval']

    def get_health_ping_interval(self, topic):
        try:
            if topic is not "":
                service_url = HashiVaultCredentialStorage().get_credentials("DWConfigs", "ODataServiceURL")[0]
                result = requests.get(service_url + "/API_CONFIG('health_ping_interval')").json()
                return result['health_ping_interval']
        except Exception:
            return self.fallback_health_ping_interval
