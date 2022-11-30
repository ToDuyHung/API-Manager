import logging
import time
from threading import Thread

from TMTChatbot.Common.singleton import BaseSingleton
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.config.schema_config import BaseSchemaConfig
from TMTChatbot.Schema.objects.base_object import BaseObject


class BaseStorage(BaseSingleton):
    def __init__(self, config: Config = None, with_sync_worker: bool = False):
        super(BaseStorage, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config if config is not None else Config()
        self.schema_cache = {}
        if with_sync_worker:
            self.update_worker = Thread(target=self.back_ground_job, daemon=True)
            self.update_worker.start()

    def update_current_schemas(self):
        new_updates = []
        drop_none_schemas = []
        for schema_id, schema in self.schema_cache.items():
            schema: BaseSchemaConfig
            if schema is None:
                drop_none_schemas.append(schema_id)
                continue
            schema: dict = self._load_schema_with_class_name(class_name=schema.class_name(),
                                                             parent_class=schema.parent_class,
                                                             storage_id=schema.storage_id,
                                                             restrict=True)
            if schema is not None:
                schema = BaseSchemaConfig(schema)
                self.schema_cache[schema_id] = schema
                new_updates.append(schema_id)
        for schema_id in drop_none_schemas:
            if schema_id in self.schema_cache:
                del self.schema_cache[schema_id]
        if len(new_updates) > 0:
            self.logger.info(f"Update {len(new_updates)} schemas of {new_updates}")
        elif len(drop_none_schemas) > 0:
            self.logger.info(f"Drop {len(drop_none_schemas)} schemas of {drop_none_schemas}")
        else:
            self.logger.info("No new schema update")

    def back_ground_job(self):
        while True:
            self.update_current_schemas()
            time.sleep(10)

    def _load_schema_with_class_name(self, class_name: str, parent_class: str, storage_id: str,
                                     restrict: bool = False) -> dict:
        raise NotImplementedError("Need Implementation")

    def _load_all_schema_with_class_name(self, class_name: str, storage_id: str):
        raise NotImplementedError("Need Implementation")

    def _load_schema(self, data_object: BaseObject, storage_id: str, restrict: bool = False) -> dict:
        raise NotImplementedError("Need Implementation")

    def _store_schema(self, schema: BaseSchemaConfig, storage_id: str, upsert: bool = True) -> BaseSchemaConfig:
        raise NotImplementedError("Need Implementation")

    def _load(self, class_name, object_id, storage_id: str, skip_fields: [str] = None):
        raise NotImplementedError("Need Implementation")

    def _load_all_from_description(self, class_name, storage_id, description, offset: int = None,
                                   limit: int = None, skip_fields: [str] = None):
        raise NotImplementedError("Need Implementation")

    def _load_from_description(self, class_name, storage_id, description, skip_fields: [str] = None):
        raise NotImplementedError("Need Implementation")

    def _save_status(self, data_object: BaseObject, storage_id: str):
        raise NotImplementedError("Need Implementation")

    def _save(self, data_object: BaseObject, storage_id: str, field_methods=None):
        raise NotImplementedError("Need Implementation")

    def _delete(self, data_object: BaseObject, storage_id: str):
        raise NotImplementedError("Need Implementation")

    def _load_relations(self, src_id: str, dst_id: str, class_name: str, storage_id: str):
        raise NotImplementedError("Need Implementation")

    def _load_random(self, class_name: str, storage_id: str, limit: int, conditions: dict = None):
        raise NotImplementedError("Need Implementation")

    def _load_all(self, class_name, storage_id, offset: int = None, limit: int = None, skip_fields: [str] = None):
        raise NotImplementedError("Need Implementation")

    def _count_with_description(self, class_name, storage_id, description):
        raise NotImplementedError("Need Implementation")

    def load_schema(self, data_object: BaseObject, storage_id: str, restrict: bool = False):
        if data_object.schema_id is not None and data_object.schema_id not in self.schema_cache:
            schema: dict = self._load_schema(data_object, storage_id=storage_id, restrict=restrict)
            if schema is not None:
                output = BaseSchemaConfig.from_json(schema)
            else:
                output = schema
            self.schema_cache[data_object.schema_id] = output
        return self.schema_cache[data_object.schema_id]

    def load_schema_with_class_name(self, class_name: str, parent_class: str, storage_id: str,
                                    restrict: bool = False) -> BaseSchemaConfig:
        schema_id = BaseSchemaConfig.generate_schema_id(class_name, parent_class, storage_id)
        if schema_id not in self.schema_cache:
            schema = self._load_schema_with_class_name(class_name=class_name, parent_class=parent_class,
                                                       storage_id=storage_id, restrict=restrict)
            if schema is not None:
                output = BaseSchemaConfig(schema)
            else:
                output = schema
            self.schema_cache[schema_id] = output
        return self.schema_cache[schema_id]

    def load_all_schema_with_class_name(self, class_name: str, storage_id: str):
        schema_id = BaseSchemaConfig.generate_schema_id(class_name, "", storage_id)
        if schema_id not in self.schema_cache:
            schema = self._load_all_schema_with_class_name(class_name=class_name, storage_id=storage_id)
            self.schema_cache[schema_id] = schema
        return self.schema_cache[schema_id]

    def store_schema(self, schema: BaseSchemaConfig, storage_id: str, upsert: bool = True):
        schema = self._store_schema(schema, storage_id=storage_id, upsert=upsert)
        self.schema_cache[schema.schema_id] = schema
        return schema

    def load(self, class_name, object_id, storage_id, skip_fields: [str] = None):
        return self._load(class_name, object_id, skip_fields=skip_fields, storage_id=storage_id)

    def load_all(self, class_name, storage_id, offset: int = None, limit: int = None, skip_fields: [str] = None):
        return self._load_all(class_name=class_name, storage_id=storage_id, offset=offset, limit=limit,
                              skip_fields=skip_fields)

    def load_all_from_description(self, class_name, storage_id, description, offset: int = None,
                                  limit: int = None, skip_fields: [str] = None):
        return self._load_all_from_description(class_name, storage_id, description, offset, limit, skip_fields)

    def load_from_description(self, class_name, storage_id, description, skip_fields: [str] = None):
        return self._load_from_description(class_name=class_name, storage_id=storage_id, description=description,
                                           skip_fields=skip_fields)

    def count_with_description(self, class_name, storage_id, description):
        return self._count_with_description(class_name, storage_id, description)

    def save_status(self, data_object: BaseObject, storage_id: str):
        """
        Update data_object's status to database if there are some changes. Status in [enable]
        :param storage_id: identify which store the object is saved
        :param data_object:  data object to be saved to database
        :return:
        """
        self._save_status(data_object, storage_id=storage_id)

    def save(self, data_object: BaseObject, storage_id: str, field_methods=None):
        """
        Update data_object to database if there are some changes
        :param storage_id: identify which store the object is saved
        :param data_object: data object to be saved to database
        :param field_methods: some field use different update method. Default: "set". Accept: "push" for list
        :return: None
        """
        self._save(data_object, field_methods=field_methods, storage_id=storage_id)

    def load_relations(self, src_id: str, dst_id: str, class_name: str, storage_id: str):
        return self._load_relations(src_id=src_id, dst_id=dst_id, class_name=class_name, storage_id=storage_id)

    def load_random(self, class_name: str, storage_id: str, limit: int, conditions: dict = None):
        return self._load_random(class_name=class_name, storage_id=storage_id, limit=limit, conditions=conditions)

    def delete(self, data_object: BaseObject, storage_id: str):
        """
        Delete object of self in database
        :return: None
        """
        self._delete(data_object, storage_id=storage_id)
