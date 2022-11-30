from typing import List, Union

from TMTChatbot.Schema.objects.graph.graph_data import Bill
from TMTChatbot.Common.storage.mongo_client import MongoConnector, JoinCollMongoConnector
from TMTChatbot.Schema.objects.conversation.conversation import Conversation, Message, Response
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.StateController.services.information_extractor import BaseInformationExtractor
from TMTChatbot.StateController.base_state_processor import BaseStateProcessor
from TMTChatbot.StateController.services.bot_intent import BotIntent
from TMTChatbot.StateController.services.user_manager import UserManager


class BaseStateController(BaseServiceSingleton):
    def __init__(self, config: Config = None):
        super(BaseStateController, self).__init__(config=config)
        self.storage = None
        self.state_processor = None
        self.information_extractor = None
        self.bot_intent_extractor = None
        self.user_manager = None
        self.init()

    def init(self):
        if self.storage is None or \
                self.state_processor is None or \
                self.information_extractor is None or \
                self.bot_intent_extractor is None or \
                self.user_manager is None:
            raise NotImplementedError("Need Implementation for create storage, state_processor, "
                                      "information_extractor and bot_intent_extractor and user_manager")

    @staticmethod
    def next_state(conversation: Conversation):
        need_response_states = []
        current_action = conversation.current_action
        while not conversation.current_state.done:
            if conversation.current_action != current_action:
                conversation.current_action.refresh()
                need_response_states.append(conversation.current_state)
            conversation.next_state()
        return need_response_states

    def process(self, conversation: Conversation, join_response) -> Union[Response, List[Response]]:
        self.information_extractor.message_information_extraction(conversation)
        self.bot_intent_extractor.extract_global_intents(conversation)

        conversation.get_state_by_entry_point()
        conversation.current_state.add_message(message=conversation.pending_message)
        conversation.drop_pending_message()
        conversation = self.state_processor(conversation, join_response=join_response)
        response = conversation.current_state.response

        pre_responses = []
        current_state = conversation.current_state
        count = 3
        while conversation.current_state is not None and conversation.current_state.done and count > 0:
            conversation.next_state()
            count -= 1
            if conversation.current_state != current_state:
                if conversation.current_state.empty_message and conversation.current_state.empty_response:
                    conversation = self.state_processor.pass_response(conversation, join_response=join_response)
                else:
                    conversation = self.state_processor(conversation, join_response=join_response)
                pre_responses.append(conversation.current_state.response)
            else:
                break
            current_state = conversation.current_state

        if join_response:
            for pre_response in pre_responses:
                response.join(pre_response, delimiter=self.config.response_delimiter)
            return response
        else:
            return [response, *pre_responses]

    def refresh_conversation(self, message: Message):
        conversation = Conversation.from_user_shop_id(user_id=message.user_id, shop_id=message.shop_id,
                                                      storage=self.storage, storage_id=message.storage_id)
        conversation.user.drop_all_attributes()
        if conversation.data.bill is not None:
            conversation.data.bill.delete(force=True)
        if conversation.data.weather is not None:
            conversation.data.weather.delete(force=True)
        conversation.data.remove_all_nodes()
        conversation.data.init_bill()
        conversation.data.init_weather()
        while conversation.current_state is not None:
            conversation.drop_state()

        while conversation.pending_message is not None:
            conversation.drop_pending_message()

        conversation.script_config = None
        conversation.save(force=True)

    def __call__(self, message: Message, script_config, join_response) -> Union[Response, List[Response]]:
        if (message.message is None or message.message == "") and (message.urls is None or len(message.urls) == 0) and \
                (message.base64_img is None or len(message.base64_img) == 0):
            output = Response(message="", storage_id=message.storage_id, user_id=message.user_id,
                              shop_id=message.shop_id)
            if join_response:
                return output
            else:
                return [output]
        import time
        s = time.time()

        conversation = Conversation.from_user_shop_id(user_id=message.user_id, shop_id=message.shop_id,
                                                      storage=self.storage, storage_id=message.storage_id,
                                                      script_config=script_config)
        # PROCESS USER GENDER
        self.user_manager.update_user_gender_by_name(conversation)
        self.logger.debug(f"---LOAD conv {time.time() - s}")
        s = time.time()
        conversation.add_pending_message(message)
        conversation.save()

        if join_response:
            all_response = Response(message="", storage_id=message.storage_id, user_id=message.user_id,
                                    shop_id=message.shop_id)
            self.logger.debug(f"---save conv pending {time.time() - s}")
            s = time.time()
            while len(conversation.pending_messages) > 0:
                response = self.process(conversation, join_response=True)
                all_response.join(response, delimiter=self.config.response_delimiter)
                conversation.save()
                self.logger.debug(f"---processing {time.time() - s}")
                s = time.time()
            all_response.message = self.state_processor.post_process(all_response.message,
                                                                     delimiter=self.config.response_delimiter)
        else:
            self.logger.debug(f"---save conv pending {time.time() - s}")
            s = time.time()
            all_response = []
            while len(conversation.pending_messages) > 0:
                response = self.process(conversation, join_response=False)
                all_response += response
                conversation.save()
                self.logger.debug(f"---processing {time.time() - s}")
                s = time.time()
        if conversation.current_state.is_done_state:
            self.new_conversation(conversation)
        return all_response

    @staticmethod
    def new_conversation(conversation: Conversation):
        """
        Execute after each order done
        - refresh node data in conversation
        - drop pending_message in conversation if any
        - drop state in conversation if any ?
        - add bill.products -> user history_products??
        :param conversation:
        :return:
        """
        # TODO: add bill.confirmed_products -> user history_products??
        # if conversation.data.bill.confirmed:
        #     conversation.user.set_attr(USER_HISTORY_PRODUCTS, conversation.data.bill.confirmed_products)
        if conversation.data.weather is not None:
            conversation.data.weather.delete(force=True)
        conversation.data.remove_nodes([node for node in conversation.data.all_nodes \
                                        if node not in [conversation.user,
                                                        conversation.shop] and node.class_name() != Bill.class_name()])
        conversation.data.init_bill()
        conversation.data.init_weather()

        while conversation.current_state is not None:
            conversation.drop_state()
        while conversation.pending_message is not None:
            conversation.drop_pending_message()

        conversation.save(force=True)


class BaseMultiStorageStateController(BaseStateController):
    def __init__(self, config: Config = None):
        super(BaseMultiStorageStateController, self).__init__(config=config)

    def init(self):
        self.storage = MongoConnector(config=self.config)
        self.state_processor = BaseStateProcessor(config=self.config, storage=self.storage)
        self.information_extractor = BaseInformationExtractor(config=self.config, storage=self.storage)
        self.bot_intent_extractor = BotIntent(config=self.config, storage=self.storage)
        self.user_manager = UserManager(config=self.config, storage=self.storage)


class BaseSingleStorageStateController(BaseStateController):
    def __init__(self, config: Config = None):
        super(BaseSingleStorageStateController, self).__init__(config=config)

    def init(self):
        self.storage = JoinCollMongoConnector(config=self.config)
        self.state_processor = BaseStateProcessor(config=self.config, storage=self.storage)
        self.information_extractor = BaseInformationExtractor(config=self.config, storage=self.storage)
        self.bot_intent_extractor = BotIntent(config=self.config, storage=self.storage)
        self.user_manager = UserManager(config=self.config, storage=self.storage)


if __name__ == "__main__":
    from TMTChatbot.StateController.config import ConversationConfig

    _config = ConversationConfig(intent_url="http://172.29.13.24:20221", graph_qa_url="http://172.29.13.24:20224",
                                 ner_url="http://172.29.13.24:20220",
                                 doc_qa_url="http://172.29.13.24:20227", mongo_host="172.29.13.24",
                                 node_search_url="http://172.29.13.24:20223",
                                 mongo_port=20253)
    controller = BaseStateController(config=_config)
    _message = Message.from_json({
        "name": "Message_f3a7cbbe-dc76-5173-b265-7282bdcb234f",
        "message": "Xin chào",
        "created_time": 1660202038,
        "storage_id": "test",
        "hashed": "6807ae66a5b30f416f3ecf0da78e4acc",
        "_id": "f3a7cbbe-dc76-5173-b265-7282bdcb234f",
        "class": "Message",
        "user_id": "nguyenpq",
        "shop_id": "f853c5c9-b7a5-5220-82a1-1c1a94777e4e"
    }, storage=controller.storage)
    controller(message=_message)
