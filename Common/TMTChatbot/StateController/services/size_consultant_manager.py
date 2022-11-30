from TMTChatbot.Common.common_keys import PRODUCT_SIZE
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.AlgoClients.size_prediction_service import SizePredictionService
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Product, BillProduct


class SizeConsultantManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(SizeConsultantManager, self).__init__(config=config)
        self.size_prediction_service = SizePredictionService(config=config, storage=storage)
        self.storage = storage

    # @staticmethod
    # def get_size_attribute(product: Product):
    #     return f"size"  # _{product.parent_class}"

    @classmethod
    def check_user_size(cls, is_global: bool = False):
        def _check_user_size(conversation: Conversation):
            output = []
            user = conversation.user
            products = conversation.data.get_previous_node(node_class=Product.class_name())
            if len(products) == 0:
                output.append(f"{BOT_BASE_USER_MISSING_INFO}_{PRODUCT_SIZE}")
            else:
                product = products[-1]
                product_size_attr = product.get_user_attribute_with_product(PRODUCT_SIZE)
                values = user.get_attr(product_size_attr)
                if isinstance(values, list) and len(values) > 0:
                    output.append(f"{BOT_BASE_USER_HAS_ATTRIBUTE}_{product_size_attr}")
                else:
                    output.append(f"{BOT_BASE_USER_MISSING_INFO}_{product_size_attr}")
            if not is_global:
                conversation.current_state.update_intents(output)
            else:
                return output

        return _check_user_size

    def predict_size(self, conversation: Conversation):
        user = conversation.user
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            products = Product.defaults(storage_id=conversation.storage_id, storage=conversation.storage)
        else:
            products = products[-1:]

        for product in products:
            if any(not user.get_last_attr_value(attr) for attr in product.schema.user_required_attributes):
                continue
            size = self.size_prediction_service((user, product))
            if size is None:
                size = "L"
            product_size_attr = product.get_user_attribute_with_product(PRODUCT_SIZE)
            user.set_attr(product_size_attr, size)

    @staticmethod
    def update_user_size(conversation: Conversation):
        user = conversation.user
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            product = Product.defaults(storage_id=conversation.storage_id, storage=conversation.storage)[-1]
        else:
            product = products[0]

        product_size_attr = product.get_user_attribute_with_product(PRODUCT_SIZE)
        message = conversation.current_state.message
        size_ent = [ent for ent in message.entities if ent.label == 'size']
        if size_ent:
            user.set_attr(product_size_attr, size_ent[0].parsed_value)

    @staticmethod
    def check_mentioned_size_in_table(conversation: Conversation):
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            conversation.current_state.update_intents([BOT_MENTIONED_SIZE_NOT_IN_TABLE])
        else:
            message = conversation.current_state.message
            size_ent = [ent.parsed_value for ent in message.entities if ent.label == 'size']
            if size_ent:
                product: Product = products[-1]
                size_table = product.schema.size_table.size_table
                if size_ent[0] not in size_table.keys():
                    conversation.current_state.update_intents([BOT_MENTIONED_SIZE_NOT_IN_TABLE])

    @staticmethod
    def check_user_size_remain(conversation: Conversation):
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            return
        else:
            product = products[0]
        bill_product: BillProduct = conversation.data.bill.get_product(product)
        product_size_attr = bill_product.get_user_attribute_with_product(PRODUCT_SIZE)
        user_size = conversation.user.get_last_attr_value(product_size_attr)

        if user_size:
            if user_size in bill_product.get_attr(PRODUCT_SIZE):
                conversation.current_state.update_intents([USER_SIZE_AVAILABLE])
            else:
                conversation.current_state.update_intents([USER_SIZE_OUT_OF_STOCK])
