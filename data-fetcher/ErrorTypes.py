import json
from enum import Enum


class ErrorTypes(Enum):
    FETCH_ERROR = 1
    PROCESS_ERROR = 2
    API_LIMIT_EXCEED = 3
    GENERAL_ERROR = 4

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
