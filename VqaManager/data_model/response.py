from enum import auto
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from fastapi_utils.enums import StrEnum
from TMTChatbot.Common.common_keys import *


class ResponseStatus(StrEnum):
    SUCCESS = auto()
    NO_PRODUCT = auto()
    NO_SHOP = auto()
    NO_BANK_ACCOUNT = auto()
    NO_POLICY = auto()
    NO_BRANCH = auto()
    WRONG_REQUIRED_ATTRIBUTES = auto()
    NOT_FOUND = auto()
    ERROR = auto()


class SchemaResponse(BaseModel):
    schema_: Optional[Any] = Field(alias=SCHEMA)
    status: ResponseStatus

    def __init__(self, schema: Any = None, status: ResponseStatus = None):
        super(SchemaResponse, self).__init__(schema_=schema, status=status)
        self.schema_ = schema
        self.status = status


class ProductResponse(BaseModel):
    products: Optional[List[Any]]
    status: ResponseStatus

    def __init__(self, products: List[Any] = None, status: ResponseStatus = None):
        super(ProductResponse, self).__init__(products=products, status=status)
        self.products = products
        self.status = status


class ShopResponse(BaseModel):
    shop: Optional[Any]
    status: ResponseStatus

    def __init__(self, shop: Any = None, status: ResponseStatus = None):
        super(ShopResponse, self).__init__(shop=shop, status=status)
        self.shop = shop
        self.status = status


class BankResponse(BaseModel):
    bank: Optional[Any]
    status: ResponseStatus

    def __init__(self, bank: Any = None, status: ResponseStatus = None):
        super(BankResponse, self).__init__(bank=bank, status=status)
        self.bank = bank
        self.status = status


class ImageResponse(BaseModel):
    list_image_failed: Optional[List[str]] = None
    status: ResponseStatus

    def __init__(self, list_image_failed: Any = None, status: ResponseStatus = None):
        super(ImageResponse, self).__init__(list_image_failed=list_image_failed, status=status)
        self.list_image_failed = list_image_failed
        self.status = status


class BranchResponse(BaseModel):
    branches: Optional[List[Any]] = None
    status: ResponseStatus

    def __init__(self, branches: Any = None, status: ResponseStatus = None):
        super(BranchResponse, self).__init__(branches=branches, status=status)
        self.branches = branches
        self.status = status


class PolicyResponse(BaseModel):
    policies: Optional[List[Any]] = None
    status: ResponseStatus

    def __init__(self, policies: Any = None, status: ResponseStatus = None):
        super(PolicyResponse, self).__init__(policies=policies, status=status)
        self.policies = policies
        self.status = status
