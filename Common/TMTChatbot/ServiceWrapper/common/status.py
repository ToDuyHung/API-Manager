from enum import Enum


class ResultStatus(Enum):
    READY = 0
    PROCESSING = 1
    SUCCESS = 2
    FAILED = 3
    BUST = 4
