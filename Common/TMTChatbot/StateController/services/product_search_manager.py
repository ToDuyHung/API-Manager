from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.AlgoClients.node_search_service import NodeSearchService
from TMTChatbot.AlgoClients.node_product_image_search import NodeProductImageSearch
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Product
from TMTChatbot.Common.default_intents import *


class ProductSearchManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(ProductSearchManager, self).__init__(config=config)
        self.storage = storage
        self.node_product_image_search = NodeProductImageSearch(config=config, storage=self.storage)
        self.node_search_service = NodeSearchService(config=config, storage=self.storage)

    @staticmethod
    def search_product_in_attachment(conversation: Conversation):
        if conversation.pending_message is not None:
            message = conversation.pending_message
            if len(message.attachments) > 0:
                nodes = [node for node in message.attachments.values() if isinstance(node, Product)]
                if len(nodes) == 1:
                    node = nodes[0]
                    if node.id in conversation.data.nodes:
                        conversation.pending_message.update_intents([USER_MENTION_OLD_OBJECT])
                    else:
                        conversation.pending_message.update_intents([USER_MENTION_OBJECT])
                elif len(nodes) > 1:
                    conversation.pending_message.update_intents([USER_MENTION_UNCLEAR_OBJECTS])
                nodes = conversation.data.add_nodes(nodes)
                if len(nodes) > 0:
                    return True
        return False

    def search_product_in_message(self, conversation: Conversation):
        # TODO Move intent in NodeSearchService here
        return self.node_search_service(conversation)

    @staticmethod
    def check_url(conversation: Conversation):
        pre_actions = []
        if conversation.current_action is not None:
            pre_actions = [pre_action.tag for pre_action in conversation.current_action.pre_actions.values()]
        if BOT_CHECK_USER_SEND_PAYMENT not in pre_actions and \
                (len(conversation.pending_message.urls) > 0 or conversation.pending_message.base64_img):
            return True
        else:
            return False


