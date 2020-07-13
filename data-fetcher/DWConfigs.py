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
        # Mock data
        switcher = {
            'RAW_G_RICH_ACC': 120,
            'RAW_G_T_PER_TIME': 120,
            'RAW_E_SMART_EXEC': 120,
            'RAW_G_N_PER_TIME': 120,
            'RAW_G_FEE_SHARE': 120,
            'RAW_G_VOLUME': 120,
            'RAW_G_PRICES': 60,
            'RAW_G_LATEST_BLOCK': 5,
            'RAW_G_STOCKTWITS_FETCHER': 60,
            'RAW_G_PRICE_VOLA': 120,
            'RAW_G_PRICE_DIFF': 120,
            'RAW_B_SPECIAL_EVT': 86400,
            'RAW_G_NEWS': 60,
            'RAW_G_RECOMM': 3600,
            'RAW_G_CREDITS': 3600,
            'RAW_E_GASSTATION': 5
        }

        return switcher.get(topic, self.fetch_interval)

    def get_aggregation_interval(self, topic):
        return self.aggregation_interval

    def get_health_ping_interval(self, topic):
        return self.health_ping_interval
