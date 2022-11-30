from typing import List, Tuple

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.utils.unit_parser import UnitParser
from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.common.nlp_tags import NerTag
from TMTChatbot.Schema.objects.conversation.conversation import Message
from TMTChatbot.AlgoClients.address_service import AddressService
from TMTChatbot.Common.config.config import Config


class NERService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(NERService, self).__init__(config=config)
        self.address_service = AddressService(config=config, storage=storage)
        self.session = None
        self.api_url = f"{self.config.ner_url}/process"
        self.sep = " , , , "

    def _pre_process(self, input_data: List[Message]):
        history, current_message = input_data
        if history is None:
            history_message = ""
        else:
            history_message = " ".join(history.message.split(" ")[-10:])
        json_data = current_message.all_data
        json_data["message"] = f"{history_message}{self.sep}{current_message.message}"
        return BaseDataModel(data=json_data)

    @staticmethod
    def _concat_entity_phrase(entities: List[NerTag]) -> List[NerTag]:
        """
        Concat adjacent entities with same Ner label -> Ner phrase

        :param entities:
        :return:
        """
        entity_phrases = []
        adjacent_entities = [tag for tag in entities if tag.label in ["DATE", "TIME", "Time"]]
        adjacent_entities.sort(key=lambda x: x.begin)
        # remove entity with same text and different label
        adjacent_entities = list({tag.text: tag for tag in adjacent_entities}.values())

        sub_phrases = []
        for tag in adjacent_entities:
            if not sub_phrases:
                sub_phrases.append(tag)
            else:
                if tag.begin == sub_phrases[-1].end + 1:
                    sub_phrases.append(tag)
                else:
                    if len(sub_phrases) >= 2:
                        join_text = ", ".join([e.text for e in sub_phrases])
                        entity_phrases.append(NerTag(begin=sub_phrases[0].begin, end=sub_phrases[-1].end,
                                                     text=" ".join([e.text for e in sub_phrases]), label="DATE",
                                                     parsed_value=UnitParser.normalize(join_text, "DATE")))
                    sub_phrases = []
        if sub_phrases and len(sub_phrases) >= 2:
            join_text = ", ".join([e.text for e in sub_phrases])
            entity_phrases.append(
                NerTag(begin=sub_phrases[0].begin, end=sub_phrases[-1].end,
                       text=" ".join([e.text for e in sub_phrases]),
                       label="DATE", parsed_value=UnitParser.normalize(join_text, "DATE")))
        return entity_phrases

    def _post_process(self, data: BaseDataModel, old_entities: List[NerTag] = None) -> Tuple[List[NerTag], str, bool]:
        has_address = False
        if data is not None:
            all_tags = data.data.get("entities", [])
            all_tags = [NerTag(**item) for item in all_tags]
            tags = []
            message = data.data.get("message")
            sep_index = message.find(self.sep)
            start_index = sep_index + len(self.sep)
            message = message[start_index:]
            for tag in all_tags:
                if tag.label in ["ADDRESS", "GPE"]:
                    has_address = True
                if tag.label in ["GPE", "ADDRESS", "LOC"]:
                    continue
                if tag.begin is not None:
                    if tag.begin >= start_index:
                        tag.begin -= start_index
                        tag.end -= start_index
                        tags.append(tag)
                else:
                    tags.append(tag)
        else:
            tags = []
            message = None

        if old_entities is not None:
            tags += old_entities
        # TODO: done = False
        done = True
        while not done:
            done = True
            result = []
            for tag in tags:
                if len(result) == 0:
                    result.append(tag)
                else:
                    is_new = True
                    for i, new_tag in enumerate(result):
                        if tag in new_tag:
                            new_tag.join(tag)
                            is_new = False
                            done = False
                            break
                        elif new_tag in tag:
                            tag.join(new_tag)
                            result[i] = tag
                            is_new = False
                            done = False
                            break
                    if is_new:
                        result.append(tag)
            tags = result
        # add DATETIME 'phrase' to tags
        tags += self._concat_entity_phrase(tags)
        return tags, message, has_address

    def __call__(self, input_data: List[Message], key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if input_data is not None and input_data[-1] is not None and self.api_possible():
            _, current_message = input_data
            if current_message.entities is not None and len(current_message.entities) > 0:
                return None, current_message

            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            output, message, has_address = self._post_process(result, current_message.entities)
            current_message.entities = output
            if message is not None:
                current_message.message = message
            if has_address:
                self.address_service(current_message)
            if len(current_message.entities) == 0:
                current_message.entities.append(NerTag(text="", label="", begin=0, end=0))
            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data
