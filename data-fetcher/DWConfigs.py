class DWConfigs:
    class __DWConfigs:
        def __init__(self):
            # in seconds
            self.fetch_interval = 300.0
            self.aggregation_interval = 60.0
            self.health_ping_interval = 60.0

    instance = None

    def __init__(self):
        if not DWConfigs.instance:
            DWConfigs.instance = DWConfigs.__DWConfigs()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_fetch_interval(self, topic):
        return self.fetch_interval

    def get_aggregation_interval(self, topic):
        return self.aggregation_interval

    def get_health_ping_interval(self, topic):
        return self.health_ping_interval
