from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field

from TMTChatbot import BaseDataModel
from TMTChatbot.Common.common_keys import *


class GetSchemaRequest(BaseModel):
    storage_id: str
    class_: str = Field(alias=CLASS)


class GetSchemaWithParentRequest(BaseModel):
    storage_id: str
    class_: str = Field(alias=CLASS)
    parent_class: str


class SchemaData(BaseModel):
    class_: str = Field(alias=CLASS)
    parent_class: str
    required_questions: Dict[str, bool]


class Schema(BaseModel):
    schema_: SchemaData = Field(alias=SCHEMA)


class SchemaBody(BaseDataModel):
    data: Schema


class VqaSchemaRequest(BaseModel):
    storage_id: str
    input_data: SchemaBody


class DeleteSchemeData(BaseModel):
    storage_id: str
    class_: str = Field(alias=CLASS)
    parent_class: str
