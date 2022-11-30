from typing import Optional, Dict

from pydantic import BaseModel

from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.config.size_schema_config import BaseSizeModel, ProductSizeInfo, UserInfo, Size


class SizePredictionDataModel(BaseSizeModel):
    product_size_info: Optional[ProductSizeInfo]
    user_info: UserInfo
    status: Optional[str]

    def __init__(self, user_info: UserInfo, product_size_info: ProductSizeInfo = None, status: str = None):
        super(SizePredictionDataModel, self).__init__(product_size_info=product_size_info, user_info=user_info,
                                                      status=status)
        self.status = "successful"
        if self.product_size_info is not None:
            if not (self.product_size_info.size_table is None and self.product_size_info.unit is None):
                if (self.product_size_info.size_table is None) ^ (self.product_size_info.unit is None):
                    self.status = "lack of product_size_info"

        if self.user_info is None and self.status == "successful":
            self.status = "lack of user_info"

    class Config:
        schema_extra = {
            "product_size_info": ProductSizeInfo.schema_json(),
            "user_info": UserInfo.schema_json()
        }

    def get_size_table(self) -> Dict[str, Size]:
        return self.product_size_info.size_table

    def set_status(self, new_status: str) -> None:
        self.status = new_status
        return

    def get_list(self, unit_general: dict) -> list:
        list_info = []
        list_feature = list(self.user_info.keys())[:-1]
        unit = self.product_size_info.unit if self.product_size_info.unit else unit_general
        for name in list_feature:
            if unit[name] == 'M':
                list_info += [self.user_info.getattr(name, 0) * 100]
            else:
                list_info += [self.user_info.getattr(name, 0)]
        return list_info


class RequestSizePredictionBaseModel(BaseDataModel):
    data: Optional[SizePredictionDataModel]

    def __init__(self, index: str = None, data: SizePredictionDataModel = None, meta_data=None):
        super(RequestSizePredictionBaseModel, self).__init__(index=index, data=data, meta_data=meta_data)

    class Config:
        schema_extra = {
            "data": SizePredictionDataModel.schema_json()
        }


class RequestSizePredictionDataModel(BaseModel):
    input_data: RequestSizePredictionBaseModel


class ResponseSizePrediction(BaseDataModel):
    data: UserInfo
