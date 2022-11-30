from typing import List

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Schema.objects.common.nlp_tags import NerTag
from TMTChatbot.Schema.objects.conversation.conversation import Conversation, Message
from TMTChatbot.Schema.objects.graph.graph_data import Bill
from TMTChatbot.AlgoClients.ner_service import NERService


class UserManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(UserManager, self).__init__(config=config)
        self.storage = storage
        self.ner_service = NERService(storage=self.storage, config=config)

    # TODO pending replace by BotIntent.global_intent_extractors.update_user_attribute_status(True)
    # @staticmethod
    # def check_user_multi_value(is_global=False):
    #     def _check_state_user_multi_value(conversation: Conversation):
    #         user = conversation.data.user
    #         required_attributes = user.schema.required_attributes
    #         output = []
    #         for attr in required_attributes:
    #             attr_value = user.get_attr(attr)
    #             if len(attr_value) > 1:
    #                 output.append(f"{BOT_BASE_USER_MULTI_INFO}_{attr}")
    #             elif len(attr_value) == 1:
    #                 output.append(f"{BOT_BASE_USER_HAS_ONE_INFO}_{attr}")
    #             else:
    #                 output.append(f"{BOT_BASE_USER_MISSING_INFO}_{attr}")
    #         if not is_global:
    #             conversation.current_state.update_intents(output)
    #         else:
    #             return output
    #     return _check_state_user_multi_value

    def update_user_gender_by_name(self, conversation: Conversation):
        user = conversation.user
        if (user.gender is None or user.gender in [DEFAULT, ""]) and \
                (user.user_name is not None and user.user_name not in [DEFAULT, ""]):
            message = Message(message=user.user_name, storage_id=DEFAULT)
            self.ner_service([None, message])
            if message.entities is not None and isinstance(message.entities, list):
                for entity in message.entities:
                    entity: NerTag
                    if entity.label == GENDER:
                        user.set_attr(GENDER, entity.parsed_value)
                        user.save(force=True)
                        self.logger.info(f"Extract gender of {user.user_name} - {user.id}: {user.gender}")
                        break

    @staticmethod
    def update_user_infor_multiple_choices(conversation: Conversation):
        node = conversation.current_state.message.multiple_choices
        if node:
            node = node[0]
            conversation.user.set_attr(node.id, node.name)
            conversation.current_state.message.drop_intents([f"{BOT_BASE_USER_MISSING_INFO}_{node.id}"])

    @staticmethod
    def update_user_attribute_status(is_global=False):
        def _update_user_attribute_status(conversation: Conversation):
            user = conversation.data.user
            user_attributes = user.schema.attributes
            output = []
            for attr in user_attributes:
                attr_value = user.get_attr(attr)
                if len(attr_value) > 1:
                    output += [f"{BOT_BASE_USER_HAS_ATTRIBUTE}_{attr}", f"{BOT_BASE_USER_MULTI_INFO}_{attr}"]
                elif len(attr_value) == 1:
                    output += [f"{BOT_BASE_USER_HAS_ATTRIBUTE}_{attr}", f"{BOT_BASE_USER_HAS_ONE_INFO}_{attr}"]
                else:
                    output.append(f"{BOT_BASE_USER_MISSING_INFO}_{attr}")
            if not is_global:
                conversation.current_state.update_intents(output)
            else:
                return output

        return _update_user_attribute_status

    @staticmethod
    def check_user_history_bill(conversation: Conversation):
        bills: List[Bill] = [node for node in conversation.data.all_nodes if node.class_name() == Bill.class_name()]
        confirmed_bills = [bill for bill in bills if bill.confirmed]
        if not confirmed_bills:
            conversation.current_state.update_intents([BOT_USER_NO_HISTORY_BILL])
        else:
            conversation.current_state.update_intents([BOT_USER_HAS_HISTORY_BILL])
