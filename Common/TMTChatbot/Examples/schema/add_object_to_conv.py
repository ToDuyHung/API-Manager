from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.storage.mongo_client import MongoConnector
from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Product

if __name__ == "__main__":
    from TMTChatbot.Common.utils import setup_logging
    from TMTChatbot.Common.config.config import Config

    _config = Config()
    storage = MongoConnector(_config)

    setup_logging(logging_folder="./logs", log_name="app.log")

    # ===================================================================================================
    # Add product to conversation

    new_conversation: Conversation = Conversation.from_json({
        OBJECT_ID: "1",
        CLASS: "Conversation"
    }, storage=storage)

    # print("=" * 20 + "BEFORE ADD" + "=" * 20)
    # print(new_conversation.data.nodes)
    # print(new_conversation.data.relations)
    # print(new_conversation.current_state.pretty_json)
    # print(new_conversation.current_state.changed)

    product: Product = Product.from_json({OBJECT_ID: "084dccb0-be0b-535d-ae96-472c72801b58", CLASS: "Product"},
                                         storage=storage)
    new_conversation.add_object(product)

    # print("=" * 20 + "AFTER ADD" + "=" * 20)
    # print(new_conversation.data.nodes)
    # print(new_conversation.data.relations)
    # print(new_conversation.current_state.pretty_json)
    # print(new_conversation.current_state.changed)
    new_conversation.save()

# print(new_conversation.memory.data.nodes)
# print(new_conversation.memory.data.relations)
# print(new_conversation.static_info)
# _json_string = json.dumps([state.json for state in new_conversation.memory.states], indent=4)
# print(_json_string)
# new_conversation.save()

# product.set_attr("colors", "red")
# product.save(force=True)
# print(product.relations)
