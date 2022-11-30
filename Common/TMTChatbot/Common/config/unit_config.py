import types
from enum import Enum

from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Schema.common.data_types import DataType


class UnitConfig(BaseSingleton):
    phone = DataType.STR
    size = DataType.STR
    color = DataType.STR
    material_product = DataType.STR
    gender = DataType.STR
    weight = DataType.KG
    height = DataType.M
    waist = DataType.CM
    hips = DataType.CM
    bust = DataType.CM
    time = DataType.DATETIME
    DATE = DataType.DATETIME
    TIME = DataType.DATETIME
    Time = DataType.DATETIME
    GPE = DataType.STR
    LOC = DataType.STR
    ORG = DataType.STR
    MONEY = DataType.VND
    PERSON = DataType.STR
    PERCENT = DataType.INT
    QUANTITY = DataType.INT
    CARDINAL = DataType.INT
    ORDINAL = DataType.STR

    @classmethod
    def get_target_data_type(cls, entity_type: str):
        if hasattr(cls, entity_type):
            return getattr(cls, entity_type)

    @classmethod
    def types_dict(cls):
        return {key: getattr(cls, key).name for key in cls.__dict__ if isinstance(getattr(cls, key), Enum)}
