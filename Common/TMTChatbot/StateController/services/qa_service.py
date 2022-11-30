from typing import List

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.common_key_mapping import KEY_MAPPING
from TMTChatbot.Common.common_phrases import DEFAULT_QUESTION_WORD
from TMTChatbot.Common.default_intents import *
from TMTChatbot.AlgoClients.graph_qa_service import GraphQAService
from TMTChatbot.AlgoClients.doc_qa_service import DocQAService
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Schema.objects.common.nlp_tags import Intent
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Product, Bill, Shop


class QAService(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(QAService, self).__init__(config=config)
        self.graph_qa_service = GraphQAService(config=config, storage=storage)
        self.qa_objects = {Product.class_name().lower(), Bill.class_name().lower(), Shop.class_name().lower()}

    def answer_user_product_question(self, conversation: Conversation):
        answer = self.graph_qa_service(conversation)
        conversation.current_state.message.answer_infor = answer
        if answer is None or answer == "":
            conversation.current_state.message.update_intents([BOT_CANNOT_ANSWER])
        else:
            conversation.current_state.message.update_intents([BOT_HAS_ANSWER])

    def answer_user_product_question_with_intent(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            conversation.current_state.message.update_intents([BOT_CANNOT_ANSWER])
            return
        intent_set: List[Intent] = current_state.intents
        for intent in intent_set:
            if intent.action == "request" and intent.object in self.qa_objects:
                question_attr = intent.object_detail
                if question_attr is None or question_attr in ["info", "specific_attribute"]:
                    continue
                mapped_question_attr = KEY_MAPPING.get(question_attr, question_attr)
                objects = conversation.data.get_previous_node(node_class=intent.object.capitalize())
                if len(objects) != 1:
                    conversation.current_state.message.update_intents([BOT_CANNOT_ANSWER])
                    return
                requested_object = objects[0]
                values = requested_object.get_attr(question_attr)
                if values is not None and len(values) > 0:
                    value = ", ".join(values)
                else:
                    values = requested_object.get_attr(mapped_question_attr.replace(" ", "_"))
                    if values is not None and len(values) > 0:
                        value = ", ".join(values)
                    else:
                        value = self.graph_qa_service \
                            .custom_node_question(conversation=conversation,
                                                  question=f"{mapped_question_attr} "
                                                           f"{DEFAULT_QUESTION_WORD}",
                                                  node=requested_object)
                conversation.current_state.message.answer_infor = value
                if value is None or value == "":
                    conversation.current_state.message.update_intents([BOT_CANNOT_ANSWER])
                else:
                    conversation.current_state.message.update_intents([BOT_HAS_ANSWER])

    def answer_custom_question(self, conversation: Conversation):
        pass
