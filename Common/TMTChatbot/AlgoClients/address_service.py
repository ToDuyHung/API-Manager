from typing import List, Tuple

from TMTChatbot.Common.storage.base_storage import BaseStorage

from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.common.nlp_tags import NerTag
from TMTChatbot.Schema.objects.conversation.conversation import Message
from TMTChatbot.Common.config.config import Config


class AddressService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(AddressService, self).__init__(config=config)
        self.session = None
        self.api_url = self.config.address_url
        self.storage = storage

    def _pre_process(self, input_data: Message):
        return BaseDataModel(data=input_data.message)

    def _post_process(self, data: BaseDataModel, old_entities: List[NerTag] = None) -> Tuple[List[NerTag], str]:
        if data is not None and data.data is not None:
            tags = [NerTag(**item) for item in data.data.get("tags")]
            if len(tags) > 1:
                tags.sort(key=lambda item: item.begin)
            message = data.data.get("text")
            if len(tags) > 0:
                new_message = ""
                start = 0
                for tag in tags:
                    if len(new_message) > 0:
                        new_begin = len(new_message) + 1
                        new_message += f" {message[start: tag.begin].strip()} {tag.text.strip()}"
                    else:
                        new_begin = tag.begin
                        new_message += f"{message[start: tag.begin].strip()} {tag.text.strip()}"
                    start = tag.end
                    tag.begin = new_begin
                    tag.end = new_begin + len(tag.text.strip())
                if start < len(message) - 1:
                    new_message += f" {message[start + 1:].strip()}"
                message = new_message
        else:
            tags = []
            message = None

        result = []
        if old_entities is not None:
            tags += old_entities
        for tag in tags:
            if len(result) == 0:
                result.append(tag)
            else:
                is_new = True
                for i, new_tag in enumerate(result):
                    if tag in new_tag:
                        new_tag.join(tag)
                        is_new = False
                        break
                    elif new_tag in tag:
                        tag.join(new_tag)
                        result[i] = tag
                        is_new = False
                        break
                if is_new:
                    result.append(tag)
        return result, message

    def __call__(self, input_data: Message, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if input_data is not None and self.api_possible():
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            output, message = self._post_process(result, input_data.entities)
            input_data.entities = output
            if message is not None:
                input_data.message = message
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data
