from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Common.default_intents import *
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.Schema.objects.conversation.conversation import Conversation


class ShopManager(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(ShopManager, self).__init__(config=config)
        self.storage = storage

    @staticmethod
    def check_shop_multi_value(is_global=False):
        def _check_shop_multi_value(conversation: Conversation):
            shop = conversation.data.shop
            attributes = shop.schema.attributes
            output = []
            for attr in attributes:
                attr_value = shop.get_attr(attr)
                if len(attr_value) > 1:
                    output.append(f"{BOT_BASE_SHOP_MULTI_INFO}_{attr}")
                elif len(attr_value) == 1:
                    output.append(f"{BOT_BASE_SHOP_HAS_ONE_INFO}_{attr}")
                else:
                    output.append(f"{BOT_BASE_SHOP_MISSING_INFO}_{attr}")
            if not is_global:
                conversation.current_state.update_intents(output)
            else:
                return output
        return _check_shop_multi_value

    @staticmethod
    def update_shop_infor_multiple_choices(conversation: Conversation):
        node = conversation.current_state.message.multiple_choices
        if node:
            node = node[0]
            conversation.shop.set_attr(node.id, node.name)
            conversation.current_state.message.drop_intents([f"{BOT_BASE_SHOP_MISSING_INFO}_{node.id}"])

    @staticmethod
    def forward_to_admin(conversation: Conversation):
        pass