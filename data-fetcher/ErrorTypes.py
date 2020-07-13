from enum import Enum


class ErrorTypes(Enum):
    FETCH_ERROR = 1
    PROCESS_ERROR = 2
    API_LIMIT_EXCEED = 3
    GENERAL_ERROR = 4
