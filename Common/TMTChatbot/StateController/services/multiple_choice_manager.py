from typing import Set
from datetime import datetime

from TMTChatbot.AlgoClients.multiple_choice_service import MultipleChoiceService
from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import BillProduct, ValueNode, Product
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.services.billing_service import BillingManager
from TMTChatbot.Common.default_intents import *


class MultipleChoiceManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(MultipleChoiceManager, self).__init__(config=config)
        self.multiple_choice_service = MultipleChoiceService(config=config, storage=storage)
        self.billing_manager = BillingManager(config=config, storage=storage)

    def unique_bill_object(self, is_global: bool = True):
        def _unique_bill_object(conversation: Conversation) -> Set[str]:
            """
            Use current object to get bill object.
            if bill object is not unique (with multiple attribute values), return BOT_PRODUCT_UNIQUE
            :param conversation:
            :return:
            """
            output_intents = set()
            nodes = conversation.data.get_previous_node(node_class=Product.class_name())
            if nodes is not None and len(nodes) == 1:
                node = nodes[0]
                bill = conversation.data.bill
                if bill is not None:
                    bill_product = bill.get_product(node)
                    if bill_product is None:
                        self.billing_manager.add_care_product(conversation)
                        bill_product = bill.get_product(node)
                    if bill_product is not None:
                        if bill_product.has_multiple_value_attributes:
                            if is_global:
                                output_intents.add(BOT_BILL_PRODUCT_NOT_UNIQUE)
                            else:
                                conversation.current_state.message.update_intents([BOT_BILL_PRODUCT_NOT_UNIQUE])
                                conversation.current_state.message.drop_intents([BOT_BILL_PRODUCT_UNIQUE])
                        else:
                            if is_global:
                                output_intents.add(BOT_BILL_PRODUCT_UNIQUE)
                            else:
                                conversation.current_state.message.update_intents([BOT_BILL_PRODUCT_UNIQUE])
                                conversation.current_state.message.drop_intents([BOT_BILL_PRODUCT_NOT_UNIQUE])
            if is_global:
                return output_intents
        return _unique_bill_object

    @staticmethod
    def product_multi_values(conversation: Conversation):
        products = conversation.data.get_previous_node()
        if len(products) == 0:
            return []
        else:
            product = products[0]
        bill_product: BillProduct = conversation.data.bill.get_product(product)
        if bill_product is not None:
            attr = bill_product.multiple_value_attribute
            if attr is not None and attr != PRODUCT_SIZE:
                values = bill_product.get_attr(attr)
                return values
        return []

    @staticmethod
    def update_choice_data(conversation: Conversation):
        message = conversation.pending_message
        if message is None:
            return
        if BOT_USER_CHOOSE_A_VALUE in message.intent_set:
            products = conversation.data.get_previous_node()
            if len(products) == 0:
                return
            else:
                product = products[0]
            bill_product: BillProduct = conversation.data.bill.get_product(product)
            if bill_product is not None:
                attr = bill_product.multiple_value_attribute
                # Only map attribute value with attribute of product
                # Check `attr not None` to avoid multiple choices for phone_number and address values
                if attr:
                    value = message.multiple_choices[0]
                    bill_product.set_unique_attr(attr, value.name)
        elif BOT_USER_CHOOSE_AN_OBJECT in message.intent_set:
            product = message.multiple_choices[0]
            conversation.data.add_nodes([product])

    def add_multiple_value_choices(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        values = self.product_multi_values(conversation)
        current_state.multiple_choices = [ValueNode(storage_id=conversation.storage_id,
                                                    prop_name=value, name=value) for value in values]

    @staticmethod
    def add_drop_product_choices(conversation: Conversation):
        """
        Get confirmed products from bill => add to conversation.current_state.multiple_choices
        :param conversation:
        :return:
        """
        current_state = conversation.current_state
        if current_state is None:
            return
        current_state.multiple_choices = [product for product in conversation.data.bill.products if product.confirmed]

    @staticmethod
    def add_infor_multiple_choices(attribute, object_of_infor):
        """
        Add infor value to multiple choices
        :param attribute: name of attribute that its values will be added to choices
        :param object_of_infor: infor choices is of USER or SHOP
        :return:
        """

        def _add_infor_multiple_choices(conversation: Conversation):
            current_state = conversation.current_state
            if current_state is None:
                return
            current_state.multiple_choices = [
                ValueNode(storage_id=conversation.storage_id, name=infor, index=attribute)
                for infor in getattr(conversation, object_of_infor).get_attr(attribute)]

        return _add_infor_multiple_choices

    def process_state(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None or current_state.multiple_choices is None or len(current_state.multiple_choices) <= 1:
            return
        message = current_state.message
        message.multiple_choices = current_state.multiple_choices
        self.multiple_choice_service(message)
        self.update_choice_data(conversation)

    def __call__(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None or current_state.multiple_choices is None or len(current_state.multiple_choices) <= 1:
            return
        message = conversation.pending_message
        if message is None:
            return
        message.multiple_choices = current_state.multiple_choices
        self.multiple_choice_service(message)
        self.update_choice_data(conversation)

    @staticmethod
    def check_user_has_pending_choices(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None or current_state.multiple_choices is None or len(current_state.multiple_choices) <= 1:
            return False
        return True

    @staticmethod
    def check_user_has_choice(conversation: Conversation):
        message = conversation.pending_message
        if message is not None:
            return BOT_USER_CHOOSE_AN_OBJECT in conversation.pending_message.intent_set or \
                   BOT_USER_CHOOSE_A_VALUE in conversation.pending_message.intent_set
        else:
            return False

    @staticmethod
    def check_has_user_pending_choices(conversation: Conversation):
        return conversation.has_user_pending_choices

    @staticmethod
    def drop_multiple_choices(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        current_state.multiple_choices = []

    @staticmethod
    def refresh_multiple_choices(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None or current_state.has_a_choice:
            return
        else:
            current_state.multiple_choices = []
