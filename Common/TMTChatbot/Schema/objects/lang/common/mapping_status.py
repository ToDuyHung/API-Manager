from enum import Enum


class MappingSTT(Enum):
    NEW = 0
    PARTIALLY_MAPPED = 1
    MAPPED = 2
    WAITING = 3
    IMPOSSIBLE = 4
