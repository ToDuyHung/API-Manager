import re
import json
import datetime

from typing import List, Type

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.common_phrases import DEFAULT_QUESTION_WORD
from TMTChatbot.Common.default_sentences import DEFAULT_NONE_ANSWER
from TMTChatbot.Schema.common.product_types import BillStatus
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.Schema.objects.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import BillProduct, Product, BankAccount, Bill
from TMTChatbot.AlgoClients.graph_qa_service import GraphQAService
from TMTChatbot.AlgoClients.weather_service import WeatherService
from TMTChatbot.AlgoClients.bill_generation_service import Json2ImageService
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.StateController.services.size_consultant_manager import SizeConsultantManager
from TMTChatbot.Common.common_key_mapping import KEY_MAPPING


def map_bill_general_info(conversation: Conversation, config: Config, key=None, join_response=True):
    _, attr = key.split("@")
    # bill = conversation.data.bill
    bill = conversation.data.get_previous_node(node_class=Bill.class_name())[-1]
    values = bill.get_attr(attr)
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = values[-1]
    elif hasattr(bill, attr):
        value = getattr(bill, attr)
    else:
        value = None
    if value is None or value == "":
        value = DEFAULT_NONE_ANSWER
    return value, []


def map_bill_info(conversation: Conversation, config: Config, key=None, join_response=True):
    if join_response:
        bill_generation_service = Json2ImageService(config=config, storage=conversation.storage)
        bill_info = conversation.data.bill.info_schema
        bill_url = bill_generation_service(bill_info)
        return f"* image {bill_url} *", [conversation.data.bill]
    else:
        return "", [conversation.data.bill]


def map_bill_drop_product(conversation: Conversation, config: Config, key=None, join_response=True):
    confirmed_products = [product for product in conversation.data.bill.products if product.confirmed]
    if not confirmed_products:
        return "", []
    last_product = confirmed_products[-1]
    conversation.data.add_nodes([last_product])
    return last_product.name, []


def map_bill_products_number(conversation: Conversation, config: Config, key=None, join_response=True):
    return len([product for product in conversation.data.bill.products if product.confirmed]), []


def map_bill_number(conversation: Conversation, config: Config, key=None, join_response=True):
    return len(conversation.data.confirmed_bills), []


def map_bill_remain_payment(conversation: Conversation, config: Config, key=None, join_response=True):
    bill = conversation.data.bill
    if bill:
        bill_payment = bill.get_last_attr_value(BILL_PAYMENT)
        bill_payment = int(bill_payment) if bill_payment else 0
        return (max(0, bill.price - bill_payment) if bill_payment else bill.price), []
    else:
        return "", []


def map_bill_delivery_status(conversation: Conversation, config: Config, key=None, join_response=True):
    return "đã đến kho trung chuyển", []


def map_bill_payment(conversation: Conversation, config: Config, key=None, join_response=True):
    bill = conversation.data.bill
    payment = 0
    if bill:
        payment = bill.get_last_attr_value(BILL_PAYMENT)
        payment = int(payment) if payment else 0
    return str(payment) + " VNĐ", []


def map_bill_payment_bank_account(conversation: Conversation, config: Config, key=None, join_response=True):
    bill = conversation.data.bill
    bank_account = bill.get_last_attr_value(BILL_BANK_ACCOUNT)
    if not bank_account:
        return "", []
    return bank_account, []


def map_bill_receiving_time(conversation: Conversation, config: Config, key=None, join_response=True):
    bill = conversation.data.bill
    if bill:
        receiving_time = bill.get_last_attr_value(BILL_RECEIVE_TIME)
        return receiving_time, []
    else:
        return "", []


def map_bill_receiving_showroom(conversation: Conversation, config: Config, key=None, join_response=True):
    bill = conversation.data.bill
    if bill:
        receiving_showroom = bill.get_last_attr_value(BILL_RECEIVE_SHOWROOM)
        return receiving_showroom, []
    else:
        return "", []


def map_user_size_shirt(conversation: Conversation, config: Config, key=None, join_response=True):
    return "L", []


def map_user_size_jean(conversation: Conversation, config: Config, key=None, join_response=True):
    return "L", []


def map_user_size(conversation: Conversation, config: Config, key=None, join_response=True):
    """
    :return: return 'áo size L và quần size M'"""
    user = conversation.user
    products = conversation.data.get_previous_node(node_class=Product.class_name())
    if len(products) == 0:
        products = Product.defaults(storage=conversation.storage, storage_id=conversation.storage_id)
    size_attrs = set([(product.parent_class, product.get_user_attribute_with_product(PRODUCT_SIZE))
                      for product in products])
    size_attrs = [(parent_class, user.get_last_attr_value(size_attr)) for parent_class, size_attr in size_attrs]
    return " và ".join([f"{parent_class} size {size}" for parent_class, size in size_attrs]), []


def map_user_info(conversation: Conversation, config: Config, key=None, join_response=True):
    _, attr = key.split("@")
    user = conversation.user
    values = user.get_attr(attr)
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = values[-1]
    else:
        value = None
    return value, []


def map_user_last_phone_numbers(conversation: Conversation, config: Config, key=None, join_response=True):
    user = conversation.data.user
    phone_numbers = user.get_attr(BILL_PHONE_NUMBER)
    return " và ".join([phone for phone in phone_numbers]), []


def map_user_last_addresses(conversation: Conversation, config: Config, key=None, join_response=True):
    user = conversation.data.user
    addresses = user.get_attr(BILL_ADDRESS)
    return " và ".join([phone for phone in addresses]), []


def map_bot_gender(conversation: Conversation, config: Config, key=None, join_response=True):
    user = conversation.user
    values = user.get_attr("gender")
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = values[-1]
    else:
        value = None
    return value, []


def map_shop_info(conversation: Conversation, config: Config, key=None, join_response=True):
    _, attr = key.split("@")
    shop = conversation.shop
    if attr == "name" and shop.name is not None:
        values = [shop.name]
    else:
        values = shop.get_attr(attr)
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = values[-1]
    else:
        value = None
    return value, []


def map_shop_showroom(conversation: Conversation, config: Config, key=None, join_response=True):
    shop = conversation.shop
    values = shop.get_attr("showroom")
    return "* ".join(values), []


def map_product_info(conversation: Conversation, config: Config, key=None, join_response=True):
    _, attr = key.split("@")
    products = conversation.data.get_previous_node(node_class=Product.class_name())
    if len(products) == 0:
        return f"<ERROR PRODUCT {attr}>", []
    else:
        product = products[0]
    if attr == "name":
        values = [product.name]
    else:
        values = product.get_attr(attr)
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = values[-1]
    elif hasattr(product, attr):
        value = getattr(product, attr)
    else:
        value = None

    if value is None:
        # TODO how to response unknown questions ????
        graph_qa_service = GraphQAService(config=config, storage=conversation.storage)
        value = graph_qa_service.custom_question(conversation,
                                                 question=f"{KEY_MAPPING.get(attr.lower())} "
                                                          f"{DEFAULT_QUESTION_WORD}")
    if value is None or value == "":
        value = DEFAULT_NONE_ANSWER
    return value, []


def map_product_image_url(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.get_previous_node()
    if len(products) == 0:
        return f"<ERROR PRODUCT> image_url", []
    else:
        product = products[0]
    values = product.image_urls
    if values is not None and isinstance(values, list) and len(values) > 0:
        value = f"image {values[-1]}"
    else:
        value = None
    if join_response:
        return value, []
    else:
        return "", [product]


def map_product_size_infor(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.get_previous_node()
    if len(products) == 0:
        return "", []
    else:
        product = products[-1]

    size_in_message = [ent.parsed_value for ent in conversation.current_state.message.entities if
                       ent.label == PRODUCT_SIZE]
    if size_in_message:
        size_table = product.schema.size_table.size_table
        size_table_of_size = size_table.get(size_in_message[0], {})
        if size_table_of_size:
            size_table_of_size = size_table_of_size.json_infor()
        return json.dumps(size_table_of_size, ensure_ascii=False), []
    return f"ERROR SIZE <{[ent.parsed_value for ent in conversation.current_state.message.entities]}>", []

def map_product_size(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.get_previous_node()
    if len(products) == 0:
        return "", []
    else:
        product = products[-1]

    return ", ".join(product.get_attr(PRODUCT_SIZE)), []

def map_product_inventory(conversation: Conversation, config: Config = None, key=None):
    return True


def map_product_general_info(conversation: Conversation, config: Config, key=None, join_response=True):
    # graph_qa_service = GraphQAService(config=config)
    # product_info = graph_qa_service(conversation)
    # if product_info is None or product_info == "":
    #     product_info = DEFAULT_NONE_ANSWER
    # return product_info
    return conversation.current_state.message.answer_infor, []


def map_question_answer(conversation: Conversation, config: Config, key=None, join_response=True):
    return conversation.current_state.message.answer_infor, []


def map_product_recommendation(conversation: Conversation, config: Config, key=None, join_response=True):
    if conversation.current_state.has_user_pending_choices:
        products = conversation.current_state.multiple_choices
    else:
        products = conversation.data.get_previous_node(node_class=Product.class_name(), return_latest=False,
                                                       k=config.num_recommendation)
    if join_response:
        return " * ".join([product.image_description for product in products]), products
    else:
        return "", products


def map_drop_product_recommendation(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.bill.products
    return " và ".join([product.name for product in products if product.confirmed]), []


def map_product_multi_values_attr(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.get_previous_node(node_class=Product.class_name())
    if len(products) == 0:
        return None, []
    else:
        product = products[0]
    bill_product: BillProduct = conversation.data.bill.get_product(product)
    if bill_product is not None:
        attr = bill_product.multiple_value_attribute
    else:
        attr = None
    if attr is not None:
        return attr, []
    return "<ERROR attr>", []


def map_product_multi_values(conversation: Conversation, config: Config, key=None, join_response=True):
    products = conversation.data.get_previous_node(node_class=Product.class_name())
    if len(products) == 0:
        return None, []
    else:
        product = products[0]
    bill_product: BillProduct = conversation.data.bill.get_product(product)
    if bill_product is not None:
        attr = bill_product.multiple_value_attribute
        if attr is not None:
            values = bill_product.get_attr(attr)
            return ", ".join(values), []
    return "<ERROR>", []


def map_unclear_products(conversation: Conversation, config: Config, key=None, join_response=True):
    k = 3
    products = conversation.data.get_previous_node(node_class=Product.class_name())[:k]
    if join_response:
        return "* ".join([product.image_description for product in products]), products
    else:
        return "", products


def map_weather_infor(conversation: Conversation, config: Config, key=None, join_response=True):
    weather_service = WeatherService(config=config, storage=conversation.storage)
    weather_infor = weather_service(input_data=conversation)
    _, attr = key.split("@")
    if attr == DATE:
        return ", ".join([weather.date for weather in weather_infor]), []
    elif attr == LOCATION:
        return ", ".join([weather.location for weather in weather_infor]), []
    else:
        descriptions = {f"{weather.location} ngày {weather.date}": {attr: ",".join(value)
                                                                    for attr, value in weather.json_attributes.items()}
                        for weather in weather_infor}
        return json.dumps(descriptions, indent=4, ensure_ascii=False), []


def map_chosen_bank_account(conversation: Conversation, config: Config, key=None, join_response=True):
    bank_accounts: List[BankAccount] = conversation.data.get_previous_node(node_class=BankAccount.class_name())
    if len(bank_accounts) == 0:
        return "", []
    descriptions = bank_accounts[0].info_schema
    return json.dumps(descriptions, indent=4, ensure_ascii=False), []


def map_recommend_full_payment_methods(conversation: Conversation, config: Config, key=None, join_response=True):
    json2image_service = Json2ImageService(config=config, storage=conversation.storage)
    bank_accounts = conversation.shop.bank_accounts
    url = json2image_service([bank_account.info_schema for bank_account in bank_accounts])
    return f"* image {url} *", []


def map_bol_codes(conversation: Conversation, config: Config, key=None, join_response=True):
    bill_infor_strings = []

    for bill in conversation.data.bills:
        if bill.status == BillStatus.CONFIRMED:
            bill_string = f"Mã vận đơn: {bill.code} - " \
                          f"Ngày đặt đơn {datetime.date.fromtimestamp(bill.confirmed_time).strftime('%d/%m/%Y')}"
            bill_infor_strings.append(bill_string)

    return '*'.join(bill_infor_strings), []


class ValueMapping(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(ValueMapping, self).__init__(config=config)
        self.storage = storage
        self.mapping_funcs = {
            "Bot@gender": map_bot_gender,
            "Bill@*": map_bill_general_info,
            "Bill@info": map_bill_info,
            "Bill@number": map_bill_number,
            # "Bill@remain_payment": map_bill_remain_payment,
            "Bill@delivery_status": map_bill_delivery_status,
            # "Bill@payment": map_bill_payment,
            "Bill@payment_bank_account": map_bill_payment_bank_account,
            "Bill@drop_product": map_bill_drop_product,
            "Bill@product_number": map_bill_products_number,
            "Bill@receiving_time": map_bill_receiving_time,
            "Bill@receiving_showroom": map_bill_receiving_showroom,
            "User@size": map_user_size,
            "User@size_shirt": map_user_size_shirt,
            "User@size_jean": map_user_size_jean,
            "User@last_addresses": map_user_last_addresses,
            "User@last_phone_numbers": map_user_last_phone_numbers,
            "User@bill_of_landing_codes": map_bol_codes,
            "User@*": map_user_info,
            "Product@info": map_product_general_info,
            "Product@inventory": map_product_inventory,
            "Product@*": map_product_info,
            "Product@recommendation": map_product_recommendation,
            "Product@recommend_drop_products": map_drop_product_recommendation,
            "Product@current_unclear": map_unclear_products,
            "Product@milti_values_attr": map_product_multi_values_attr,
            "Product@multi_values": map_product_multi_values,
            "Product@image_url": map_product_image_url,
            "Product@size_infor": map_product_size_infor,
            "Product@size": map_product_size,
            "Shop@*": map_shop_info,
            "Shop@showroom": map_shop_showroom,
            "Weather@info": map_weather_infor,
            "Weather@*": map_weather_infor,
            "Shop@chosen_bank_account": map_chosen_bank_account,
            "Shop@recommend_full_payment_methods": map_recommend_full_payment_methods,
            "Question@answer": map_question_answer
        }

    def add_mapping_func(self, key, func):
        self.mapping_funcs[key] = func

    @staticmethod
    def map_product_info(conversation: Conversation, config: Config):
        graph_qa_service = GraphQAService(config=config, storage=conversation.storage)
        product_info = graph_qa_service(conversation)
        return product_info

    @staticmethod
    def get_mapping_key(message: str):
        output = list(set(re.findall(r'(?<=\{)(\S+)(?=\})', message)))
        if "Bill@info" in output:
            output.remove("Bill@info")
            output = ["Bill@info", *output]
        return set(output)

    def get_mapping_func(self, key):
        mapping_func = self.mapping_funcs.get(key)
        if mapping_func is None:
            key_subject, _ = key.split("@")
            for mapping_func_name, mapping_func in self.mapping_funcs.items():
                subject, attr = mapping_func_name.split("@")
                if subject == key_subject and attr == "*":
                    return mapping_func
        else:
            return mapping_func

    def get_mapping_value(self, key, message: str, conversation: Conversation, config: Config, join_response):
        mapping_func = self.get_mapping_func(key)
        attachments = []
        if mapping_func is not None:
            mapping_info, mapped_key = conversation.current_state \
                .state_action_config.get_info_mapping(key)
            if mapping_info is not None:
                mapping_result = mapping_func(conversation, config, key=key, join_response=join_response)
                if len(mapping_result) != 2:
                    print()
                mapped_value, attachments = mapping_result
                mapped_template = mapping_info.get_mapping_template(key=key, mapped_key=mapped_key,
                                                                    mapped_value=mapped_value)
                mapped_value = mapped_template.format(**{key: mapped_value})
                if mapped_value is not None:
                    message = message.replace("{" + key + "}", mapped_value)
            return message, attachments
        else:
            return message, attachments

    def __call__(self, message: str, conversation: Conversation, join_response):
        count = 0
        all_attachments = []
        while count < 5:
            count += 1
            keys = self.get_mapping_key(message)
            if len(keys) == 0:
                break
            for key in keys:
                message, attachments = self.get_mapping_value(key, message, conversation, self.config, join_response)
                all_attachments += attachments
        return message, all_attachments
