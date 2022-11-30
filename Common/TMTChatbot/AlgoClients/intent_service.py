from typing import List

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.common.nlp_tags import Intent
from TMTChatbot.Schema.objects.conversation.conversation import Message


class IntentService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(IntentService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.intent_url}/process"
        self.storage = storage

    def _pre_process(self, input_data: Message):
        return BaseDataModel(data=input_data.all_data)

    def _post_process(self, data: BaseDataModel) -> List[Intent]:
        if data is not None:
            json_data = data.data.get("intents", [])
            result = []
            for json_intent in json_data:
                tags = json_intent["tag"].split("+")
                for tag in tags:
                    result.append(Intent(tag=tag, score=json_intent["score"]))
        else:
            result = []
        for intent in result:
            intent.score = 1
        return result

    def __call__(self, input_data: Message, key=None, postfix="", num_retry: int = None, call_prop: float = 0,
                 add_has_message_intent: bool = True):
        if input_data is not None and self.api_possible():
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            output: List[Intent] = self._post_process(result)

            input_data.update_intents(output)
            if add_has_message_intent:
                if input_data.message is not None and len(input_data.message) > 0:
                    input_data.update_intents([USER_HAS_MESSAGE])
            else:
                input_data.drop_intents([USER_HAS_MESSAGE])
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data
