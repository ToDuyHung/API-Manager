import json
import hashlib
from uuid import uuid4, uuid5
from datetime import datetime

import logging

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Schema.config.schema_config import BaseSchemaConfig


class BaseObject:
    schema_required = True
    force_accept = True
    use_random_key = True

    def __init__(self, _id, storage_id, storage=None, schema=None, parent_class=None,
                 schema_required=None, hashed=None, enable: bool = True, **kwargs):
        self.logger = logging.getLogger(self.class_name())
        if schema_required is not None:
            self.schema_required = schema_required
        self.id = _id if _id is not None else self.generate_id(self.class_name())
        self.storage = storage
        self._parent_class = parent_class
        self.hash_code = None
        self._read_only = True
        self.deletable = False
        self.storage_id = storage_id if storage_id is not None else ""
        if schema is None or (PARENT_CLASS in schema and schema[PARENT_CLASS] is None):
            self.schema = self.load_schema()
        elif isinstance(schema, BaseSchemaConfig):
            self.schema = schema
        else:
            # self.schema = BaseSchemaConfig.from_json(schema, validate=False)
            self.schema = self.load_schema()
        self.name = f"{self.class_name()}_{self.id}"
        self.hashed = hashed
        self._enable = enable

    @property
    def parent_class(self):
        return self._parent_class

    @parent_class.setter
    def parent_class(self, _parent_class):
        self.schema = self.load_schema()
        self._parent_class = _parent_class

    @property
    def is_enable(self):
        return self._enable

    def enable(self):
        self._enable = True

    def disable(self):
        self._enable = False

    @property
    def read_only(self):
        return self._read_only

    @read_only.setter
    def read_only(self, _read_only):
        self._read_only = _read_only

    @classmethod
    def generate_id(cls, key=None):
        if cls.use_random_key:
            base_id = uuid4()
            if key is None:
                key = ""
            key += str(datetime.now().timestamp())
            return str(uuid5(base_id, key))
        else:
            return cls.generate_hash(key)

    @staticmethod
    def generate_hash(data):
        json_string = json.dumps(data, sort_keys=True)
        hash_string = hashlib.md5(json_string.encode("utf-8")).hexdigest()
        return hash_string

    def load_schema(self, schema=None) -> BaseSchemaConfig:
        """
        Load Schema using class_name and parent_class -> represent required attributes and relations of an object.
        Extra attributes and relations are all excepted but not listed in SchemaObject
        :return: BaseSchemaConfig
        """
        if self.schema_required:
            if self.check_storage():
                schema = self.storage.load_schema(self, storage_id=self.storage_id)
                self.logger.debug(
                    f"Schema loaded with CLASS: {self.class_name()} and PARENT_CLASS: {self.parent_class}")
                if schema is not None:
                    return schema
        return BaseSchemaConfig.from_json({CLASS: self.schema_class_name(), PARENT_CLASS: self.parent_class},
                                          validate=False)

    def check_storage(self):
        if self.storage is None:
            self.logger.debug(f"Need Storage interface: {self.class_name()}")
            return False
        return True

    def save_status(self, force=False):
        """
        Update object json to database if there are any changes
        :param force: if force and self.force_accept: the object data is replaced into the corresponding one in database
        :return: None
        """
        if (not self.read_only or (force and self.force_accept)) and self.check_storage():
            self.storage.save_status(self, storage_id=self.storage_id)
            self.logger.info(f"UPDATE [ENABLE] OF {self.class_name()} to {self.is_enable}")

    def save(self, force=False, field_methods=None):
        """
        Update object json to database if there are any changes
        :param force: if force and self.force_accept: the object data is replaced into the corresponding one in database
        :param field_methods: some field use different update method. Default: "set". Accept: "push" for list
        :return: None
        """
        if (not self.read_only or (force and self.force_accept)) and self.check_storage():
            if self.changed:
                self.storage.save(self, storage_id=self.storage_id, field_methods=field_methods)
                self.logger.debug(f"SAVE NEW OBJECT OF {self.class_name()}")
            else:
                self.logger.debug(f"NOT SAVE NEW OBJECT OF {self.class_name()}")

    def delete(self, force=False):
        if (not self.deletable or (force and self.force_accept)) and self.check_storage():
            self.storage.delete(self, storage_id=self.storage_id)

    @staticmethod
    def get_json_value(data, key, default_value=None):
        extracted_data = data.get(key)
        extracted_data = extracted_data if extracted_data is not None else default_value
        return extracted_data

    @property
    def _json(self):
        raise NotImplementedError("Need implementation")

    @property
    def _all_data(self):
        raise NotImplementedError("Need implementation")

    @property
    def static_info(self):
        return {
            OBJECT_ID: self.id,
            CLASS: self.class_name(),
            STORAGE_ID: self.storage_id
        }

    @classmethod
    def __drop_empty(cls, data: dict):
        for key, value in data.items():
            if isinstance(value, list):
                if len(data[key]) == 0:
                    data[key] = None
        return data

    @property
    def json(self):
        json_data = self._json
        json_data = self.__drop_empty(json_data)
        json_data[SCHEMA] = None if self.schema is None else self.schema.static_info
        json_data[STORAGE_ID] = self.storage_id
        json_data[OBJECT_HASHED] = self.generate_hash(json_data)
        json_data[OBJECT_ID] = self.id
        json_data[CLASS] = self.class_name()
        for key in json_data:
            if key is None:
                del json_data[key]
        return json_data

    @property
    def all_data(self):
        json_data = self._all_data
        json_data[OBJECT_ID] = self.id
        json_data[CLASS] = self.class_name()
        json_data[STORAGE_ID] = self.storage_id
        return json_data

    @property
    def pretty_json(self):
        return json.dumps(self.json, indent=4)

    @classmethod
    def class_name(cls):
        return cls.__name__

    @classmethod
    def schema_class_name(cls):
        return cls.class_name()

    @classmethod
    def skip_fields(cls):
        return []

    @property
    def schema_id(self):
        return BaseSchemaConfig.generate_schema_id(self.schema_class_name(), self.parent_class, self.storage_id)

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, **kwargs):
        raise NotImplementedError("Need implementation")

    @classmethod
    def load_all(cls, storage, storage_id, offset: int = None, limit: int = None):
        objects_data = storage.load_all(class_name=cls.class_name(), storage_id=storage_id,
                                        offset=offset, limit=limit)
        objects = [cls.from_json(data=data, storage=storage) for data in objects_data]
        return objects

    @classmethod
    def from_json(cls, data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        class_name = data.get(CLASS)
        object_name = data.get(NAME)
        if OBJECT_ID not in data:
            data[OBJECT_ID] = data.get(f"_{OBJECT_ID}")
        if f"_{OBJECT_ID}" in data:
            del data[f"_{OBJECT_ID}"]
        object_id = data.get(OBJECT_ID)
        storage_id = data.get(STORAGE_ID)

        if nodes is None:
            nodes = {}
        if object_id is not None:
            node = nodes.get(object_id)
        else:
            node = None
        if node is not None and node.class_name() == class_name and node.storage_id == storage_id:
            return node

        if storage_id is None:
            raise ValueError(f"{STORAGE_ID} must not be null")
        if object_name is None and storage is not None and class_name is not None and object_id is not None:
            new_data = storage.load(class_name, object_id, skip_fields=cls.skip_fields(), storage_id=storage_id)
            if new_data is not None:
                for key, value in data.items():
                    new_data[key] = value
                data = new_data
        new_object = cls._from_json(data, storage, schema_required, nodes=nodes, **kwargs)
        if new_object is not None:
            new_object.hashed = data.get(OBJECT_HASHED)
            nodes[new_object.id] = new_object
            return new_object

    @classmethod
    def from_description(cls, data, schema_required=None, storage=None, **kwargs):
        class_name = data.get(CLASS)
        storage_id = data.get(STORAGE_ID)
        if storage_id is None:
            raise ValueError(f"{STORAGE_ID} must not be null")
        if storage is not None and class_name is not None:
            new_data = storage.load_from_description(class_name=class_name, storage_id=storage_id,
                                                     description=data, skip_fields=cls.skip_fields())
            if new_data is not None:
                for key, value in new_data.items():
                    data[key] = value
        nodes = {}
        new_object = cls._from_json(data, storage, schema_required, nodes=nodes, **kwargs)
        if new_object is not None:
            new_object.hashed = data.get(OBJECT_HASHED)
            nodes[new_object.id] = new_object
            return new_object

    @property
    def changed(self):
        json_data = self._json
        json_data = self.__drop_empty(json_data)
        hash_code = self.generate_hash(json_data)
        output = hash_code != self.hash_code
        self.hash_code = hash_code
        return output
