from typing import List
from datetime import datetime

from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Product
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton


class RecommendationManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(RecommendationManager, self).__init__(config=config)
        self.storage = storage

    def recommend_products(self, conversation: Conversation) -> List[Product]:
        shop = conversation.shop
        products = conversation.data.get_previous_node(mentioned_time_range=datetime.now().timestamp() - 5 * 60,
                                                       node_class=Product.class_name(),
                                                       return_latest=False, k=self.config.num_recommendation)
        if len(products) < self.config.num_recommendation:
            new_products = shop.get_random_product(k=self.config.num_recommendation - len(products))
            products += new_products
        return products

    def add_product_recommendations(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return []
        if not current_state.has_user_pending_choices and not current_state.has_a_choice:
            products = self.recommend_products(conversation)
            conversation.data.add_nodes(products)
            return products
        else:
            return []

    def add_product_multiple_choices(self, conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        products = conversation.data.get_previous_node(node_class=Product.class_name())
        if len(products) == 0:
            products = self.add_product_recommendations(conversation)
        current_state.multiple_choices = [product for product in products]

    @staticmethod
    def drop_product_multiple_choices(conversation: Conversation):
        current_state = conversation.current_state
        if current_state is None:
            return
        current_state.multiple_choices = []
