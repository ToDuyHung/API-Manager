import sys
from abc import ABC
from typing import List, Set, Union
from datetime import datetime
import re

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Schema.objects.common.nlp_tags import Intent, NerTag, DependencyTag
from TMTChatbot.Schema.objects.graph.graph_data import Node, Relation, Shop, User
from TMTChatbot.Schema.objects.graph.graph import SubGraph
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Schema.objects.conversation.state_action_config import (
    ActionConfig,
    StateActionConfig,
    ActionExpectation,
    ScriptConfig
)


class BaseConversation(BaseObject, ABC):
    schema_required = False

    def __init__(self, _id, storage_id, storage=None, schema=None):
        super(BaseConversation, self).__init__(_id=_id, storage=storage, schema=schema, storage_id=storage_id)
        self._read_only = False


class Condition(BaseConversation, ABC):

    def __init__(self, intent):
        super(Condition, self).__init__(_id=None)
        self.intent = intent

    def __call__(self, message):
        return self.intent

    @staticmethod
    def get_condition():
        return


class ReferenceCondition(Condition, ABC):
    def __init__(self, intent):
        super(ReferenceCondition, self).__init__(intent)

    def check(self, condition):
        return condition.tag == self.intent


class Message(BaseConversation):
    def __init__(self, message_id: str = None, message: str = None, created_time: int = None,
                 intents: [Intent] = None, entities: [NerTag] = None, dependency_tags: List[DependencyTag] = None,
                 storage=None, storage_id: str = None, user_id: str = None, shop_id: str = None,
                 multiple_choices: List[Node] = None, urls: List[str] = None, answer_infor: str = None,
                 base64_img: str = None, attachments: List = None):
        super(Message, self).__init__(_id=message_id, storage=storage, storage_id=storage_id)
        self.message = message
        self.base64_img = base64_img
        self.urls = urls if urls is not None else []
        self.intents = intents if intents is not None else []
        self.entities = entities
        self.dependency_tags = dependency_tags if dependency_tags is not None else []
        self.created_time = created_time if created_time is not None else int(datetime.now().timestamp())
        self.user_id = user_id
        self.shop_id = shop_id
        self.multiple_choices = multiple_choices if multiple_choices is not None else []
        self.answer_infor = answer_infor
        self.extract_url()
        self.attachments = {} if attachments is None else {attachment.id: attachment for attachment in attachments}

    def add_attachments(self, attachments: List):
        for attachment in attachments:
            self.add_attachment(attachment)

    def add_attachment(self, attachment):
        if attachment.id not in self.attachments:
            self.attachments[attachment.id] = attachment

    def extract_url(self):
        if self.message is not None:
            message = self.message
            message = f" {message} "
            self.urls = list(set(self.urls + list(re.findall(r"(?P<url>https?://[^\s]+)", self.message))))
            for url in self.urls:
                message = message.replace(f" {url} ", "")
            self.message = message.strip()

    @property
    def intent_set(self):
        return set(intent.tag for intent in self.intents)

    def update_intents(self, intents: Union[List[Union[str, Intent]], Set[str]]):
        intent_set = self.intent_set
        for intent in intents:
            if isinstance(intent, str):
                if intent not in intent_set:
                    self.intents.append(Intent(tag=intent, score=1))
            else:
                if intent.tag not in intent_set:
                    self.intents.append(intent)

    def update_entities(self, entities: List[NerTag]):
        self.entities += entities

    def drop_user_intents(self):
        new_intents = []
        for intent in self.intents:
            if intent.subject != "User":
                new_intents.append(intent)
        self.intents = new_intents

    def drop_intents(self, intents: List[str]):
        drop_intents = []
        for intent in self.intents:
            if intent.tag in intents:
                drop_intents.append(intent)

        for intent in drop_intents:
            self.intents.remove(intent)

    @staticmethod
    def get_class_by_type(object_class):
        output_class = None
        if object_class is not None:
            output_class = getattr(sys.modules[__name__], object_class)
        if output_class is None:
            output_class = Message
        return output_class

    @property
    def _json(self):
        return {
            NAME: self.name,
            CONV_MESSAGE_TEXT: self.message,
            CONV_MESSAGE_INTENT: [intent.dict() for intent in (self.intents if self.intents is not None else [])],
            CONV_MESSAGE_TIME: self.created_time,
            CONV_MESSAGE_ENTITIES: [entity.dict() for entity in (self.entities if self.entities is not None else [])],
            CONV_MESSAGE_DEPENDENCY: [tag.dict() for tag in self.dependency_tags],
            CONV_MESSAGE_USER_ID: self.user_id,
            CONV_MESSAGE_SHOP_ID: self.shop_id,
            CONV_MESSAGE_MULTIPLE_CHOICES: [node.json for node in self.multiple_choices],
            CONV_MESSAGE_URLS: self.urls,
            CONV_MESSAGE_ANSWER_INFO: self.answer_infor,
            CONV_MESSAGE_BASE64_IMG: self.base64_img,
            CONV_MESSAGE_ATTACHMENTS: [attachment.all_data for attachment in self.attachments.values()]
        }

    @property
    def _all_data(self):
        return self._json

    @classmethod
    def _from_json(cls, data, storage=None, schema_required=None, graph_nodes=None, **kwargs):
        message_id = data.get(OBJECT_ID)
        storage_id = data.get(STORAGE_ID)
        class_name = data.get(CLASS)
        user_id = data.get(CONV_MESSAGE_USER_ID)
        shop_id = data.get(CONV_MESSAGE_SHOP_ID)
        message_class = cls.get_class_by_type(class_name)
        if message_id is None:
            message_id = data.get(CONV_MESSAGE_ID)
        intents = data.get(CONV_MESSAGE_INTENT, [])
        entities = data.get(CONV_MESSAGE_ENTITIES)
        dependency_tags = data.get(CONV_MESSAGE_DEPENDENCY, [])
        if intents is None:
            intents = []
        if dependency_tags is None:
            dependency_tags = []
        intents = [Intent(tag=item.get("tag"), score=item.get("score", 0)) for item in intents]
        if entities is not None:
            entities = [NerTag(text=item.get("text"), label=item.get("label"), begin=item.get("begin"),
                               end=item.get("end"), entity_id=item.get("entity_id"), labels=item.get("labels"))
                        for item in entities]
        dependency_tags = [DependencyTag(form=item.get("form"), posTag=item.get("posTag"), head=item.get("head"),
                                         depLabel=item.get("depLabel"), index=item.get("index"))
                           for item in dependency_tags]
        multiple_choices = [Node.from_json(item) for item in
                            Message.get_json_value(data, CONV_MESSAGE_MULTIPLE_CHOICES, [])]
        urls = Message.get_json_value(data, CONV_MESSAGE_URLS, [])
        urls = [item for item in urls if item is not None]
        base64_img = data.get(CONV_MESSAGE_BASE64_IMG)
        attachments = [Node.from_json(item)
                       for item in Message.get_json_value(data, CONV_MESSAGE_ATTACHMENTS, [])]
        if graph_nodes is not None:
            attachments = [graph_nodes[attachment.id] for attachment in attachments]
        return message_class(message_id=message_id,
                             message=data.get(CONV_MESSAGE_TEXT),
                             intents=intents,
                             entities=entities,
                             dependency_tags=dependency_tags,
                             created_time=data.get(CONV_MESSAGE_TIME),
                             storage=storage,
                             storage_id=storage_id,
                             user_id=user_id,
                             shop_id=shop_id,
                             multiple_choices=multiple_choices,
                             urls=urls,
                             base64_img=base64_img,
                             attachments=attachments)


class Response(Message):
    def extract_url(self):
        pass

    def join(self, other, delimiter: str = "*", join_first=False):
        if other is not None:
            if isinstance(other, str):
                other_message = other
            else:
                other_message = other.message
            if join_first:
                self.message = f"{other_message} {delimiter} {self.message}"
            else:
                self.message = f"{self.message} {delimiter} {other_message}"


class State(BaseConversation):
    def __init__(self, conv_id: str, message: Message = None, state_id: str = None, last_response: Response = None,
                 response: Response = None, direct_send: bool = False, current_actions: List[str] = None,
                 storage=None, storage_id: str = None, state_action_config_id: str = None,
                 state_action_config: StateActionConfig = None, multiple_choices: List = None, **kwargs):
        super(State, self).__init__(_id=state_id, storage=storage, storage_id=storage_id)
        self.message = message
        self.response = response
        self.last_response = last_response
        self.direct_send = direct_send
        self.state_action_config = state_action_config \
            if state_action_config is not None \
            else StateActionConfig.default(storage=storage, state_action_config_id=state_action_config_id)
        self.current_actions = [self.state_action_config.tasks[action_name]
                                for action_name in (current_actions if current_actions is not None else [])
                                if action_name in self.state_action_config.tasks]
        self.conv_id = conv_id
        self.load_default_actions()
        self.multiple_choices = multiple_choices if multiple_choices is not None else []

    @property
    def empty_message(self):
        return self.message is None or self.message.entities is None or self.message.message == ""

    @property
    def empty_response(self):
        return self.response is None

    @property
    def has_user_pending_choices(self):
        if self.multiple_choices is None or len(self.multiple_choices) <= 1:
            return False
        return True

    @property
    def has_a_choice(self):
        if self.multiple_choices is not None and len(self.multiple_choices) == 1 and \
                (BOT_USER_CHOOSE_A_VALUE in self.intent_set or BOT_USER_CHOOSE_AN_OBJECT in self.intent_set):
            return True
        return False

    @property
    def task(self):
        return self.state_action_config.name

    @property
    def is_done_state(self):
        return self.task == "DONE"

    def refresh(self):
        for action in self.state_action_config.tasks.values():
            action.refresh()

    def get_action_by_entry_point(self):
        if not self.current_action.is_done_action and not self.current_action.is_begin_action:
            for branch in self.current_action.branches.values():
                if branch.done and not branch.only_has_message:
                    return False
        entry_points = self.state_action_config.entry_points
        intents = self.message.intents
        intents.sort(key=lambda item: 0 if item.subject == "User" else 1)
        if USER_HAS_MESSAGE in intents:
            intents.remove(USER_HAS_MESSAGE)
            intents.append(USER_HAS_MESSAGE)

        best_entry_point = None
        best_score = 0
        for entry_point in entry_points.values():
            is_entry_point_satisfied, score = entry_point.is_satisfied(intents)
            if is_entry_point_satisfied and score > best_score:
                best_score = score
                best_entry_point = entry_point

        if best_entry_point is not None:
            action: ActionConfig = best_entry_point.actions[0]
            current_action = self.current_action
            if current_action.only_has_message_expectation:
                self.drop_action()
            if current_action is None or current_action.name != action.name:
                self.refresh()
                self.current_actions.append(action)
                return True

    @property
    def done(self):
        return self.current_action.is_done_action

    def load_default_actions(self):
        if len(self.current_actions) == 0:
            default_entry_point = self.state_action_config.default_entry_point
            if default_entry_point is not None:
                self.current_actions = [default_entry_point.get_action()]

    @property
    def current_action(self) -> ActionConfig:
        if len(self.current_actions) > 0:
            return self.current_actions[-1]

    @property
    def intents(self):
        return self.message.intents

    @property
    def intent_set(self):
        if self.message is not None:
            return self.message.intent_set
        return set()

    def update_intents(self, intents: List[str]):
        self.message.update_intents(intents)

    def add_action(self, action: ActionConfig):
        if action is not None:
            current_action = self.current_action
            if current_action is not None and current_action.name != action.name:
                self.current_actions.append(action)

    def drop_action(self):
        if len(self.current_actions) > 1:
            current_action = self.current_action
            if current_action is not None:
                if not current_action.is_done_action:
                    self.current_actions.pop(-1)

    def add_message(self, message: Message):
        if self.message is not None:
            self.message.delete(force=True)
        self.message = message
        if message is not None:
            message.storage_id = self.storage_id

    def add_response(self, response: Response):
        if self.response is not None:
            self.response.delete(force=True)
        self.response = response
        response.storage_id = self.storage_id

    @property
    def last_message_time(self):
        if self.message is not None:
            return self.message.created_time

    @property
    def last_response_time(self):
        if self.response is not None:
            return self.response.created_time

    @property
    def _json(self):
        return {
            NAME: self.name,
            CONV_MESSAGE: self.message.static_info if self.message is not None else None,
            CONV_STATE_ACTIONS: [action.name for action in self.current_actions if action is not None],
            CONV_STATE_ACTION_CONFIG: self.state_action_config.json,
            CONV_RESPONSE: self.response.static_info if self.response is not None else self.response,
            CONV_LAST_RESPONSE: self.last_response.static_info if self.last_response is not None else None,
            CONV_STATE_DIRECT_SEND: self.direct_send,
            CONV_ID: self.conv_id,
            CONV_STATE_MULTIPLE_CHOICES: [item if isinstance(item, str) else item.json for item in
                                          self.multiple_choices]
        }

    @property
    def _all_data(self):
        return {
            NAME: self.name,
            CONV_MESSAGE: self.message.all_data if self.message is not None else None,
            CONV_STATE_ACTIONS: [action.name for action in self.current_actions],
            CONV_STATE_ACTION_CONFIG: self.state_action_config.json,
            CONV_RESPONSE: self.response.all_data if self.response is not None else self.response,
            CONV_LAST_RESPONSE: self.last_response.static_info if self.last_response is not None else None,
            CONV_STATE_DIRECT_SEND: self.direct_send,
            CONV_ID: self.conv_id,
            CONV_STATE_MULTIPLE_CHOICES: [item if isinstance(item, str) else item.json for item in
                                          self.multiple_choices]
        }

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, **kwargs):
        response_message = data.get(CONV_RESPONSE)
        if response_message is not None:
            response_message = Response.from_json(response_message, storage=storage, **kwargs)
        message = data.get(CONV_MESSAGE)
        if message is not None:
            message = Message.from_json(data.get(CONV_MESSAGE, {}), storage=storage, **kwargs)
        last_response_message = data.get(CONV_LAST_RESPONSE)
        if last_response_message is not None:
            last_response_message = Response.from_json(last_response_message, storage=storage, **kwargs)
        state_action_config = data.get(CONV_STATE_ACTION_CONFIG)
        if state_action_config is not None:
            state_action_config = StateActionConfig.from_json(state_action_config, storage=storage)
        else:
            state_action_config = StateActionConfig.default(storage=storage)
        multiple_choices = [Node.from_json(item) for item in Node.get_json_value(data, CONV_STATE_MULTIPLE_CHOICES, [])]
        return State(state_id=data.get(OBJECT_ID),
                     message=message,
                     response=response_message,
                     direct_send=data.get(CONV_STATE_DIRECT_SEND, False),
                     storage=storage,
                     conv_id=data.get(CONV_ID),
                     storage_id=data[STORAGE_ID],
                     last_response=last_response_message,
                     state_action_config=state_action_config,
                     current_actions=data.get(CONV_STATE_ACTIONS),
                     multiple_choices=multiple_choices)

    def save(self, force=False, field_methods=None):
        super().save(force=force, field_methods=field_methods)
        if self.message is not None:
            self.message.save(force=force)
        if self.response is not None:
            self.response.save(force=force)
        if self.last_response is not None:
            self.last_response.save(force=force)


class Conversation(BaseConversation):
    def __init__(self, storage_id: str, shop: Shop = None, user: User = None, states: List[State] = None,
                 data: SubGraph = None, history: [Message] = None, storage=None, schema=None,
                 pending_messages: List[Message] = None, script_config: ScriptConfig = None, conv_id: str = None):
        super(Conversation, self).__init__(_id=conv_id, storage=storage, schema=schema, storage_id=storage_id)
        self.script_config = script_config if script_config is not None else ScriptConfig.default(storage=storage)
        self.states: List[State] = states if states is not None else []
        self.state_dict = {state.task: state for state in self.states}
        if data is not None:
            self.data = data
        else:
            if shop is not None and user is not None:
                self.data = SubGraph(nodes=[shop, user], shop=shop, user=user, storage=storage,
                                     storage_id=self.storage_id)
            else:
                raise ValueError("User and Shop must not be None if data is not represented")

        self.history = history if history is not None else []
        self.conv_id = conv_id if conv_id is not None else self.id
        self.pending_messages = pending_messages if pending_messages is not None else []
        self.pending_responses = []
        self.init_contact_relation()

    @property
    def has_user_pending_choices(self):
        current_state = self.current_state
        if current_state is None:
            return False
        return current_state.has_user_pending_choices

    @classmethod
    def skip_fields(cls):
        return [CONV_HISTORY]

    @property
    def history_text(self) -> List[str]:
        if len(self.history) > 0:
            output = [self.history[0].message]
            for i, message in enumerate(self.history[1:]):
                if str(type(message)) == str(type(self.history[i])):
                    output[-1] += ". " + message.message
                else:
                    output.append(message.message)
        else:
            output = []
        return output

    @property
    def pending_message(self):
        if len(self.pending_messages) > 0:
            return self.pending_messages[0]

    def add_pending_message(self, message: Message):
        if len(self.pending_messages) == 0 or message.hashed != self.pending_messages[-1].hashed:
            self.pending_messages.append(message)

    def drop_pending_message(self):
        self.pending_messages.pop(0)

    @property
    def user(self):
        return self.data.user

    @property
    def shop(self):
        return self.data.shop

    def init_contact_relation(self):
        shop_user_relations = self.user.src_dst_relations(self.shop, "contact")
        if len(shop_user_relations) == 0:
            contact_relation = Relation(src_node=self.user, dst_node=self.shop, name="contact", storage=self.storage,
                                        storage_id=self.storage_id)
            contact_relation.complete_end_nodes()
            contact_relation.save()
            self.logger.info("CREATE CONTACT RELATION")

    def add_state(self, new_state: State):
        """
        :param:
        new_state: if new_state's task exist in current conversation => return the appropriate state
                      else add new_state to the current conversation and return new_state
        :return:
        """
        current_state: State = self.state_dict.get(new_state.task)
        if current_state is None:
            self.states.append(new_state)
            self.state_dict[new_state.task] = new_state
            return new_state
        else:
            self.states.remove(current_state)
            self.states.append(current_state)
            return current_state

    def new_state_with_message(self, message: Message = None, state_action_config_id: str = None,
                               state_action_config: StateActionConfig = None):
        if message is not None:
            message.storage = self.storage
        new_state = State(message=message, storage=self.storage, conv_id=self.id, storage_id=self.storage_id,
                          state_action_config_id=state_action_config_id, state_action_config=state_action_config)

        current_state: State = self.add_state(new_state)
        if current_state != new_state:
            current_state.add_message(message)
        self.history.append(message)
        return new_state

    def add_message(self, message: Message):
        if message.storage is None:
            message.storage = self.storage
        current_state = self.current_state
        if current_state is None:
            self.new_state_with_message(message)
        else:
            current_state.add_message(message)
        self.history.append(message)

    def add_response(self, response: Response):
        if response.storage is None:
            response.storage = self.storage
        current_state = self.current_state
        if current_state is None:
            self.new_state_with_message(response)
        else:
            current_state.add_response(response)
        self.history.append(response)

    def add_object(self, node: Node):
        self.data.add_node(node)

    def drop_state(self):
        if len(self.states) > 0:
            last_state = self.states.pop(-1)
            if last_state.message is not None:
                last_state.message.delete(force=True)
            if last_state.response is not None:
                last_state.response.delete(force=True)
            if last_state.name in self.state_dict:
                del self.state_dict[last_state.name]
            last_state.delete(force=True)

    def move_state_backward(self, state):
        if state.task in self.state_dict:
            self.states.remove(state)
            self.states = [state, *self.states]

    @property
    def current_action(self):
        current_state = self.current_state
        if current_state is not None:
            return self.current_state.current_action

    @property
    def current_expectations(self) -> ActionExpectation:
        current_action = self.current_action
        if current_action is not None:
            return current_action.expectations

    def next_action(self):
        current_state = self.current_state
        if current_state is not None:
            current_action = current_state.current_action
            current_state.drop_action()
            next_action = current_action.get_next_action()
            if next_action is not None:
                current_state.add_action(next_action)
                return True
        return False

    def drop_action(self):
        current_state = self.current_state
        if current_state is not None:
            self.current_state.drop_action()

    @property
    def current_state(self) -> State:
        if len(self.states) > 0:
            return self.states[-1]

    def get_state_by_entry_point(self):
        entry_points = self.script_config.entry_points
        message: Message = self.pending_message
        if self.current_state is None:
            state_config: StateActionConfig = entry_points[DEFAULT_TAG].actions[0]
            self.new_state_with_message(message, state_action_config=state_config)
            return True
        else:
            intents = message.intents
            if USER_HAS_MESSAGE in intents:
                intents.remove(USER_HAS_MESSAGE)
                intents.append(USER_HAS_MESSAGE)

            best_entry_point = None
            best_score = 0
            for entry_point in entry_points.values():
                is_entry_point_satisfied, score = entry_point.is_satisfied(intents)
                if is_entry_point_satisfied:
                    if score > best_score or (score == best_score and entry_point.has_user_intent):
                        best_score = score
                        best_entry_point = entry_point

            if best_entry_point is not None:
                current_state = self.current_state
                state_config: StateActionConfig = best_entry_point.actions[0]
                if len(best_entry_point.actions) > 1:
                    state_config = best_entry_point.actions[0]
                    for item in best_entry_point.actions:
                        if item.name == current_state.task:
                            state_config = item
                            break
                state_config, response = state_config.get_next_state_by_best_branch(intents)
                if current_state.name != state_config.name:
                    self.new_state_with_message(message, state_action_config=state_config)
                    self.pending_responses.append(Response(message=response, user_id=self.user.id, shop_id=self.shop.id,
                                                           storage=self.storage, storage_id=self.storage_id))
                    return True
            return False

    def next_state(self):
        current_state = self.current_state
        if current_state is not None and current_state.done:
            if self.pending_message is not None:
                intents = self.pending_message.intents
            else:
                intents = []
            current_state_name = current_state.task
            current_state_config = self.script_config.tasks[current_state_name]
            next_state_config: StateActionConfig = current_state_config.get_next_action()
            # MOVE TO STATE BY BRANCHES
            next_state_config, _ = next_state_config.get_next_state_by_best_branch(intents)
            self.new_state_with_message(message=Message(message="", user_id=self.user.id, shop_id=self.shop.id,
                                                        storage=self.storage, storage_id=self.storage_id),
                                        state_action_config=next_state_config)
            if current_state != self.current_state:
                return True
            else:
                self.move_state_backward(self.current_state)
                return False
        return False

    @property
    def static_info(self):
        info = super().static_info
        info[CONV_USER] = self.user.static_info
        info[CONV_SHOP] = self.shop.static_info
        return info

    @property
    def _json(self):
        output = {
            NAME: self.name,
            CONV_USER: self.user.static_info,
            CONV_SHOP: self.shop.static_info,
            CONV_STATES: [state.static_info for state in self.states if state is not None],
            CONV_DATA: self.data.static_info,
            CONV_HISTORY: [message.json for message in self.history if message is not None],
            CONV_PENDING_MESSAGES: [message.json for message in self.pending_messages],
            CONV_SCRIPT_CONFIG: self.script_config.static_info if self.script_config is not None else None
        }
        return output

    @property
    def _all_data(self):
        return {
            NAME: self.name,
            CONV_USER: self.user.all_data,
            CONV_SHOP: self.shop.all_data,
            CONV_STATES: [state.all_data for state in self.states if state is not None],
            CONV_DATA: self.data.all_data,
            CONV_HISTORY: [message.json for message in self.history if message is not None],
            CONV_PENDING_MESSAGES: [message.json for message in self.pending_messages if message is not None],
            CONV_SCRIPT_CONFIG: self.script_config.static_info if self.script_config is not None else None
        }

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, script_config=None, nodes: dict = None, **kwargs):
        conv_id = data.get(OBJECT_ID)
        storage_id = data.get(STORAGE_ID)
        if conv_id is None or storage_id is None:
            return

        user_data = Conversation.get_json_value(data, CONV_USER, None)
        shop_data = Conversation.get_json_value(data, CONV_SHOP, None)
        if user_data is None or shop_data is None:
            return

        user = User.from_json(user_data, storage=storage, nodes=nodes)
        shop = User.from_json(shop_data, storage=storage, nodes=nodes)

        if CONV_DATA in data:
            memory_data = SubGraph.from_json(data.get(CONV_DATA), storage=storage, nodes=nodes)
        else:
            memory_data = SubGraph(storage_id=storage_id, nodes=[user, shop], user=user, shop=shop, storage=storage)

        pending_messages = data.get(CONV_PENDING_MESSAGES, [])
        pending_messages = pending_messages if pending_messages is not None else []
        pending_messages = [Message.from_json(message_data, storage=storage, nodes=nodes)
                            for message_data in pending_messages]
        if script_config is None:
            script_config = data.get(CONV_SCRIPT_CONFIG)
            if script_config is not None:
                script_config = ScriptConfig.from_json(script_config, storage=storage, nodes=nodes)
            else:
                script_config = ScriptConfig.default(storage=storage)
        states = []
        state_data = data.get(CONV_STATES, [])
        state_data = state_data if state_data is not None else []
        for state_data in state_data:
            state: State = State.from_json(data=state_data, storage=storage,
                                           graph_nodes=memory_data.nodes,
                                           nodes=nodes)
            state.conv_id = conv_id
            states.append(state)
        return Conversation(conv_id=conv_id, states=states, data=memory_data, storage=storage, storage_id=storage_id,
                            pending_messages=pending_messages, script_config=script_config,
                            user=user, shop=shop)

    @classmethod
    def from_user_shop_id(cls, user_id: str, shop_id: str, storage_id: str, storage=None, script_config=None):
        description = {
            "user.id": user_id,
            "shop.id": shop_id,
            STORAGE_ID: storage_id,
            CLASS: cls.class_name()
        }
        conversation = cls.from_description(description, storage=storage, script_config=script_config)
        if conversation is None:
            user_description = {
                OBJECT_ID: user_id,
                STORAGE_ID: storage_id,
                CLASS: User.class_name()
            }
            shop_description = {
                OBJECT_ID: shop_id,
                STORAGE_ID: storage_id,
                CLASS: Shop.class_name()
            }
            user = User.from_json(user_description, storage=storage)
            shop = Shop.from_json(shop_description, storage=storage)
            conversation = Conversation(storage=storage, storage_id=storage_id, user=user, shop=shop,
                                        script_config=script_config)
            return conversation
        return conversation

    def save(self, force=False, field_methods=None):
        super().save(force=force, field_methods={CONV_HISTORY: "push"})
        self.data.save(force=force)
        [state.save(force=force) for state in self.states]
