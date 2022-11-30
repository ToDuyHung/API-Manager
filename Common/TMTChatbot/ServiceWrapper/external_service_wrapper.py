from abc import ABC
from datetime import datetime

from TMTChatbot.Common.config.config import Config
from TMTChatbot.ServiceWrapper.services.base_cache_service import (
    BaseServiceWithCacheSingleton,
    BaseAsyncServiceWithCacheSingleton
)
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel


class BaseExternalService(BaseServiceWithCacheSingleton):
    def __init__(self, config: Config = None):
        super(BaseExternalService, self).__init__(config=config)
        self.session = None
        self.api_url = None
        self.api_alive = True
        self.last_call = datetime.now().timestamp()

    def api_possible(self):
        output = self.api_alive or datetime.now().timestamp() - self.last_call > self.config.external_failed_timeout
        self.last_call = datetime.now().timestamp()
        return output

    def _call_api(self, input_data: BaseDataModel) -> BaseDataModel:
        if self.api_url is None:
            raise ValueError("self.api_url must not be None")
        output = self.session.post(self.api_url, json=input_data.dict()).json()
        return BaseDataModel(**output)

    def _post_process(self, data: BaseDataModel):
        raise NotImplementedError("Need Implementation")

    def _pre_process(self, input_data) -> BaseDataModel:
        raise NotImplementedError("Need Implementation")

    def __call__(self, input_data, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if self.api_possible():
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            output = self._post_process(result)
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return output


class BaseAsyncExternalService(BaseAsyncServiceWithCacheSingleton, BaseExternalService):
    def __init__(self, config: Config = None):
        super(BaseAsyncExternalService, self).__init__(config=config)
        BaseExternalService.__init__(self, config=config)

    async def _call_api(self, input_data: BaseDataModel) -> BaseDataModel:
        if self.api_url is None:
            raise ValueError("self.api_url must not be None")
        output = await self.session.post(self.api_url, json=input_data.dict())
        output = await output.json()
        return BaseDataModel(**output)

    async def __call__(self, input_data, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if self.api_possible():
            data = self._pre_process(input_data)
            result = await self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                             num_retry=num_retry, call_prop=call_prop)
            output = self._post_process(result)
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return output
