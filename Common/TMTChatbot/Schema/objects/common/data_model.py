from uuid import uuid4, uuid5
from typing import AnyStr, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from TMTChatbot.ServiceWrapper.common.status import ResultStatus


class BaseMetaData(BaseModel):
    processing_time: Optional[float]
    receive_time: Optional[float]
    response_time: Optional[float]
    status: Optional[ResultStatus]

    def __init__(self, processing_time: float = None, receive_time: float = None,
                 response_time: float = None, status: ResultStatus = ResultStatus.READY):
        super(BaseMetaData, self).__init__(processing_time=processing_time, receive_time=receive_time,
                                           response_time=response_time, status=status)

    def update_receive_time(self):
        if self.receive_time is None:
            self.receive_time = datetime.now().timestamp()

    def update_response_time(self):
        self.response_time = datetime.now().timestamp()
        self.processing_time = self.response_time - self.receive_time

    @staticmethod
    def from_json(data):
        return BaseMetaData(**data)

    def dict(self, *args, **kwargs):
        return {
            "processing_time": self.processing_time,
            "receive_time": self.receive_time,
            "response_time": self.response_time,
            "status": self.status.value
        }


class BaseDataModel(BaseModel):
    index: AnyStr
    data: Any
    meta_data: Optional[BaseMetaData]

    @staticmethod
    def id_generator():
        base_id = uuid4()
        new_id = uuid5(base_id, str(datetime.now()))
        return str(new_id)

    def __init__(self, index: AnyStr = None, data: Dict = None, meta_data: BaseMetaData = None):
        if index is None:
            index = self.id_generator()
        super(BaseDataModel, self).__init__(index=index, data=data, meta_data=meta_data)
        self.index = str(index)
        if self.meta_data is None:
            self.meta_data = BaseMetaData()

    def update_receive_time(self):
        self.meta_data.update_receive_time()

    def update_response_time(self):
        self.meta_data.update_response_time()

    @staticmethod
    def from_json(data):
        meta_data = data.get("meta_data", {})
        meta_data = BaseMetaData.from_json(meta_data)
        data["meta_data"] = meta_data
        return BaseDataModel(**data)
