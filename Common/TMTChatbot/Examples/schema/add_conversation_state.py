from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.storage.mongo_client import MongoConnector
from TMTChatbot.Schema.objects.conversation.conversation import Conversation, Message, Response

if __name__ == "__main__":
    import json
    from TMTChatbot.Common.utils import setup_logging
    from TMTChatbot.Common.config.config import Config

    _config = Config()
    storage = MongoConnector(_config)

    setup_logging(logging_folder="./logs", log_name="app.log")

    # Load conversation from conversation data => Auto fill missing values using database connection
    # From user static info and shop static info
    new_conversation: Conversation = Conversation.from_json({
        CONV_USER: {
            OBJECT_ID: "c682de29-74d1-5306-9450-4bd74915479e",
            CLASS: "User"
        },
        CONV_SHOP: {
            OBJECT_ID: "f0c513df-9be8-5dd6-bcab-c68ef9e88e10",
            CLASS: "Shop"
        },
        CLASS: "Conversation",
        OBJECT_ID: "1"
    }, storage=storage)
    json_data = new_conversation.json
    _json_string = json.dumps(json_data, indent=4)
    print(_json_string)
    print(new_conversation.data.nodes)
    print(new_conversation.data.relations)
    new_conversation.save()

    # --------------------------------------------------------------------------------------------------
    # From ConversationId and Conversation Class

    # new_conversation: Conversation = Conversation.from_json({
    #     OBJECT_ID: "1",
    #     CLASS: "Conversation"
    # }, storage=storage)
    #
    # # json_data = new_conversation.json
    # # _json_string = json.dumps(json_data, indent=4)
    # # print(_json_string)
    # print(new_conversation.memory.data.nodes)
    # print(new_conversation.memory.data.relations)
    # new_conversation.save()
    # del new_conversation

    # ===================================================================================================
    # Add State and Message Example
    # All message will be saved in history key in database

    new_conversation: Conversation = Conversation.from_json({
        OBJECT_ID: "1",
        CLASS: "Conversation"
    }, storage=storage)

    # # Add new state from new message
    new_conversation.new_state_with_message(
        message=Message(message="Xin chào. Shop có các sản phẩm nào vậy?", message_id="0", storage=storage))
    # Add response for current message
    new_conversation.add_response(
        response=Response(message="Shop nghỉ bán rồi ạ", message_id="1", storage=storage))

    _json_string = json.dumps(new_conversation.json, indent=4)
    print(_json_string)
    current_state = new_conversation.current_state
    _json_string = json.dumps([state.json for state in new_conversation.states], indent=4)
    print(_json_string)
    print(current_state.changed)
    new_conversation.save()
