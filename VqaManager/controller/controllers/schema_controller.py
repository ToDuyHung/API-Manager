from typing import Union

from TMTChatbot.Common.common_keys import *
from TMTChatbot import BaseDataModel, Node
from TMTChatbot.Schema.config.schema_config import BaseSchemaConfig

from config.config import Config
from data_model import SchemaResponse, ResponseStatus
from controller.controllers.base_controller import BaseController


class SchemaController(BaseController):
    def __init__(self, config: Config):
        super(SchemaController, self).__init__(config=config)

    def get_schema(
            self,
            storage_id: str,
            class_name: str,
            parent_class_name: str,
            return_response: bool = True
    ) -> Union[SchemaResponse, BaseSchemaConfig]:
        def process_func():
            class_ = class_name.capitalize()
            parent_class = parent_class_name
            if parent_class:
                parent_class = parent_class.capitalize()
            schema = self.storage.load_schema_with_class_name(class_, parent_class, storage_id, restrict=True)
            if not schema:
                return None, ResponseStatus.NO_PRODUCT
            return schema, ResponseStatus.SUCCESS

        return self.process(process_func, SchemaResponse, return_response=return_response, return_json=True)

    def get_all_schemas(self, storage_id: str, class_: str) -> SchemaResponse:
        def process_func():
            class_name = class_.capitalize()
            node = Node.get_class_by_type(class_name)
            schemas = self.storage.load_all_schema_with_class_name(class_name=node.class_name(),
                                                                   storage_id=storage_id)
            if not schemas:
                return None, ResponseStatus.NO_PRODUCT
            return schemas, ResponseStatus.SUCCESS

        return self.process(process_func, SchemaResponse)

    def update_schema_from_json(self, storage_id, schema, upsert, return_response=True):
        def process_func(schema_):
            schema_[CLASS] = schema_[CLASS].capitalize()
            if PARENT_CLASS in schema_ and schema_[PARENT_CLASS]:
                schema_[PARENT_CLASS] = schema_[PARENT_CLASS].capitalize()
            else:
                schema_[PARENT_CLASS] = None
            schema_[STORAGE_ID] = storage_id
            if not upsert and not self.storage.load_schema_with_class_name(class_name=schema_[CLASS],
                                                                           parent_class=schema_[PARENT_CLASS],
                                                                           storage_id=storage_id,
                                                                           restrict=True):
                return None, ResponseStatus.NO_PRODUCT
            else:
                schema_ = BaseSchemaConfig.from_json(schema_)
                schema_ = self.storage.store_schema(schema_, storage_id, upsert)
            return schema_, ResponseStatus.SUCCESS

        return self.process(process_func,
                            SchemaResponse,
                            return_response=return_response,
                            return_json=True,
                            args=(schema,))

    def update_schema(self, storage_id: str, input_data: BaseDataModel, upsert: bool) -> SchemaResponse:
        schema = input_data.data.schema_.dict(by_alias=True)
        return self.update_schema_from_json(storage_id, schema=schema, upsert=upsert)

    def delete_schema(
            self,
            storage_id: str,
            class_: str,
            parent_class: str) \
            -> SchemaResponse:
        def process_func(schema_):
            schema_ = self.storage.delete_schema(schema_, storage_id, class_, parent_class)
            return schema_, ResponseStatus.SUCCESS

        schema = self.storage.load_schema_with_class_name(class_, parent_class, storage_id, restrict=True)
        return self.process(process_func,
                            SchemaResponse,
                            return_response=True,
                            return_json=False,
                            args=(schema,))
