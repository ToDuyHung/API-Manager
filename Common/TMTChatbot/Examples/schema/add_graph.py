from TMTChatbot.Schema.objects.graph.graph_data import Shop, User, Product
from TMTChatbot.Schema.objects.graph.graph import SubGraph
from TMTChatbot.Common.storage.mongo_client import MongoConnector


if __name__ == "__main__":
    from TMTChatbot.Common.utils import setup_logging
    from TMTChatbot.Common.config.config import Config

    _config = Config()
    storage = MongoConnector(_config)

    setup_logging(logging_folder="./logs", log_name="app.log")
    _shop = Shop(index="f0c513df-9be8-5dd6-bcab-c68ef9e88e10", name="SHOP abc", aliases=["ABC"], storage=storage)
    shirt = Product(name="áo sơ mi", aliases=["sơ mi"], parent_class="Shirt", storage=storage)
    shirt.set_attr("colors", "red")
    jean = Product(name="quần jean", aliases=["jean", "quần bò"], parent_class="Jean",
                   storage=storage)
    hat = Product(name="mủ", aliases=["mủ lưỡi trai"], parent_class="Hat", storage=storage)
    _user = User(name="User XYZ", aliases=["xyz"], storage=storage)
    _shop.create_relation(shirt, "own")
    _shop.create_relation(jean, "own")
    _shop.create_relation(hat, "own")

    graph = SubGraph(nodes=[_shop, _user, shirt, hat, jean], shop=_shop, user=_user, storage=storage)

    # Only force = True can save data graph
    graph.save(force=True)
    # force = False will not make change to database

