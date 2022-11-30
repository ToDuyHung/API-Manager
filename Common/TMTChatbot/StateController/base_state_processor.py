from typing import Union
from TMTChatbot.Common.storage.base_storage import BaseStorage
from TMTChatbot.Schema.objects.common.data_model import BaseDataModel
from TMTChatbot.ServiceWrapper.services.base_service import BaseServiceSingleton
from TMTChatbot.Schema.objects.conversation import Conversation, Response
from TMTChatbot.Schema.objects.conversation.state_action_config import ActionExpectation, ActionConfig
from TMTChatbot.StateController.config.config import Config
from TMTChatbot.StateController.services.value_mapping import ValueMapping
from TMTChatbot.StateController.services.action_manager import ActionManager


class BaseStateProcessor(BaseServiceSingleton):
    def __init__(self, storage: BaseStorage, config: Config = None):
        super(BaseStateProcessor, self).__init__(config=config)
        self.action_manager = ActionManager(config=config, storage=storage)
        self.value_mapper = ValueMapping(config=config, storage=storage)
        self.storage = storage

    def next_action(self, conversation: Conversation):
        """
        Step to next action base on current system conditions.
        Before jumping to next action, some system actions can be called.
        :param conversation:
        :return:
        """
        need_response_actions = []
        current_action = conversation.current_action
        count = 0
        while conversation.current_action.done and not conversation.current_state.done:
            count += 1
            # call tasks for the most appropriate branch
            self.action_manager.make_current_action(conversation)
            is_new_action = conversation.next_action()

            if conversation.current_action != current_action:
                need_response_actions.append(conversation.current_action)

            if is_new_action:
                conversation.current_action.refresh()
                conversation.current_state.message.drop_user_intents()
                self.action_manager.make_pre_actions(conversation=conversation, mapping_info_only=True)
                self.action_manager.map_bot_expectation(conversation=conversation)
                self.action_manager.make_post_actions(conversation=conversation)
            else:
                break

            if count >= 3:
                break
        return need_response_actions

    @staticmethod
    def make_response_sent(input_data: Union[Conversation, ActionConfig]) -> str:
        response = ""
        if isinstance(input_data, Conversation):
            current_state = input_data.current_state
            current_action = current_state.current_action
        else:
            current_action = input_data
        current_branch: ActionExpectation = current_action.current_branch
        if current_branch is not None:
            response = current_branch.get_response()
        return response

    @staticmethod
    def make_request_sent(conversation: Conversation) -> str:
        request = ""
        current_action = conversation.current_action
        if current_action is not None:
            request = current_action.get_request()
        return request

    @staticmethod
    def post_process(message: str, delimiter: str = "*"):
        message = message.replace("None", " ")
        while "  " in message or "* *" in message:
            message = message.replace("  ", " ")
            message = message.replace("* *", "*")
        message = message.strip()
        if len(message) > 0 and message[0] == "*":
            message = message[1:]
        if len(message) > 0 and message[-1] == "*":
            message = message[:-1]
        message = message.replace("*", delimiter)
        sentences = [item.strip() for item in message.split(delimiter) if len(item.strip()) > 0]
        sentences = [((item[0].upper() + item[1:]).replace("_", " ") if "image" not in item else item[0] + item[1:])
                     for item in sentences if len(item.strip()) > 0]
        message = delimiter.join(sentences)
        return message

    def __call__(self, conversation: Conversation, join_response: bool) -> Conversation:
        self.action_manager.make_pre_actions(conversation=conversation)
        self.action_manager.map_bot_expectation(conversation=conversation)

        # CHECK ENTRY POINT and CHOOSE ACTION
        is_new_action = conversation.current_state.get_action_by_entry_point()
        if is_new_action:
            self.action_manager.make_pre_actions(conversation=conversation, is_new_action=is_new_action)
            self.action_manager.map_bot_expectation(conversation=conversation)

        response = self.make_response_sent(conversation)
        need_response_actions = self.next_action(conversation)
        extra_responses = [self.make_response_sent(item) for item in need_response_actions]
        extra_responses = " * ".join(extra_responses)

        # START CURRENT ACTION
        request = self.make_request_sent(conversation)
        response = f"{response} * {extra_responses} * {request}"
        for pending_response in conversation.pending_responses:
            response = f"{pending_response.message} * {response}"
        response, attachments = self.value_mapper(response, conversation, join_response=join_response)
        response = self.post_process(response)
        response = Response(message=response, user_id=conversation.user.id, shop_id=conversation.shop.id)
        response.add_attachments(attachments)
        conversation.add_response(response)

        # Post actions
        self.action_manager.make_post_actions(conversation)
        return conversation

    def pass_response(self, conversation: Conversation, join_response) -> Conversation:
        # DO pre-answer tasks
        self.action_manager.default_pre_actions(conversation, is_new_action=False, mapping_info_only=True)

        response = self.make_response_sent(conversation)
        need_response_actions = self.next_action(conversation)
        extra_responses = [self.make_response_sent(item) for item in need_response_actions]
        extra_responses = " * ".join(extra_responses)
        request = self.make_request_sent(conversation)
        response = f"{response} * {extra_responses} * {request}"

        response, attachments = self.value_mapper(response, conversation, join_response=join_response)
        response = self.post_process(response)
        response = Response(message=response, user_id=conversation.user.id, shop_id=conversation.shop.id)
        response.add_attachments(attachments)
        conversation.add_response(response)
        return conversation

    def process_raw(self, input_data: BaseDataModel, save=True, join_response=True) -> BaseDataModel:
        conversation = Conversation.from_json(input_data.data, storage=self.storage)
        conversation: Conversation = self.process(conversation, save=save, join_response=join_response)
        input_data.data = conversation.all_data
        return input_data

    def process(self, conversation: Conversation, save=False, join_response=True) -> Conversation:
        conversation: Conversation = self(conversation, join_response=join_response)
        if save:
            conversation.save()
        return conversation
