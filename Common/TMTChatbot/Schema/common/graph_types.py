from enum import Enum


class NodeTypes(Enum):
    ENTITY = 0
    VALUE = 1


class RelationTypes(Enum):
    ATTR = 0
    REL = 1
    R_ATTR = 2
    O_ATTR = 3


class PhraseMask:
    SRC_MASK = "AA"
    DST_MASK = "BB"
