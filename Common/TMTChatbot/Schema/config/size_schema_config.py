from types import MethodType
from typing import Dict, Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field

from TMTChatbot.Schema.objects.common.data_model import BaseDataModel


class BaseSizeModel(BaseModel):

    def keys(self):
        output = [item for item in self.__dir__() if
                  not item.startswith("_")
                  and not isinstance(getattr(self, item), MethodType)
                  and not isinstance(getattr(self, item), type)]
        return output

    def getattr(self, item, default=None):
        if hasattr(self, item):
            return getattr(self, item)
        return default

    def setattr(self, attr, value):
        if hasattr(self, attr):
            return setattr(self, attr, value)

    def json_infor(self):
        infor = {}
        for key in self.keys():
            value = self.getattr(key)
            if isinstance(value, BaseSizeModel):
                value = value.json_infor()
            infor[key] = value
        return infor


class Range(BaseSizeModel):
    min: float = Field(description="minimum value")
    max: float = Field(description="maximum value")


class Size(BaseSizeModel):
    weight: Range
    height: Range
    bust: Optional[Range]
    waist: Optional[Range]
    hips: Optional[Range]

    @classmethod
    def keys(cls):
        return list(cls.__fields__.keys())


class ProductSizeInfo(BaseSizeModel):
    size_table: Dict[str, Size] = Field(description="Size table of an category")
    unit: Optional[Dict[str, Literal["KG", "M", "CM"]]] = Field(description="Unit of measurement")

    class Config:
        schema_extra = {
            "size_table": {
                "XS": {
                    "weight": {
                        "min": 30,
                        "max": 36
                    },
                    "height": {
                        "min": 146,
                        "max": 148
                    },
                    "bust": {
                        "min": 74,
                        "max": 77
                    },
                    "waist": {
                        "min": 60,
                        "max": 63
                    },
                    "hips": {
                        "min": 80,
                        "max": 82
                    }
                },
                "M": {
                    "weight": {
                        "min": 40,
                        "max": 55
                    },
                    "height": {
                        "min": 152,
                        "max": 160
                    },
                    "bust": {
                        "min": 82,
                        "max": 90
                    },
                    "waist": {
                        "min": 66,
                        "max": 71.5
                    },
                    "hips": {
                        "min": 85,
                        "max": 94
                    }
                },
                "L": {
                    "weight": {
                        "min": 47,
                        "max": 60
                    },
                    "height": {
                        "min": 155,
                        "max": 168
                    },
                    "bust": {
                        "min": 86,
                        "max": 98
                    },
                    "waist": {
                        "min": 70,
                        "max": 76.5
                    },
                    "hips": {
                        "min": 74,
                        "max": 98
                    }
                },
                "XL": {
                    "weight": {
                        "min": 56,
                        "max": 70
                    },
                    "height": {
                        "min": 160,
                        "max": 177
                    },
                    "bust": {
                        "min": 90,
                        "max": 107
                    },
                    "waist": {
                        "min": 74,
                        "max": 80
                    },
                    "hips": {
                        "min": 95,
                        "max": 106
                    }
                },
                "XXL": {
                    "weight": {
                        "min": 70,
                        "max": 80
                    },
                    "height": {
                        "min": 177,
                        "max": 200
                    },
                    "bust": {
                        "min": 90,
                        "max": 107
                    },
                    "waist": {
                        "min": 74,
                        "max": 80
                    },
                    "hips": {
                        "min": 95,
                        "max": 106
                    }
                }
            },
            "unit": {
                "weight": "KG",
                "height": "M",
                "bust": "CM",
                "waist": "CM",
                "hips": "CM"
            }
        }


class UserInfo(BaseSizeModel):
    weight: Optional[float] = Field(description="User weight")
    height: Optional[float] = Field(description="User height")
    bust: Optional[float] = Field(description="User bust")
    waist: Optional[float] = Field(description="User waist")
    hips: Optional[float] = Field(description="User hips")
    size: Optional[str] = Field(description="User size")

    def __init__(self, weight=None, height=None, bust=None, waist=None, hips=None, size=None):
        weight = float(weight) if weight is not None else None
        height = float(height) if height is not None else None
        hips = float(hips) if hips is not None else None
        bust = float(bust) if bust is not None else None
        waist = float(waist) if waist is not None else None
        super(UserInfo, self).__init__(weight=weight, height=height, hips=hips, bust=bust, waist=waist, size=size)

    def getattr(self, item, default=None):
        if item == "size":
            return self.size
        if hasattr(self, item):
            output = getattr(self, item)
        else:
            output = 0
        if output is None:
            output = 0
        return output

    def keys(self):
        output = list(super().keys())
        if "size" in output:
            output.remove("size")
        return output
