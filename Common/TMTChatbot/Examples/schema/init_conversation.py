from TMTChatbot.Schema.objects.conversation.conversation import Conversation
from TMTChatbot.Schema.objects.graph.graph_data import Shop, User, Product
from TMTChatbot.Common.storage.mongo_client import MongoConnector


if __name__ == "__main__":
    import json
    from TMTChatbot.Common.utils import setup_logging
    from TMTChatbot.Common.config.config import Config

    _config = Config()
    storage = MongoConnector(_config)

    setup_logging(logging_folder="./logs", log_name="app.log")
    _shop = Shop(index="1", name="SHOP abc", aliases=["ABC"], storage=storage)
    shirt = Product(index="p_0", name="áo sơ mi", aliases=["sơ mi"], parent_class="Shirt", storage=storage)
    shirt.set_attr("colors", "red")
    jean = Product(index="p_1", name="quần jean", aliases=["jean", "quần bò"], parent_class="Jean",
                   storage=storage)
    hat = Product(index="p_2", name="mủ", aliases=["mủ lưỡi trai"], parent_class="Hat", storage=storage)
    _user = User(index="0", name="User XYZ", aliases=["xyz"], storage=storage)
    _shop.create_relation(shirt, "own")
    _shop.create_relation(jean, "own")
    _shop.create_relation(hat, "own")
    conversation = Conversation("1", shop=_shop, user=_user, storage=storage)
    # print(conversation.data.nodes)
    conversation.save(force=True)
    json_data = conversation.json
    json_string = json.dumps(json_data, indent=4)
    # print(json_string)
    new_conversation: Conversation = Conversation.from_json(json_data, storage=storage)
    json_data = new_conversation.json
    _json_string = json.dumps(json_data, indent=4)
    # print(_json_string)
    # print(json_string == _json_string)
    new_conversation.save(force=True)
    # print(new_conversation.data.nodes)
