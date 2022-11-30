from typing import Union, List, Dict, Set
import random

from cached_property import cached_property

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.default_intents import *
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Schema.objects.common.nlp_tags import Intent, NerTag


class BaseExpectation:
    def __init__(self, schema: str, done: bool = False):
        self.schema = schema
        if schema[0] == "*":
            self.required = True
            schema = schema[1:]
        else:
            self.required = False
        self._schema = schema
        self.done = done
        self.neighbours = {}

    def add_neighbour(self, neighbour):
        self.neighbours[str(id(neighbour))] = neighbour

    def forward_done_signal(self, _done, updated_set: set = None):
        if updated_set is None:
            updated_set = set()
        if str(id(self)) in updated_set:
            return
        if not self.required:
            self.done = _done
        updated_set.add(str(id(self)))
        for neighbour in self.neighbours.values():
            neighbour.forward_done_signal(_done, updated_set)

    def refresh(self):
        if self.required:
            self.done = False

    def json(self):
        raise NotImplementedError("Need implementation")


class ExpectedValue(BaseExpectation):
    def __init__(self, schema: str, done: bool = False):
        super(ExpectedValue, self).__init__(schema, done)
        self.subject, attr = self._schema.split("@")
        self.attr, entity_types = attr.split("=")
        self.entity_types = set(item.strip() for item in entity_types.replace("[", "").replace("]", "").split(",")
                                if len(item.strip()) > 0)

    @property
    def id(self):
        return BaseObject.generate_hash(f"{self.__class__.__name__}|{self._schema}")

    def __repr__(self):
        return f"{self.subject}@{self.attr}=[{','.join(self.entity_types)}]"

    @property
    def json(self):
        return {
            CONV_EXPECTED_VALUE_SCHEMA: self.schema,
            CONV_EXPECTED_VALUE_DONE: self.done
        }


class ExpectedIntent(BaseExpectation):
    def __init__(self, schema: str, done: bool = False):
        super(ExpectedIntent, self).__init__(schema, done)
        self.tag = self._schema
        self.subject, _ = self._schema.split("@")

    @property
    def id(self):
        return BaseObject.generate_hash(f"{self.__class__.__name__}|{self.tag}")

    def __repr__(self):
        return str(id(self))

    @property
    def json(self):
        return {
            CONV_EXPECTED_INTENT: self.schema,
            CONV_EXPECTED_INTENT_DONE: self.done
        }

    def refresh(self):
        self.done = False

    @property
    def is_bot_intent(self):
        return self.subject == "Bot"


class ActionExpectation:
    def __init__(self, intents: List[Dict] = None, values: List[Dict] = None, responses: List[str] = None,
                 next_actions: List[str] = None, post_actions: List[Dict] = None, **kwargs):
        intents = [ExpectedIntent(**intent) for intent in intents] if intents is not None else []
        self.intents = {intent.tag: intent for intent in intents}
        expected_values = [ExpectedValue(**value) for value in values] if values is not None else []
        self.expected_values = {expected_value.id: expected_value for expected_value in expected_values}
        self.responses = responses if responses is not None else []
        self.next_action_names = next_actions if next_actions is not None else []
        self.next_actions = []
        post_actions = [ExpectedIntent(**intent) for intent in post_actions] if post_actions is not None else []
        self.post_actions = {intent.tag: intent for intent in post_actions}

    def is_satisfied(self, intents: List[Union[str, Intent]]):
        if len(intents) == 0:
            return False, 0
        if isinstance(intents[0], Intent):
            intents = [intent.tag for intent in intents]

        for intent in self.intents:
            if intent not in intents:
                return False, 0
        return True, len(self.intents)

    @cached_property
    def only_has_message(self):
        return len(self.intents) == 1 and USER_HAS_MESSAGE in self.intents

    @property
    def score(self) -> int:
        output = 0
        for intent in self.intents.values():
            if intent.done:
                output += 1
        for value in self.values:
            if value.done:
                output += 1
        return output

    def refresh(self):
        for intent in list(self.intents.values()):
            intent.refresh()
        for value in list(self.expected_values.values()):
            value.refresh()

    @property
    def values(self):
        return list(self.expected_values.values())

    @property
    def id(self):
        return BaseObject.generate_hash(f"{self.__class__.__name__}|{list(self.intents.keys())}|{self.values}")

    @property
    def done(self):
        for intent in self.intents.values():
            if not intent.done:
                return False
        for value in self.values:
            if not value.done:
                return False
        return True

    @property
    def partially_done(self):
        if not self.done:
            for value in self.values:
                if value.done:
                    return True
            for intent in self.intents.values():
                if intent.done:
                    return True
        return False

    @property
    def intent_set(self):
        return set(self.intents)

    def validate(self, intents: Set[str], values: List[NerTag]):
        matched_expected_entities = {}
        tags = {ner_tag.id: ner_tag for ner_tag in values}
        for ner_tag in values:
            for expected_tag in self.values:
                matched_score = len(set(ner_tag.labels).intersection(expected_tag.entity_types))
                if matched_score > 0:
                    if ner_tag.id not in matched_expected_entities:
                        matched_expected_entities[ner_tag.id] = []
                    matched_expected_entities[ner_tag.id].append((expected_tag, matched_score))

        for ner_id, matched_tags in matched_expected_entities.items():
            if len(matched_tags) > 1:
                best_score = 0
                best_matched_tag = None
                for matched_tag, matched_score in matched_tags:
                    if matched_score > best_score:
                        best_score = matched_score
                        best_matched_tag = matched_tag
                matched_expected_entities[ner_id] = best_matched_tag
            else:
                matched_expected_entities[ner_id] = matched_tags[0][0]

        matched_entities = [(matched_tag, tags[ner_id]) for ner_id, matched_tag in matched_expected_entities.items()]
        if len(matched_entities) > 0:
            intents.add(USER_PROVIDE_DATA)
        matched_intents = self.intent_set.intersection(intents)
        return matched_intents, matched_entities, intents

    def update_actions(self, actions):
        for action in actions:
            if action.name in self.next_action_names and action not in self.next_actions:
                self.next_actions.append(action)
        self.next_actions.sort(key=lambda act: self.next_action_names.index(act.name))

    def get_next_action(self):
        not_done_actions = [action for action in self.next_actions if not action.done]
        if len(not_done_actions) > 0:
            return not_done_actions[0]
        else:
            if len(self.next_actions) > 0:
                return self.next_actions[0]

    def get_response(self) -> str:
        if len(self.responses) > 0:
            return random.choice(self.responses)
        return ""

    @property
    def json(self):
        return {
            CONV_EXPECTED_INTENTS: [intent.json for intent in self.intents.values()],
            CONV_EXPECTED_VALUES: [value.json for value in self.values],
            CONV_RESPONSES: self.responses,
            CONV_NEXT_ACTIONS: self.next_action_names,
            CONV_BOT_POST_ACTIONS: [intent.json for intent in self.post_actions.values()]
        }


class StateExpectation(ActionExpectation):
    def __init__(self, intents: List[Dict] = None, values: List[Dict] = None, responses: List[str] = None,
                 next_actions: List[str] = None, **kwargs):
        super(StateExpectation, self).__init__(intents=intents, values=values, responses=responses,
                                               next_actions=next_actions)
