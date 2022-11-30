from typing import Set, List
from datetime import datetime

from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import User, Bill
from TMTChatbot.StateController.services.value_mapping import map_product_inventory
from TMTChatbot.StateController.services.multiple_choice_manager import MultipleChoiceManager
from TMTChatbot.StateController.services.product_search_manager import ProductSearchManager
from TMTChatbot.StateController.services.user_manager import UserManager


class BotIntent(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(BotIntent, self).__init__(config=config)
        self.storage = storage
        self.multiple_choice_manager = MultipleChoiceManager(config=config, storage=self.storage)
        self.product_search_manager = ProductSearchManager(config=config, storage=self.storage)
        self.user_manager = UserManager(config=config, storage=storage)
        self.global_intent_extractors = [
            self.object_intents,
            self.user_manager.update_user_attribute_status(True),
            self.user_missing_info_intents,
            self.bill_missing_info_intents,
            self.mentioned_objects,

            self.validate_bill,
            self.billing_intents,
            self.confirmed_bills,
            self.number_of_old_bills,

            self.product_search_intents,

            # update bot intents for DATETIME and MONEY entity
            self.user_mentioned_entity
        ]
        self.state_based_intent_extractors = [
            self.multi_value_expectations,
            self.multiple_choice_manager.unique_bill_object(True),
            self.wrong_phone_intent
        ]

    def add_intent_extraction_func(self, func):
        self.state_based_intent_extractors.append(func)

    def product_search_intents(self, conversation: Conversation) -> Set[str]:
        output_intents = set()
        if self.product_search_manager.check_url(conversation):
            if not conversation.pending_message.message or len(conversation.pending_message.message) <= 1:
                output_intents.add(BOT_USER_SEND_IMAGE)
            else:
                output_intents.add(BOT_USER_SEND_IMAGE_TEXT)
        return output_intents

    @staticmethod
    def number_of_old_bills(conversation: Conversation) -> Set[str]:
        """
        return BOT_NONE_OLD_BILL if there is no CONFIRMED or DONE bill
        :param conversation:
        :return:
        """
        output_intents = set()
        if len(conversation.data.old_bills) > 0:
            output_intents.add(BOT_MULTIPLE_OLD_BILLS)
        else:
            output_intents.add(BOT_NONE_OLD_BILL)
        return output_intents

    @staticmethod
    def confirmed_bills(conversation: Conversation) -> Set[str]:
        """
        If there is no confirmed bill -> return BOT_NONE_CONFIRMED_BILL
        If there is only one confirmed bill -> return BOT_SINGLE_CONFIRMED_BILL + <BILL_STATUS>
        If there are many bills (>=2) -> return BOT_MULTIPLE_CONFIRMED_BILLS for choosing which bill the user requires
        :param conversation: current Conversation
        :return:
        """
        output_intents = set()
        bills: List[Bill] = conversation.data.confirmed_bills
        if len(bills) == 0:
            output_intents.add(BOT_NONE_CONFIRMED_BILL)
        elif len(bills) == 1:
            output_intents.add(BOT_SINGLE_CONFIRMED_BILL)
        else:
            output_intents.add(BOT_MULTIPLE_CONFIRMED_BILLS)
        return output_intents

    @staticmethod
    def validate_bill(conversation: Conversation) -> Set[str]:
        """
        Use all objects in bill to add BOT_BILL_VALID_PRODUCTS
        :param conversation: Conversation
        :return:
        """
        output_intents = set()
        bill = conversation.data.bill
        if bill is not None:
            all_products = bill.confirmed_products
            if len(all_products) > 0:
                for bill_product in all_products:
                    if bill_product.has_multiple_value_attributes:
                        return output_intents
                output_intents.add(BOT_BILL_VALID_PRODUCTS)
            else:
                """
                TEST => user_id == "nguyenpq" -> 
                """
                output_intents.add(BOT_BILL_EMPTY)
        return output_intents

    @staticmethod
    def wrong_phone_intent(conversation: Conversation) -> Set[str]:
        """
        add USER_WRONG_PHONE_NUMBER if phone not right
        :param conversation: Conversation
        :return:
        """
        output_intents = set()
        message = conversation.current_state.message
        entities = message.entities
        if entities is not None:
            for entity in message.entities:
                if entity.label == "wrong_phone":
                    output_intents.add(BOT_USER_WRONG_PHONE)
                    return output_intents
        return output_intents

    @staticmethod
    def mentioned_objects(conversation: Conversation) -> Set[str]:
        """
        if user mentioned an object in 5 minutes, then add USER_MENTIONED_OBJECT
        :param conversation:
        :return:
        """
        output_intents = set()
        nodes = conversation.data.get_previous_node(mentioned_time_range=datetime.now().timestamp() - 5 * 60)
        if nodes is not None and len(nodes) > 0:
            output_intents.add(USER_MENTIONED_OBJECT)
        return output_intents

    @staticmethod
    def multi_value_expectations(conversation: Conversation) -> Set[str]:
        """
        Getting user info that has multiple values from Conversation.current_state.all_expected_values
        :param conversation: Conversation
        :return:
        """
        output_intents = set()
        current_state = conversation.current_state
        if current_state is None:
            return output_intents
        state_action_config = current_state.state_action_config
        all_expected_values = state_action_config.all_expected_values
        user = conversation.user
        for expected_value in all_expected_values:
            attr = expected_value.attr
            value = user.get_attr(attr)
            if value is not None and isinstance(value, list) and len(value) > 1:
                output_intents.add(f"{USER_MULTI_VALUE}_{attr}")
        return output_intents

    @staticmethod
    def object_intents(conversation: Conversation) -> Set[str]:
        output_intents = set()
        current_nodes = conversation.data.get_previous_node()
        if len(current_nodes) > 1:
            output_intents.add(BOT_MULTI_OBJECTS)
        elif len(current_nodes) == 1:
            # current_node = current_nodes[0]
            # # inventory = current_node.get_attr("inventory")
            inventory = map_product_inventory(conversation)
            if inventory is None or (isinstance(inventory, list) and len(inventory) == 0):
                output_intents.add(BOT_ZERO_INVENTORY)
            else:
                output_intents.add(BOT_HAVE_INVENTORY)
        else:
            output_intents.add(BOT_OBJECT_NOT_FOUND)
        return output_intents

    @staticmethod
    def user_missing_info_intents(conversation: Conversation) -> Set[str]:
        output_intents = set()
        user: User = conversation.user
        missing_required_attributes = user.missing_required_attributes
        for attr in missing_required_attributes:
            output_intents.add(f"{BOT_BASE_USER_MISSING_INFO}_{attr}")
        return output_intents

    @staticmethod
    def bill_missing_info_intents(conversation: Conversation) -> Set[str]:
        output_intents = set()
        bill: Bill = conversation.data.bill
        missing_required_infor = bill.missing_required_infor
        for attr in missing_required_infor:
            output_intents.add(f"{BOT_BASE_BILL_MISSING_INFO}_{attr}")
        return output_intents

    @staticmethod
    def billing_intents(conversation: Conversation) -> Set[str]:
        output_intents = set()
        bill = conversation.data.bill
        if bill.confirmed:
            output_intents.add(BOT_BILL_CONFIRMED)
        elif bill.is_processing:
            output_intents.add(BOT_BILL_PROCESSING)
        return output_intents

    def extract_global_intents(self, conversation: Conversation):
        intents = set()
        for intent_extractor in self.global_intent_extractors:
            intents = intents.union(intent_extractor(conversation))
        intents = list(intents)
        conversation.pending_message.update_intents(intents)

    def extract_state_based_intents(self, conversation: Conversation):
        intents = set()
        for intent_extractor in self.state_based_intent_extractors:
            intents = intents.union(intent_extractor(conversation))
        intents = list(intents)
        conversation.current_state.message.update_intents(intents)

    @staticmethod
    def user_mentioned_entity(conversation: Conversation):
        """
        check whether user is mentioning time in message => add particular time to extra_data of corresponding ner tag
        :param conversation:
        :return:
        """
        output_intents = set()
        message = conversation.pending_message
        if not message:
            return output_intents
        if message.entities is None:
            return output_intents
        for idx, ent in enumerate(message.entities):
            if any(label in ["DATE", "TIME", "Time"] for label in ent.labels) and ent.parsed_value:
                output_intents.add(BOT_USER_MENTIONED_TIME)
            elif any(label in ["MONEY"] for label in ent.labels) and ent.parsed_value:
                output_intents.add(BOT_USER_MENTIONED_MONEY)
        return output_intents
