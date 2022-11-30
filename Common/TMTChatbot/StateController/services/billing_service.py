from datetime import datetime
import json

from functools import reduce

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.common_keys import *
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.AlgoClients.bill_image_service import BillImageService
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import BillProduct, Product, BankAccount, ValueNode, Bill
from TMTChatbot.Schema.common.product_types import PaymentStatus, BillStatus


class BillingManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(BillingManager, self).__init__(config=config)
        self.bill_image_service = BillImageService(config=config, storage=storage)

    @staticmethod
    def cancel_product(conversation: Conversation):
        """
        Turn current Product status into CANCELED
        :param conversation:
        :return:
        """
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            return
        else:
            product = products[0]
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill_product: BillProduct = BillProduct.from_product(product)
        bill_product = bill.get_product(bill_product)
        bill_product.cancel()

    @staticmethod
    def check_bill_product_to_cancel(conversation: Conversation):
        products = conversation.data.bill.confirmed_products
        if len(products) == 1:
            conversation.current_state.update_intents([USER_BILL_HAVE_ONE])
        else:
            conversation.current_state.update_intents([USER_BILL_HAVE_PRODUCTS])

    @staticmethod
    def add_care_product(conversation: Conversation):
        """
        Add current Product to bill => Auto care product if product is not confirmed
        :param conversation:
        :return:
        """
        if BOT_USER_CHOOSE_AN_OBJECT in conversation.current_state.intent_set:
            product = conversation.current_state.message.multiple_choices[0]
            conversation.data.add_nodes([product])
        else:
            products = conversation.data.get_previous_node(node_class=Product.class_name())
            if len(products) == 0:
                return
            else:
                product = products[0]
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill_product: BillProduct = BillProduct.from_product(product)
        bill_product = bill.add_product(bill_product)
        bill_product.care()

    @staticmethod
    def add_billing_product(conversation: Conversation):
        """
        Add current Product to bill => Auto confirm
        :param conversation:
        :return:
        """
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        products = [p for p in products if isinstance(p, Product)]
        if len(products) == 0:
            return
        else:
            product = products[0]
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill_product: BillProduct = BillProduct.from_product(product)
        bill_product = bill.add_product(bill_product)
        current_time = datetime.now().timestamp()
        bill_product.set_mentioned_time(current_time)
        if not bill_product.is_canceled:
            bill_product.confirm()

    @staticmethod
    def add_bill_payment_bank_account(conversation: Conversation):
        bank_accounts = conversation.data.get_previous_node(node_class=BankAccount.class_name())
        if len(bank_accounts) == 0:
            return
        else:
            bank_account = bank_accounts[0]
            bill = conversation.data.bill
            conversation.data.add_nodes([bill])
            bill.set_attr(BILL_BANK_ACCOUNT, json.dumps(bank_account.info_schema, indent=4, ensure_ascii=False))

    @staticmethod
    def add_payment_bank_account_recommendations(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        current_state.multiple_choices = conversation.shop.bank_accounts

    @staticmethod
    def process_bill(conversation: Conversation):
        if conversation.data.bill is None:
            conversation.data.init_bill()
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill.processing()

    @staticmethod
    def confirm_bill(conversation: Conversation):
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill.confirm()

    @staticmethod
    def cancel_bill(conversation: Conversation):
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill.cancel()

    @staticmethod
    def new_bill(conversation: Conversation):
        conversation.data.init_bill()

    @staticmethod
    def update_pending_payment(conversation: Conversation):
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill.payment_status = PaymentStatus.PENDING

    @staticmethod
    def update_done_payment(conversation: Conversation):
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill.payment = PaymentStatus.DONE

    @staticmethod
    def check_user_send_payment(conversation: Conversation):
        """
        Check if user send and image of bill with correct amount of money
        :param conversation:
        :return:
        """
        conversation.current_state.message.update_intents([BOT_USER_SEND_PAYMENT])

    @staticmethod
    def check_product_discount(conversation: Conversation):
        """
        If the product is unique, then check if there is any discount of this product
        :param conversation:
        :return:
        """
        products = conversation.data.get_previous_node()
        if len(products) == 0:
            return
        elif len(products) > 1:
            return
        else:
            product = products[0]
            for key in ["discount", "giảm_giá"]:
                discount = product.get_attr(key)
                if discount is not None and len(discount) > 0:
                    conversation.current_state.message.update_intents([BOT_PRODUCT_HAS_DISCOUNT])
                    return

    @staticmethod
    def check_bill_infor(conversation: Conversation):
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        if bill:
            for attr in bill.attributes:
                if attr in bill.missing_attributes:
                    conversation.current_state.update_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attr}"])
                else:
                    conversation.current_state.update_intents([f"{BILL_BASE_HAS_INFOR}_{attr}"])
                    # remove old intents with old attribute value before update new intent with new attribute value
                    for intent in conversation.current_state.message.intent_set:
                        if intent.startswith(f"{BILL_BASE_HAS_INFOR}_{attr}_"):
                            conversation.current_state.message.drop_intents([intent])
                    if bill.get_last_attr_value(attr):
                        conversation.current_state.update_intents(
                            [f"{BILL_BASE_HAS_INFOR}_{attr}_{bill.get_last_attr_value(attr)}"])
                    conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attr}"])

    @staticmethod
    def update_bill_info(attribute):
        def _update_bill_info(conversation: Conversation):
            bill = conversation.data.bill
            conversation.data.add_nodes([bill])
            user = conversation.data.user
            shop = conversation.data.shop
            all_shop_user_attributes = user.schema.json_attributes + shop.schema.json_attributes
            if attribute in bill.required_attributes and attribute in all_shop_user_attributes:
                if attribute in user.schema.json_attributes:
                    node_data = user.get_last_attr_value(attribute)
                else:
                    node_data = shop.get_last_attr_value(attribute)

                if node_data:
                    bill.set_attr(attribute, node_data)
                    conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])
            elif attribute == BILL_RECEIVE_SHOWROOM:
                node = conversation.current_state.message.multiple_choices
                if node:
                    node = node[0]
                    bill.set_attr(attribute, node.name)
                    conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])
            elif attribute == BILL_RECEIVE_TIME:
                message = conversation.current_state.message
                receive_time = [ent for ent in message.entities if
                                ent.parsed_value and any(label in ["DATE", "TIME", "Time"] for label in ent.labels)]
                receive_time.sort(key=lambda x: len(x.text), reverse=True)
                if receive_time:
                    receive_time = receive_time[0]
                    bill.set_attr(attribute, receive_time.parsed_value)
                    conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])
            elif attribute == BILL_PAYMENT:
                message = conversation.current_state.message
                entity_value = [ent for ent in message.entities if
                                ent.parsed_value and any(label in ["MONEY"] for label in ent.labels)]
                if entity_value:
                    entity_value = entity_value[0]
                    bill.set_attr(attribute, entity_value.parsed_value)
                    conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])

        return _update_bill_info

    @staticmethod
    def update_bill_infor_with_value(attribute, value):
        def _update_bill_infor_with_value(conversation: Conversation):
            bill = conversation.data.bill
            if bill:
                conversation.data.add_nodes([bill])
                bill.set_attr(attribute, value)
                conversation.current_state.message.drop_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])

        return _update_bill_infor_with_value

    @staticmethod
    def remove_bill_attribute(attribute):
        """
        set attribute value of bill to None
        :param attribute:
        :return:
        """

        def _remove_bill_attribute(conversation: Conversation):
            bill = conversation.data.bill
            if bill:
                conversation.data.add_nodes([bill])
                bill.drop_attr(attribute)
                conversation.current_state.update_intents([f"{BOT_BASE_BILL_MISSING_INFO}_{attribute}"])
                # remove old intents with old attribute value
                for intent in conversation.current_state.message.intent_set:
                    if intent.startswith(f"{BILL_BASE_HAS_INFOR}_{attribute}_"):
                        conversation.current_state.message.drop_intents([intent])

        return _remove_bill_attribute

    @staticmethod
    def update_bill_product_attr(attribute):
        def _update_bill_product_attr(conversation: Conversation):
            user = conversation.user
            products = conversation.data.get_previous_node()
            if len(products) == 0:
                return
            else:
                product = products[0]
            bill = conversation.data.bill
            conversation.data.add_nodes([bill])
            bill_product: BillProduct = bill.get_product(product)
            # TODO: attribute is product's attribute => maybe not user's attribute (ex: size attribute of user is `size_{Product.parent_class}`)
            user_attribute = product.get_user_attribute_with_product(attribute)
            attr_value = user.get_last_attr_value(user_attribute)
            if bill_product is not None and attr_value:
                bill_product.set_unique_attr(attribute, attr_value)

        return _update_bill_product_attr

    @staticmethod
    def check_user_size_remain(conversation: Conversation):
        user_size = conversation.user.get_last_attr_value(PRODUCT_SIZE)
        products = conversation.data.get_previous_node()
        if len(products) == 0:
            return
        else:
            product = products[0]
        bill = conversation.data.bill
        conversation.data.add_nodes([bill])
        bill_product: BillProduct = conversation.data.bill.get_product(product)
        if not user_size:
            conversation.current_state.update_intents([USER_SIZE_OUT_OF_STOCK])
        else:
            if user_size in bill_product.get_attr(PRODUCT_SIZE):
                conversation.current_state.update_intents([USER_SIZE_AVAILABLE])
            else:
                conversation.current_state.update_intents([USER_SIZE_OUT_OF_STOCK])

    @staticmethod
    def get_chosen_bill(conversation: Conversation):
        current_intents = conversation.current_state.intent_set
        if BOT_SINGLE_CONFIRMED_BILL in current_intents:
            confirmed_bills = conversation.data.confirmed_bills
            conversation.data.add_nodes(confirmed_bills)
        elif BOT_MULTIPLE_CONFIRMED_BILLS in current_intents:
            user_choices = conversation.current_state.message.multiple_choices
            if len(user_choices) == 1 and isinstance(user_choices[0], Bill):
                chosen_bill: Bill = conversation.data.nodes.get(user_choices[0].id)
                conversation.data.add_nodes([chosen_bill])

    @staticmethod
    def add_bills_to_check_order_status(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return

        # NOTE: add BOL Kode to alias of Bill Node
        confirmed_bills = list()
        for bill in conversation.data.bills:
            if bill.status == BillStatus.CONFIRMED:
                confirmed_bills.append(bill)
        conversation.current_state.multiple_choices = confirmed_bills

    @staticmethod
    def drop_bills_after_check_order_status(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        current_state.multiple_choices = list()

    @staticmethod
    def check_number_of_processing_bills(conversation: Conversation):
        count = 0
        for bill in conversation.data.bills:
            if bill.status == BillStatus.PROCESSING:
                count += 1
        if count == 0:
            conversation.current_state.update_intents([BOT_USER_NO_PROCESSING_BILL])



