from enum import IntEnum


class ErrorTypes(IntEnum):
    FETCH_ERROR = 1
    PROCESS_ERROR = 2
    API_LIMIT_EXCEED = 3
    GENERAL_ERROR = 4

    def __str__(self):
        return str(self.value)
