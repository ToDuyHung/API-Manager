from TMTChatbot import (
    BaseServiceWithRAMCacheSingleton,
    BaseDataModel
)

from config.config import Config
from controller.controllers import *
from data_model.response import *


class Processor(BaseServiceWithRAMCacheSingleton):
    def __init__(self, config: Config):
        super(Processor, self).__init__(config=config)
        self.schema_controller = SchemaController(config)

    def get_schema(self, storage_id: str, class_: str, parent_class: str = None) -> SchemaResponse:
        return self.schema_controller.get_schema(storage_id, class_, parent_class)

    def get_all_schemas(self, storage_id: str, class_: str):
        return self.schema_controller.get_all_schemas(storage_id, class_)
    #
    # def insert_schema(self, storage_id: str, input_data: BaseDataModel) -> SchemaResponse:
    #     return self.schema_controller.update_schema(storage_id, input_data, upsert=True)
    #
    # def update_schema(self, storage_id: str, input_data: BaseDataModel) -> SchemaResponse:
    #     return self.schema_controller.update_schema(storage_id, input_data, upsert=False)
    #
    # def enable_schema_attribute(
    #         self,
    #         storage_id: str,
    #         class_: str,
    #         input_data: BaseDataModel,
    #         parent_class: str = None,
    # ) -> SchemaResponse:
    #     return self.schema_controller.enable_schema_attribute(storage_id, class_, input_data, parent_class)

    def insert_vqa_schema(self, storage_id: str, input_data: BaseDataModel) -> SchemaResponse:
        return self.schema_controller.update_schema(storage_id, input_data, upsert=True)

    def update_vqa_schema(self, storage_id: str, input_data: BaseDataModel) -> SchemaResponse:
        return self.schema_controller.update_schema(storage_id, input_data, upsert=False)

    def delete_vqa_schema(
            self,
            storage_id: str,
            class_: str,
            parent_class: str
    ) -> SchemaResponse:
        return self.schema_controller.delete_schema(storage_id, class_, parent_class)
