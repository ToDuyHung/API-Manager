from typing import Dict

from TMTChatbot.Common.storage.base_storage import BaseStorage

from TMTChatbot.AlgoClients.node_search_service import NodeSearchService
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot import BaseDataModel
from TMTChatbot.Common.storage.mongo_client import MongoConnector
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Common.common_keys import *


class BillImageService(NodeSearchService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(BillImageService, self).__init__(config=config, storage=storage)
        self.api_url = f"{self.config.bill_image_service_url}/process"
        self.storage = storage

    def _post_process(self, data: BaseDataModel, conversation: Conversation = None) -> Dict:
        if data is None:
            return {}
        else:
            api_output: Dict = data.data
            return api_output

    def _pre_process(self, input_data: Conversation) -> BaseDataModel:
        data = {}
        if len(input_data.current_state.message.urls) > 0:
            data = {
                IMAGE_URL: input_data.current_state.message.urls[0]
            }
        elif input_data.current_state.message.base64_img:
            data = {
                IMAGE_URL: input_data.current_state.message.base64_img
            }
        return BaseDataModel(data=data)

    def __call__(self, input_data: Conversation, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if (len(input_data.current_state.message.urls) > 0 or input_data.current_state.message.base64_img) \
                and self.api_possible():
            input_data.current_state.message.update_intents([BOT_USER_SEND_IMAGE])
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data))
            api_output = self._post_process(result, conversation=input_data)

            if api_output:
                if not api_output[CHECK_INPUT_DATA]:
                    pass
                elif api_output[CHECK_INPUT_DATA] and api_output[MONEY] <= 0:
                    """
                    Invalid bill image or money
                    """
                    pass
                elif api_output[CHECK_INPUT_DATA] and api_output[MONEY] > 0:
                    """
                    Valid
                    """
                    # input_data.data.bill.payment = float(api_output[MONEY])
                    input_data.data.bill.set_attr(attr=BILL_PAYMENT, value=int(api_output[MONEY]))
                    input_data.current_state.message.update_intents([BOT_USER_SEND_PAYMENT])

            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data
