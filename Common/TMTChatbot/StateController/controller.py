import json
import logging

from TMTChatbot.StateController.base_state_processor import BaseStateProcessor
from TMTChatbot import (
    Conversation,
    Message
)
from TMTChatbot.StateController.config import ConversationConfig
from TMTChatbot.Common.utils.logging_utils import setup_logging

from TMTChatbot.StateController.services.information_extractor import BaseInformationExtractor
from TMTChatbot.Common.config.config import Config


class Controller:

    def __init__(self, config: Config = None, conversation_data: dict = None):

        setup_logging(logging_folder="logs", log_name="example.log")
        self._config = ConversationConfig(
            intent_url="http://172.29.13.24:20221", graph_qa_url="http://172.29.13.24:20224",
            ner_url="http://172.29.13.24:20220", node_search_url="http://172.29.13.24:20223",
            mongo_host="172.29.13.24", mongo_port=20253
        ) if config is None else config

        self.state_controller = BaseStateProcessor(self._config)
        self.conversation: Conversation = Conversation.from_json(
            conversation_data,
            storage=self.state_controller.storage
        )
        self.conversation_json = self.conversation.json
        self.curr_state = self.conversation.current_state

        self.information_extractor = BaseInformationExtractor(config=config)

    def add_pending_message(self, message: Message):
        self.conversation.add_pending_message(message=message)

    def drop_pending_message(self):
        self.conversation.drop_pending_message()

    @staticmethod
    def get_condition():
        with open("config/condition.json", "r", encoding="utf8") as f:
            condition = json.load(f)
            logging.info(f"Condition: {condition['Condition']}")

        return condition

    def get_state(self, message: str):
        service_ners = self.information_extractor.ner_service(Message(message=message))
        service_intents = self.information_extractor.intent_model(
            Message(message=message), add_has_message_intent=not False
        )
        intents = service_intents.intents
        condition = self.get_condition()
        ners = service_ners.entities
        if ners:
            logging.debug("+"*10 + " NER " + "+"*10)
            entities = set([entity.label for entity in ners])
            for s, ent in condition['Condition'].items():
                conditions = set(ent)
                ints = set(intent.tag for intent in intents)
                st = set(condition['State'][s][1])
                print("1111", ints, st, ints.intersection(st))
                print("2222", entities, conditions, entities.intersection(conditions))
                if ints.intersection(st) and entities.intersection(conditions):
                    # force = input("Input state: ")
                    print(f"+" * 20)
                    return condition['State'][s][0]
        else:
            logging.debug("+" * 10 + " INTENT " + "+" * 10)
            for key, state in condition['State'].items():
                print("-" * 10, intents[0].tag, state[1])
                if intents[0].tag in state[1] and key in condition['Condition']:
                    logging.debug(f"Working on {message} with intent: {condition['State'][key][0]}")
                    return condition['State'][key][0]

    def control_state(self, prev_state: bool = False, message: str = None):
        print(f"-----{self.state_name}")
        if prev_state:
            print(f"Current State: {self.state_name}")
            self.conversation = Conversation.from_json(self.conversation_json, storage=self.state_controller.storage)
            state = self.conversation.current_state
            state.add_message(
                Message(message=message, storage=self.state_controller.storage)
            )
        else:
            print(f"New State: {self.state_name}")
            self.conversation.new_state_with_message(
                Message(message=message, storage=self.state_controller.storage),
                state_action_config_id=self.state_name.lower()
            )
        self.conversation.save()
        self.conversation_json = self.conversation.json

    def execute_conversation(self):
        self.conversation = Conversation.from_json(self.conversation_json, storage=self.state_controller.storage)
        self.conversation: Conversation = self.state_controller.process(self.conversation, save=True)
        logging.info(self.conversation.current_state.response.message)
        self.conversation.save()

    def __call__(self):
        messages = self.conversation.pending_messages
        message = messages[-1].json["message"]
        self.state_name = self.get_state(message=message)
        print(message)
        print(self.state_name)

        name = self.conversation.current_state
        if name is not None:
            print(f"******State {name.state_action_config.name.split('_')[1]}")
            prev_state = self.state_name.lower() == name.state_action_config.name.split("_")[1]
        else:
            prev_state = False

        self.control_state(prev_state=prev_state, message=message)
        self.execute_conversation()


def main():
    conversation_data = {
        "_id": "3",
        "class": "Conversation",
        "storage_id": "test"
    }
    controller = Controller(conversation_data=conversation_data)
    while True:
        message = input("Please enter input: ")
        # messages = [
        #     # "hello",
        #     # "Mình cao 1m6 nặng 45kg thì mặc size gì shop",
        #     # "lấy cho mình nha",
        #     # "số đt mình là 19298829338",
        #     "0982457845",h
        # ]
        controller.add_pending_message(message=message)
        controller()
        controller.drop_pending_message()


if __name__ == "__main__":
    main()


