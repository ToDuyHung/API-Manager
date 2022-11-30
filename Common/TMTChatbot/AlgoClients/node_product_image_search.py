from typing import Dict, Tuple, List
from datetime import datetime

from TMTChatbot.AlgoClients.node_search_service import NodeSearchService
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Schema.objects.graph.graph_data import Node, Product, VariantProduct
from TMTChatbot.StateController.services.value_mapping import map_product_inventory
from TMTChatbot.Common.config.config import Config
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Common.common_keys import *


class NodeProductImageSearch(NodeSearchService):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(NodeProductImageSearch, self).__init__(config=config, storage=storage)
        self.api_url = f"{self.config.node_image_search_url}/process"

    def _post_process(self, data: BaseDataModel, conversation: Conversation = None) -> Tuple[List[Node], Dict]:
        nodes = []
        if data is None:
            return nodes, {}
        else:
            api_output: Dict = data.data
            if api_output and api_output[DISTANCE] != "None" and \
                    api_output[CHECK_INPUT_DATA] and api_output[LIST_RECOMMEND_ITEMS]:
                nodes = []
                _nodes = [Node.from_json(item, storage=self.storage) for item in api_output[LIST_RECOMMEND_ITEMS]]
                # TODO how to process variant product instead of parent product
                cache_nodes = {node.id: node for node in _nodes}
                for node in _nodes:
                    if isinstance(node, VariantProduct):
                        node = Product.from_json({
                            CLASS: Product.class_name(),
                            STORAGE_ID: node.storage_id,
                            OBJECT_ID: node.parent_id
                        }, storage=self.storage, nodes=cache_nodes)
                    nodes.append(node)
            return nodes, api_output

    def _pre_process(self, input_data: Conversation) -> BaseDataModel:
        data = {}
        if len(input_data.current_state.message.urls) > 0:
            data = {
                INPUT_TYPE: "url",
                STORAGE_ID: input_data.storage_id,
                IMAGE_URL: input_data.current_state.message.urls[0]
            }
        elif input_data.current_state.message.base64_img:
            data = {
                INPUT_TYPE: "base64",
                STORAGE_ID: input_data.storage_id,
                IMAGE_URL: input_data.current_state.message.base64_img
            }
        return BaseDataModel(data=data)

    def __call__(self, input_data: Conversation, key=None, postfix="", num_retry: int = None, call_prop: float = 0):
        if (len(input_data.current_state.message.urls) > 0 or input_data.current_state.message.base64_img) \
                and self.api_possible():
            data = self._pre_process(input_data)
            result: BaseDataModel = self.make_request(lambda: self._call_api(data))
            nodes, api_output = self._post_process(result, conversation=input_data)

            if api_output and api_output[DISTANCE] != "None" and \
                    api_output[CHECK_INPUT_DATA] and api_output[LIST_RECOMMEND_ITEMS]:
                if float(api_output[DISTANCE]) >= self.config.threshold_cloth_model:
                    input_data.current_state.update_intents([BOT_ITEM_IN_SHOP])
                else:
                    input_data.current_state.update_intents([BOT_ITEM_OUT_SHOP])
            if len(nodes) >= 1:
                if nodes[0].id in input_data.data.nodes:
                    input_data.current_state.update_intents([USER_MENTION_OLD_OBJECT])
                else:
                    input_data.current_state.update_intents([USER_MENTION_OBJECT])
                if len(nodes) > 1:
                    input_data.data.add_nodes(nodes[1:], datetime.now().timestamp())
                    input_data.data.add_nodes([nodes[0]], datetime.now().timestamp() + 1e-5)
                    input_data = self.check_inventory(input_data)
                elif len(nodes) == 1:
                    input_data.data.add_nodes([nodes[0]])
                    input_data = self.check_inventory(input_data)

            if result is None:
                self.api_alive = False
            else:
                self.api_alive = True
            return input_data

    @staticmethod
    def check_inventory(input_data: Conversation) -> Conversation:
        inventory = map_product_inventory(input_data)
        if inventory is None or (isinstance(inventory, list) and len(inventory) == 0):
            input_data.current_state.update_intents([BOT_ZERO_INVENTORY])
        else:
            input_data.current_state.update_intents([BOT_HAVE_INVENTORY])
        return input_data
