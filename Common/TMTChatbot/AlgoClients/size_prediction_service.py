from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.config.config import Config
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.graph.graph_data import User, Product
from TMTChatbot.Schema.config.size_schema_config import (
    Size,
    UserInfo
)
from TMTChatbot.Schema.config.schema_config import ProductSchemaConfig, ProductSizeInfo

from TMTChatbot.AlgoClients.data_model.size_prediction import (
    SizePredictionDataModel,
    RequestSizePredictionBaseModel,
    ResponseSizePrediction
)


class SizePredictionService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(SizePredictionService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.size_prediction_url}/process"
        self.storage = storage

    def _pre_process(self, input_data: [User, Product]):
        user, product = input_data
        product_schema: ProductSchemaConfig = product.schema
        user_data = {key: user.get_last_attr_value(key) for key in Size.keys()}
        user_info = UserInfo(**user_data)
        product_size_info = product_schema.size_table
        return RequestSizePredictionBaseModel(data=SizePredictionDataModel(product_size_info=product_size_info,
                                                                           user_info=user_info))

    def _post_process(self, data: BaseDataModel) -> str:
        result = None
        if data is not None:
            result = data.data.get("size")
        if result == "":
            result = None
        return result

