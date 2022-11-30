from TMTChatbot.Common.storage.base_storage import BaseStorage

from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Common.config.config import Config


class Json2ImageService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(Json2ImageService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.bill_generation_url}/process"
        self.storage = storage

    def _pre_process(self, input_data):
        if not isinstance(input_data, list):
            input_data = [input_data]
        return BaseDataModel(data=input_data)

    def _post_process(self, data: BaseDataModel) -> str:
        if data is not None:
            result = data.data.get("image", "")
        else:
            result = ""
        return result

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
