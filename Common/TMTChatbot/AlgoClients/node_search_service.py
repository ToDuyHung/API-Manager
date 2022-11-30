from typing import Dict, Union

from TMTChatbot.ServiceWrapper.external_service_wrapper import BaseExternalService
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Schema.objects.common.nlp_tags import NerTag
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Node
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Common.common_keys import *


class NodeSearchService(BaseExternalService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(NodeSearchService, self).__init__(config=config)
        self.session = None
        self.api_url = f"{self.config.node_search_url}/process/"
        self.storage = storage

    def _pre_process(self, input_data: Conversation):
        if input_data.pending_message is not None \
                and input_data.pending_message.message is not None \
                and len(input_data.pending_message.message) > 0:
            return BaseDataModel(data=input_data.all_data)

    def _post_process(self, data: BaseDataModel) -> Union[NerTag, None]:
        if data is not None:
            result: Dict = data.data
            nodes = result[NODES]
            if len(nodes) == 0:
                return None
            else:
                return NerTag(text=result[TEXT], label=result[LABEL], begin=result[BEGIN], end=result[END],
                              extra_data=nodes)
        else:
            return None

    def __call__(self, input_data: Conversation, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        is_api_possible = self.api_possible()
        if is_api_possible:
            data = self._pre_process(input_data)
            if data is None:
                return input_data
            result: BaseDataModel = self.make_request(lambda: self._call_api(data), key=key, postfix=postfix,
                                                      num_retry=num_retry, call_prop=call_prop)
            ner_tag = self._post_process(result)

            if ner_tag is not None:
                nodes = ner_tag.extra_data
                nodes = [Node.from_json(node_data, storage=self.storage) for node_data in nodes]
                if len(nodes) == 1:
                    node = nodes[0]
                    if node.id in input_data.data.nodes:
                        input_data.pending_message.update_intents([USER_MENTION_OLD_OBJECT])
                    else:
                        input_data.pending_message.update_intents([USER_MENTION_OBJECT])
                elif len(nodes) > 1:
                    input_data.pending_message.update_intents([USER_MENTION_UNCLEAR_OBJECTS])
                nodes = input_data.data.add_nodes(nodes)

                if len(nodes) > 0:
                    # current_time = datetime.now().timestamp()
                    # for node in nodes:
                    #     node.set_mentioned_time(current_time)
                    input_data.pending_message.update_entities([ner_tag])

            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data
