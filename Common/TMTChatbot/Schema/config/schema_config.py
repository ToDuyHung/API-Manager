import sys
from typing import List, Dict

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Schema.config.size_schema_config import ProductSizeInfo


class SchemaAttribute:
    def __init__(self, enable: bool = True):
        self._enable = enable

    @property
    def enable(self):
        return self._enable

    @enable.setter
    def enable(self, _enable: bool):
        self._enable = _enable


class BaseSchemaConfig:
    def __init__(self, data=None, validate=True, class_name: str = None, storage_id: str = None,
                 parent_class: str = None, user_required_attributes: Dict[str, bool] = None,
                 required_attributes: Dict[str, bool] = None, attributes: Dict[str, bool] = None,
                 variant_attributes: Dict[str, bool] = None, key_words: List[str] = None):
        if data is None:
            data = {
                USER_REQUIRED_ATTRIBUTES: dict(),
                REQUIRED_ATTRIBUTES: dict(),
                VARIANT_ATTRIBUTES: dict(),
                ATTRIBUTES: dict()
            }

        attributes_data = self.assign_attributes(data,
                                                 user_required_attributes,
                                                 required_attributes,
                                                 variant_attributes,
                                                 attributes)
        user_required_attributes, required_attributes, variant_attributes, attributes = attributes_data
        schema_attributes, user_attributes = self.create_schema_attributes(required_attributes,
                                                                           variant_attributes,
                                                                           attributes,
                                                                           user_required_attributes)

        if OBJECT_ID in data:
            del data[OBJECT_ID]
        if class_name is not None:
            data[CLASS] = class_name
        if storage_id is not None:
            data[STORAGE_ID] = storage_id
        if parent_class is not None:
            data[PARENT_CLASS] = parent_class
        if user_required_attributes:
            data[USER_REQUIRED_ATTRIBUTES] = user_attributes
        if required_attributes:
            data[REQUIRED_ATTRIBUTES] = {key: value for key, value in schema_attributes.items()
                                         if key in required_attributes}
        if attributes:
            data[ATTRIBUTES] = {key: value for key, value in schema_attributes.items() if key in attributes}
        if variant_attributes:
            data[VARIANT_ATTRIBUTES] = {key: value for key, value in schema_attributes.items()
                                        if key in variant_attributes}
        if key_words is not None:
            data[KEY_WORDS] = key_words
        if validate:
            self.validate_data(data)
        self.data = data

    @staticmethod
    def assign_attributes(data, user_required_attributes, required_attributes, variant_attributes, attributes):
        attributes_name = [USER_REQUIRED_ATTRIBUTES, REQUIRED_ATTRIBUTES, VARIANT_ATTRIBUTES, ATTRIBUTES]
        attributes_variable = [user_required_attributes, required_attributes, variant_attributes, attributes]

        for idx, (var, name) in enumerate(zip(attributes_variable, attributes_name)):
            if not var and name in data and data[name]:
                attributes_variable[idx] = data[name]
            else:
                attributes_variable[idx] = dict()
        return attributes_variable

    @classmethod
    def create_schema_attributes(
        cls,
        required_attributes,
        variant_attributes,
        attributes,
        user_required_attributes
    ):
        all_attributes = list(required_attributes.items()) + list(variant_attributes.items()) + list(attributes.items())
        schema_attributes: Dict[str, SchemaAttribute] = dict()
        user_attributes: Dict[str, SchemaAttribute] = dict()

        for key, value in all_attributes:
            if key in schema_attributes and schema_attributes[key].enable != value:
                raise ValueError(f"Attribute {key} must have consistent enable value across attribute fields")
            schema_attributes[key] = SchemaAttribute(enable=value)

        for key, value in user_required_attributes.items():
            user_attributes[key] = SchemaAttribute(enable=value)

        return schema_attributes, user_attributes

    @staticmethod
    def get_class_by_type(object_class):
        try:
            return getattr(sys.modules[__name__], object_class)
        except Exception as e:
            return None

    @staticmethod
    def generate_schema_id(class_name: str, parent_class: str, storage_id: str):
        return f"{class_name}_{parent_class}_{storage_id}"

    @property
    def schema_id(self):
        return self.generate_schema_id(self.class_name(), self.parent_class, self.storage_id)

    def class_name(self):
        return self.data[CLASS]

    @property
    def storage_id(self):
        return self.data.get(STORAGE_ID, "default")

    @property
    def parent_class(self):
        return self.data.get(PARENT_CLASS)

    @property
    def user_required_attributes(self):
        return self.data.get(USER_REQUIRED_ATTRIBUTES, dict())

    @user_required_attributes.setter
    def user_required_attributes(self, _user_required_attributes):
        for key, value in _user_required_attributes.items():
            self.data[USER_REQUIRED_ATTRIBUTES][key].enable = value

    @property
    def required_attributes(self):
        return self.data.get(REQUIRED_ATTRIBUTES, dict())

    @required_attributes.setter
    def required_attributes(self, _required_attributes):
        for key, value in _required_attributes.items():
            self.data[REQUIRED_ATTRIBUTES][key].enable = value

    @property
    def attributes(self):
        return self.data.get(ATTRIBUTES, dict())

    @attributes.setter
    def attributes(self, _attributes):
        for key, value in _attributes.items():
            self.data[ATTRIBUTES][key].enable = value

    @property
    def variant_attributes(self):
        return self.data.get(VARIANT_ATTRIBUTES, dict())

    @variant_attributes.setter
    def variant_attributes(self, _variant_attributes: Dict[str, bool]):
        for key, value in _variant_attributes.items():
            self.data[VARIANT_ATTRIBUTES][key].enable = value
            self.data[REQUIRED_ATTRIBUTES][key].enable = value

    @property
    def json_attributes(self):
        all_attributes = list(self.attributes.keys()) + \
                         list(self.required_attributes.keys()) + \
                         list(self.variant_attributes.keys())
        return list(set(all_attributes))

    @property
    def json(self):
        json_data = {**self.data}
        json_data[ATTRIBUTES] = {key: value.enable for key, value in json_data[ATTRIBUTES].items()}
        json_data[REQUIRED_ATTRIBUTES] = {key: value.enable for key, value in json_data[REQUIRED_ATTRIBUTES].items()}
        json_data[VARIANT_ATTRIBUTES] = {key: value.enable for key, value in json_data[VARIANT_ATTRIBUTES].items()}
        json_data[USER_REQUIRED_ATTRIBUTES] = {key: value.enable
                                               for key, value in json_data[USER_REQUIRED_ATTRIBUTES].items()}
        return json_data

    @property
    def static_info(self):
        return {
            PARENT_CLASS: self.parent_class,
            CLASS: self.class_name(),
            STORAGE_ID: self.storage_id
        }

    @staticmethod
    def validate_data(data):
        for attribute in [CLASS, REQUIRED_ATTRIBUTES, VARIANT_ATTRIBUTES]:
            if attribute not in data:
                raise ValueError(f"{attribute} key must exist")

        if not set(data[VARIANT_ATTRIBUTES].keys()).issubset(data[REQUIRED_ATTRIBUTES].keys()):
            raise ValueError(f"Variants attributes must be a subset of required attributes")

    @staticmethod
    def from_json(data, **kwargs):
        class_name = data.get(CLASS)
        if class_name is None:
            schema_class = BaseSchemaConfig
        else:
            schema_class_name = f"{class_name}SchemaConfig"
            schema_class = BaseSchemaConfig.get_class_by_type(schema_class_name)
            if schema_class is None:
                schema_class = BaseSchemaConfig
        return schema_class(data, **kwargs)


class ProductSchemaConfig(BaseSchemaConfig):
    def __init__(self, data=None, validate=True, class_name: str = None, storage_id: str = None,
                 parent_class: str = None, user_required_attributes: str = None,
                 required_attributes: List[str] = None, attributes: List[str] = None,
                 variant_attributes: List[str] = None, size_table: Dict = None):
        super(ProductSchemaConfig, self).__init__(data=data, validate=validate, class_name=class_name,
                                                  storage_id=storage_id, parent_class=parent_class,
                                                  user_required_attributes=user_required_attributes,
                                                  required_attributes=required_attributes, attributes=attributes,
                                                  variant_attributes=variant_attributes)
        if size_table is not None:
            self.size_table = ProductSizeInfo(**size_table)
        elif data.get(SIZE_TABLE) is not None:
            self.size_table = ProductSizeInfo(**data.get(SIZE_TABLE))
        else:
            self.size_table = None

    @property
    def json(self):
        json_data = super().json
        json_data[SIZE_TABLE] = self.size_table.dict() if self.size_table is not None else None
        return json_data
