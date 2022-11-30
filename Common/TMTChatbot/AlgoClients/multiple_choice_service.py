from TMTChatbot.Common.storage.base_storage import BaseStorage

from TMTChatbot.Schema.objects.graph.graph_data import Node, ValueNode
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.conversation.conversation import Message
from TMTChatbot.Schema.objects.conversation.choice import ChoiceResult
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *


class MultipleChoiceService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(MultipleChoiceService, self).__init__(config=config)
        self.session = None
        self.storage = storage
        self.api_url = f"{self.config.multiple_choice_url}/process/"

    def _pre_process(self, input_data: Message):
        return BaseDataModel(data=input_data.all_data)

    def _post_process(self, data: BaseDataModel) -> ChoiceResult:
        if data is not None:
            if data.data is not None:
                choice_data = data.data.get("choice")
                if choice_data is not None:
                    choice_data = Node.from_json(data.data.get("choice"))
                    score = data.data.get("score")
                    result = ChoiceResult(choice=choice_data, score=score)
                else:
                    result = ChoiceResult(choice=None, score=1)
            else:
                result = ChoiceResult(choice=None, score=1)
        else:
            result = ChoiceResult(choice=None, score=1)
        return result

    def __call__(self, input_data: Message, key=None, postfix="", num_retry: int = None, call_prop: float = 0,
                 add_has_message_intent: bool = True):
        if input_data is not None and self.api_possible():
            if input_data.message is None or input_data.message in ["", "."]:
                output = ChoiceResult(choice=None, score=0)
                result = True
            else:
                data = self._pre_process(input_data)

                result = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                           num_retry=num_retry, call_prop=call_prop)
                output: ChoiceResult = self._post_process(result)
            if output.choice is None:
                input_data.multiple_choices = []
                input_data.update_intents([BOT_USER_UNCLEAR_CHOICE])
            else:
                input_data.multiple_choices = [output.choice]
                if output.score > 0.7:
                    if isinstance(output.choice, ValueNode):
                        input_data.update_intents([BOT_USER_CHOOSE_A_VALUE])
                    else:
                        input_data.update_intents([BOT_USER_CHOOSE_AN_OBJECT])
                else:
                    input_data.update_intents([BOT_USER_UNCLEAR_CHOICE])

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
