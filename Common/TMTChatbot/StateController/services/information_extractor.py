from TMTChatbot.Common.storage.mongo_client import MongoConnector
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.Schema.objects.conversation import Conversation, Message
from TMTChatbot.AlgoClients.intent_service import IntentService
from TMTChatbot.AlgoClients.ner_service import NERService
from TMTChatbot.AlgoClients.graph_qa_service import GraphQAService
from TMTChatbot.AlgoClients.node_search_service import NodeSearchService
from TMTChatbot.StateController.services.product_search_manager import ProductSearchManager
from TMTChatbot.StateController.services.multiple_choice_manager import MultipleChoiceManager
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Common.default_intents import *


class BaseInformationExtractor(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(BaseInformationExtractor, self).__init__(config=config)
        self.storage = storage
        self.intent_model = IntentService(config=config, storage=storage)
        self.ner_service = NERService(config=config, storage=storage)
        self.graph_qa_service = GraphQAService(config=config, storage=storage)
        self.product_search_manager = ProductSearchManager(config=config, storage=storage)
        self.multiple_choice_manager = MultipleChoiceManager(config=config, storage=storage)

    @staticmethod
    def mapping_user_info(conversation: Conversation, is_new_action: bool = False):
        """
        If there is no last message => default add ner to user attributes.
        Mapping user infor with expected entity type (currently not use <ExpectedEntity.subject>).
        Drop some expectations if mapped
        :param
        conversation: current conversation
        is_new_action: if this is a new action => not mapping has_message intent
        :return:
        """
        user = conversation.user
        intents = conversation.current_state.intent_set
        message = conversation.current_state.message
        entities = message.entities
        entities = entities if entities is not None else []
        new_attr = False
        for current_expectations in conversation.current_action.branches.values():
            if current_expectations is not None:
                matched_intents, matched_entities, new_intents = current_expectations.validate(intents, entities)

                # Add intents based on provided entities
                conversation.current_state.update_intents(new_intents)
                for expected_intent in current_expectations.intents.values():
                    if is_new_action and expected_intent.tag == USER_HAS_MESSAGE:
                        continue
                    if expected_intent.tag in matched_intents:
                        expected_intent.done = True
                if matched_entities is not None:
                    for expected_tag, entity in matched_entities:
                        user.set_attr(expected_tag.attr, entity.parsed_value)
                        expected_tag.done = True
                        expected_tag.forward_done_signal(True)
                        new_attr = True
                        message.drop_intents([f"{BOT_BASE_USER_MISSING_INFO}_{expected_tag.attr}"])
        if new_attr:
            user.save(force=True)

    @staticmethod
    def map_expectation(conversation: Conversation):
        """
        Mapping user info with expected values of current state config: Conversation.current_state.state_action_config
        :param conversation: Conversation
        :return:
        """
        current_state = conversation.current_state
        if current_state is None:
            return
        state_action_config = current_state.state_action_config
        unsatisfied_expected_values = state_action_config.unsatisfied_expected_values
        user = conversation.user
        for expected_value in unsatisfied_expected_values:
            attr = expected_value.attr
            value = user.get_attr(attr)
            if value is not None:
                if (isinstance(value, list) or isinstance(value, str)) and len(value) > 0:
                    expected_value.done = True

    @staticmethod
    def map_bot_expectation(conversation: Conversation, is_global=False):
        """
        Mapping only bot intent
        :param conversation: current Conversation
        :param is_global: if is_global, pending message will be used instead of current_message to get intents
        :return:
        """
        if is_global:
            intents = conversation.pending_message.intents
        else:
            intents = conversation.current_state.intent_set
        for current_expectations in conversation.current_action.branches.values():
            if current_expectations is not None:
                for expected_intent in current_expectations.intents.values():
                    if expected_intent.is_bot_intent and expected_intent.tag in intents:
                        expected_intent.done = True

    def message_information_extraction(self, conversation: Conversation, is_new_action: bool = False):
        message = conversation.pending_message
        import time

        s = time.time()
        has_product_in_attachment = self.product_search_manager.search_product_in_attachment(conversation)
        if not has_product_in_attachment:
            self.ner_service([None, message])
            self.logger.debug(f"----ner {time.time() - s}")
            if self.multiple_choice_manager.check_user_has_pending_choices(conversation):
                s = time.time()
                self.multiple_choice_manager(conversation)
                self.logger.debug(f"----multiple choice search {time.time() - s}")
            if not self.multiple_choice_manager.check_user_has_choice(conversation):
                s = time.time()
                self.product_search_manager.search_product_in_message(conversation)
                self.logger.debug(f"----node search {time.time() - s}")
            s = time.time()
            self.intent_model(message, add_has_message_intent=not is_new_action)
            self.logger.debug(f"----intent {time.time() - s}")

    def information_extraction(self, conversation: Conversation, is_new_action: bool = False):
        current_state = conversation.current_state
        if current_state.message is not None and current_state.message.message is not None:
            self.message_information_extraction(conversation, is_new_action=is_new_action)

    def mapping_info(self, conversation: Conversation, is_new_action: bool = False):
        current_state = conversation.current_state
        if current_state.message is not None and current_state.message.message is not None:
            self.mapping_user_info(conversation, is_new_action=is_new_action)
        self.map_expectation(conversation)
