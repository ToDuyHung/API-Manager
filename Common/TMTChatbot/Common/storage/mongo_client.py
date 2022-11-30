import pymongo

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.config.schema_config import BaseSchemaConfig
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Common.storage.base_storage import BaseStorage


class MongoConnector(BaseStorage):
    def __init__(self, config: Config = None):
        super(MongoConnector, self).__init__(config=config)
        self.config = config if config is not None else Config()
        if self.config.mongo_uri is not None:
            self.mongo_connector = pymongo.MongoClient(self.config.mongo_uri)
        else:
            self.mongo_connector = pymongo.MongoClient(host=self.config.mongo_host,
                                                       port=self.config.mongo_port,
                                                       username=self.config.mongo_username,
                                                       password=self.config.mongo_password)
        self.schema_cache = {}

    @staticmethod
    def __to_update_json(data, field_methods: dict = None):
        if field_methods is None:
            field_methods = {}
        output = {}
        for key, value in data.items():
            if key == ATTRIBUTES:
                method = "$set"
                if method not in output:
                    output[method] = {}
                if isinstance(value, dict):
                    for attr_key, attr_value in value.items():
                        output[method][f"{key}.{attr_key}"] = attr_value
            elif key not in field_methods:
                method = "$set"
                if method not in output:
                    output[method] = {}
                output[method][key] = value
            else:
                method = f"${field_methods[key]}"
                if method not in output:
                    output[method] = {}
                if isinstance(value, list):
                    output[method][key] = {"$each": value}
        if ATTRIBUTES in data and (data[ATTRIBUTES] is None or len(data[ATTRIBUTES]) == 0):
            output["$set"][ATTRIBUTES] = {}
        return output

    @staticmethod
    def __to_query_json(skip_fields: [str] = None):
        output = {MONGO_OBJECT_ID: 0}
        if skip_fields is None:
            return output
        for key in skip_fields:
            output[key] = 0
        return output

    def get_database(self, storage_id: str):
        return f"{self.config.mongo_database}_{storage_id}"

    @staticmethod
    def get_collection(class_name: str, storage_id: str):
        return class_name

    @staticmethod
    def get_filter_condition(filter_condition: dict, storage_id: str):
        return filter_condition

    def _load_schema_with_class_name(self, class_name: str, parent_class: str, storage_id: str,
                                     restrict: bool = False) -> dict:
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(SCHEMA.capitalize(),
                                                                                             storage_id)]
        if parent_class is None:
            output: dict = collection.find_one(self.get_filter_condition({CLASS: class_name}, storage_id))
        else:
            output: dict = collection.find_one(self.get_filter_condition({CLASS: class_name,
                                                                          PARENT_CLASS: parent_class}, storage_id))
            if output is None and not restrict:
                output: dict = collection.find_one(self.get_filter_condition({CLASS: class_name}, storage_id))

        if output is None and storage_id != "default":
            output = self._load_schema_with_class_name(class_name,
                                                       parent_class,
                                                       storage_id="default",
                                                       restrict=restrict)

        if output is not None and MONGO_OBJECT_ID in output:
            del output[MONGO_OBJECT_ID]
        return output

    def _load_all_schema_with_class_name(self, class_name: str, storage_id: str):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(SCHEMA.capitalize(),
                                                                                             storage_id)]
        output = collection.find(self.get_filter_condition({CLASS: class_name}, storage_id))
        output = list(output)
        if output is None and storage_id != "default":
            output = self._load_all_schema_with_class_name(class_name,
                                                           storage_id="default")

        if output is not None:
            for schema in output:
                if MONGO_OBJECT_ID in schema:
                    del schema[MONGO_OBJECT_ID]
        return output

    def _load_schema(self, data_object: BaseObject, storage_id: str, restrict: bool = False) -> dict:
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(SCHEMA.capitalize(),
                                                                                             storage_id)]
        if data_object.parent_class is None:
            output: dict = collection.find_one(
                self.get_filter_condition({CLASS: data_object.schema_class_name()}, storage_id))
        else:
            output: dict = collection.find_one(self.get_filter_condition({CLASS: data_object.schema_class_name(),
                                                                          PARENT_CLASS: data_object.parent_class},
                                                                         storage_id))
            if output is None and not restrict:
                output: dict = collection.find_one(self.get_filter_condition({CLASS: data_object.schema_class_name()},
                                                                             storage_id))

        if output is None and storage_id != "default":
            output = self._load_schema(data_object, storage_id="default", restrict=restrict)

        if output is not None and MONGO_OBJECT_ID in output:
            del output[MONGO_OBJECT_ID]

        return output

    def _store_schema(self, schema: BaseSchemaConfig, storage_id: str, upsert: bool = True):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(SCHEMA.capitalize(),
                                                                                             storage_id)]
        schema_json = schema.json
        if MONGO_OBJECT_ID in schema_json:
            del schema_json[MONGO_OBJECT_ID]
        if schema.parent_class is None:
            collection.replace_one(self.get_filter_condition({CLASS: schema.class_name()}, storage_id), schema_json,
                                   upsert=upsert)
        else:
            collection.replace_one(self.get_filter_condition({CLASS: schema.class_name(),
                                                              PARENT_CLASS: schema.parent_class}, storage_id),
                                   schema_json, upsert=upsert)
        return schema

    def _load(self, class_name, object_id, storage_id: str, skip_fields: [str] = None):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        return collection.find_one(self.get_filter_condition({OBJECT_ID: object_id}, storage_id),
                                   self.__to_query_json(skip_fields))

    def _load_all(self, class_name, storage_id, offset: int = None, limit: int = None, skip_fields: [str] = None):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        output = collection.find(self.get_filter_condition({}, storage_id), self.__to_query_json(skip_fields))
        if offset:
            output = output.skip(offset)
        if limit:
            output = output.limit(limit)
        return list(output)

    def _load_all_from_description(self, class_name, storage_id, description, offset: int = None,
                                   limit: int = None, skip_fields: [str] = None):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        output = collection.find(self.get_filter_condition(description, storage_id),
                                 self.__to_query_json(skip_fields))
        if offset:
            output = output.skip(offset)
        if limit:
            output = output.limit(limit)
        return list(output)

    def _load_from_description(self, class_name, storage_id, description, skip_fields: [str] = None):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        return collection.find_one(self.get_filter_condition(description, storage_id),
                                   self.__to_query_json(skip_fields))

    def _count_with_description(self, class_name, storage_id, description: dict = None):
        if not description:
            description = dict()
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        return collection.count_documents(self.get_filter_condition(description, storage_id))

    def _save_status(self, data_object: BaseObject, storage_id: str):
        """
        Update status of data_object
        :param data_object: Base Object
        :param storage_id: storage id
        :return: None
        """
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(data_object.class_name(),
                                                                                             storage_id)]
        json_data = self.__to_update_json({
            ENABLE: data_object.is_enable
        })
        collection.update_one(self.get_filter_condition({OBJECT_ID: data_object.id}, storage_id), json_data,
                              upsert=True)

    def _save(self, data_object: BaseObject, storage_id: str, field_methods=None):
        """
        Update data_object to mongo database
        :param data_object: data object to be saved to database
        :param field_methods: some field use different update method. Default: "set". Accept: "push" for list
        :return: None
        """
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(data_object.class_name(),
                                                                                             storage_id)]
        save_data = data_object.json
        json_data = self.__to_update_json(save_data, field_methods=field_methods)
        collection.update_one(self.get_filter_condition({OBJECT_ID: data_object.id}, storage_id), json_data,
                              upsert=True)

    def _load_relations(self, src_id: str, dst_id: str, class_name: str, storage_id: str):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        output = list(collection.find(self.get_filter_condition({REL_SRC: src_id, REL_DST: dst_id}, storage_id)))
        return output

    def _delete(self, data_object: BaseObject, storage_id: str):
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(data_object.class_name(),
                                                                                             storage_id)]
        collection.find_one_and_delete(self.get_filter_condition({OBJECT_ID: data_object.id}, storage_id))

    def _load_random(self, class_name: str, storage_id: str, limit: int, conditions: dict = None):
        if conditions is None:
            conditions = {}
        collection = self.mongo_connector[self.get_database(storage_id)][self.get_collection(class_name,
                                                                                             storage_id)]
        return list(collection.find(self.get_filter_condition(conditions, storage_id)).limit(limit))


class DiffCollMongoConnector(MongoConnector):
    def get_database(self, storage_id: str):
        return self.config.mongo_database

    @staticmethod
    def get_collection(class_name: str, storage_id: str = None):
        return f"{class_name}_{storage_id}"


class JoinCollMongoConnector(MongoConnector):
    def get_database(self, storage_id: str):
        return self.config.mongo_database

    @staticmethod
    def get_collection(class_name: str, storage_id: str = None):
        return class_name

    @staticmethod
    def get_filter_condition(filter_condition: dict, storage_id: str):
        filter_condition[STORAGE_ID] = storage_id
        return filter_condition
