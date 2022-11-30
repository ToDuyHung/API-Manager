from abc import ABC
from typing import List, Dict, Tuple, Union
import random

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Schema.objects.common.nlp_tags import Intent
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Schema.objects.conversation.base_expectation import (
    ExpectedValue,
    ExpectedIntent,
    ActionExpectation,
    StateExpectation
)


class ActionConfig(BaseObject, ABC):

    schema_required = False

    def __init__(self, name: str, in_conditions: List[str] = None, requests: List[str] = None, required: bool = False,
                 recommendations: List[str] = None, expectations: Dict = None, branches: List[Dict] = None,
                 passable: bool = False, storage=None, storage_id=None, pre_actions: List[Dict] = None,
                 post_actions: List[Dict] = None, **kwargs):
        if OBJECT_ID in kwargs:
            del kwargs[OBJECT_ID]
        if f"_{OBJECT_ID}" in kwargs:
            del kwargs[f"_{OBJECT_ID}"]
        super(ActionConfig, self).__init__(_id=name, storage=storage, storage_id=storage_id, **kwargs)
        self.name = name
        self.in_conditions = in_conditions if in_conditions is not None else []
        self.requests = requests if requests is not None else []
        self.recommendations = recommendations if recommendations is not None else []
        self.expectations = ActionExpectation(**expectations) if expectations is not None else ActionExpectation()
        branches = [ActionExpectation(**value) for value in (branches if branches is not None else [])]
        self.branches = {action.id: action for action in branches}
        self.branches[self.expectations.id] = self.expectations
        pre_actions = [ExpectedIntent(**intent) for intent in pre_actions] if pre_actions is not None else []
        self.pre_actions = {intent.tag: intent for intent in pre_actions}
        post_actions = [ExpectedIntent(**intent) for intent in post_actions] if post_actions is not None else []
        self.post_actions = {intent.tag: intent for intent in post_actions}
        self.update_expectations()
        self.required = required
        self.passable = passable

    @property
    def only_has_message_expectation(self):
        return self.expectations.only_has_message

    def refresh(self):
        for branch in self.branches.values():
            branch.refresh()

    @property
    def has_next_action(self):
        for branch in self.branches.values():
            if len(branch.next_actions) > 0:
                return True
        return False

    @property
    def is_done_action(self):
        return self.name == "DONE"

    @property
    def is_begin_action(self):
        return self.name == "BEGIN"

    def update_expectations(self):
        expected_intents = {}
        for branch_id, branch in self.branches.items():
            for intent_name, intent in branch.intents.items():
                if intent.required:
                    continue
                if intent_name not in expected_intents:
                    expected_intents[intent_name] = intent
                else:
                    branch.intents[intent_name] = expected_intents[intent_name]

    @property
    def current_branch(self):
        best_branch = None
        best_score = 0
        for branch in self.branches.values():
            branch_score = branch.score
            if branch.done and branch_score >= best_score:
                best_branch = branch
                best_score = branch_score
        return best_branch

    def get_next_action(self):
        next_action = None
        if self.expectations.done:
            self.logger.debug(f"ACTION {self.name}=====DONE=====")
            next_action = self.expectations.get_next_action()
        else:
            best_branch = self.current_branch

            if best_branch is not None:
                next_action = best_branch.get_next_action()
                self.logger.debug(f"BRANCH {self.name}.{best_branch.expected_values}=====DONE=====")

        return next_action

    def get_request(self):
        if len(self.requests) > 0:
            return random.choice(self.requests)

    @property
    def done(self):
        if self.required:
            return self.expectations.done
        else:
            if self.passable:
                for branch in self.branches.values():
                    if branch.done:
                        return True
            return False

    def update_actions(self, actions):
        self.expectations.update_actions(actions)
        for expectation in self.branches.values():
            expectation.update_actions(actions)

    @property
    def _json(self):
        return {
            CONV_ACTION_IN_CONDITION: self.in_conditions,
            CONV_ACTION_REQUESTS: self.requests,
            CONV_ACTION_RECOMMENDATIONS: self.recommendations,
            CONV_ACTION_BRANCHES: [action_branch.json for action_branch in self.branches.values()],
            CONV_ACTION_EXPECTATIONS: self.expectations.json,
            CONV_ACTION_REQUIRED: self.required,
            CONV_ACTION_PASSABLE: self.passable,
            CONV_ACTION_BOT_PRE_ACTIONS: [intent.json for intent in self.pre_actions.values()],
            CONV_ACTION_BOT_POST_ACTIONS: [intent.json for intent in self.post_actions.values()]
        }

    def __repr__(self):
        return json.dumps(self.json, indent=4)

    def update_info_mapping(self, information_mapping):
        pass


class EntryPoint:
    def __init__(self, tag: str, responses: List[str] = None, actions: List = None, is_global: bool = False, **kwargs):
        self.tag = tag
        self.intents = tag.split("+")
        self.responses = responses if responses is not None else []
        self.actions = actions if actions is not None else []
        self.is_global = is_global
        self.has_user_intent = "User@" in tag

    def contain_intent(self, intent: str):
        return intent in self.intents

    def is_satisfied(self, intents: List[Union[str, Intent]]):
        if len(intents) == 0:
            return False, 0
        if isinstance(intents[0], Intent):
            intents = [intent.tag for intent in intents]

        for intent in self.intents:
            if intent not in intents:
                return False, 0
        return True, len(self.intents)

    @property
    def id(self):
        return BaseObject.generate_hash(f"{self.__class__.__name__}|{self.tag}|{self.actions}")

    def get_response(self) -> str:
        if len(self.responses) > 0:
            return random.choice(self.responses)

    def get_action(self) -> ActionConfig:
        if len(self.actions) > 0:
            return self.actions[0]

    @property
    def json(self):
        return {
            CONV_STATE_EP_TAG: self.tag,
            CONV_STATE_EP_RESPONSES: self.responses,
            CONV_STATE_EP_ACTIONS: [action.name for action in self.actions],
            CONV_STATE_EP_IS_GLOBAL: self.is_global
        }


class InfoMapping:
    def __init__(self, key, value):
        self.key = key
        if not isinstance(value, dict):
            raise ValueError("Value of response mapping must be a dict of {default: <default_value>, key1: value1}")
        self.value = value

    @property
    def id(self):
        return BaseObject.generate_hash(f"{self.__class__.__name__}|{self.key}|{self.value}")

    def get_mapping_template(self, key, mapped_key, mapped_value):
        mapping_template = self[mapped_value]
        mapping_template = mapping_template.replace(mapped_key, key)
        return mapping_template

    def __getitem__(self, item):
        if item in self.value:
            return self.value[item]
        return self.value["default"]


class StateActionConfig(ActionConfig):
    def __init__(self, _id: str = None, storage=None, storage_id: str = None, tasks: Dict[str, ActionConfig] = None,
                 entry_points: Dict[str, EntryPoint] = None, info_mapping: Dict[str, InfoMapping] = None,
                 expected_values: Dict[str, ExpectedValue] = None, expectations: Dict = None,
                 branches: List[Dict] = None, **kwargs):
        super(StateActionConfig, self).__init__(storage=storage, storage_id=storage_id, name=_id,
                                                **kwargs)
        self.expected_values = expected_values if expected_values is not None else {}
        self.tasks = tasks if tasks is not None else {}
        self.update_task_actions()
        self.entry_points = entry_points if entry_points is not None else {}
        self.information_mapping = info_mapping if info_mapping is not None else {}

        self.expectations = StateExpectation(**expectations) if expectations is not None else StateExpectation()
        branches = [StateExpectation(**value) for value in (branches if branches is not None else [])]
        self.branches = {action.id: action for action in branches}
        # self.branches[self.expectations.id] = self.expectations
        self.update_expectations()

    def get_next_state_by_best_branch(self, intents):
        branches: List[StateExpectation] = list(self.branches.values())
        best_branch = None
        best_branch_score = None
        for branch in branches:
            is_satisfied, score = branch.is_satisfied(intents)
            if is_satisfied and (best_branch_score is None or best_branch_score < score):
                best_branch_score = score
                best_branch = branch
        if best_branch is not None:
            state_config: StateActionConfig = best_branch.next_actions[0]
            response = best_branch.get_response()
            return state_config, response
        return self, ""

    def update_info_mapping(self, info_mapping: Dict[str, InfoMapping]):
        for key, value in info_mapping.items():
            if key not in self.information_mapping:
                self.information_mapping[key] = value

    def get_next_action(self):
        if len(self.expectations.next_actions) > 0:
            return self.expectations.next_actions[0]
        return self

    def get_info_mapping(self, key) -> Tuple[InfoMapping, str]:
        if key in self.information_mapping:
            return self.information_mapping[key], key
        else:
            key_subject, key_attr = key.split("@")
            for key_info, info_mapping in self.information_mapping.items():
                subject, attr = key_info.split("@")
                if subject == key_subject and attr == "*":
                    return info_mapping, key_info

    @property
    def unsatisfied_expected_values(self) -> List[ExpectedValue]:
        output = []
        for expected_value in self.expected_values.values():
            if not expected_value.done and not expected_value.required:
                output.append(expected_value)
        return output

    @property
    def all_expected_values(self) -> List[ExpectedValue]:
        output = []
        for expected_value in self.expected_values.values():
            if not expected_value.required:
                output.append(expected_value)
        return output

    @property
    def default_entry_point(self):
        if "default" in self.entry_points:
            return self.entry_points["default"]

    def update_task_actions(self):
        actions = list(self.tasks.values())
        for task in actions:
            task.update_actions(actions)

    @property
    def _json(self):
        return {
            NAME: self.name,
            CONV_STATE_EP: [entry_point.json for entry_point in self.entry_points.values()],
            CONV_STATE_MAPPING: {key: info_mapping.value for key, info_mapping in self.information_mapping.items()},
            CONV_STATE_TASKS: {action_name: action.json for action_name, action in self.tasks.items()},
            CONV_STATE_EXPECTATIONS: self.expectations.json,
            CONV_STATE_BRANCHES: [branch.json for branch in self.branches.values()]
        }

    @property
    def _all_data(self):
        return {
            NAME: self.name,
            CONV_STATE_EP: [entry_point.json for entry_point in self.entry_points.values()],
            CONV_STATE_MAPPING: {key: info_mapping.value for key, info_mapping in self.information_mapping.items()},
            CONV_STATE_TASKS: {action_name: action.json for action_name, action in self.tasks.items()},
            CONV_STATE_EXPECTATIONS: self.expectations.json,
            CONV_STATE_BRANCHES: [branch.json for branch in self.branches.values()]
        }

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        obj_id = data[OBJECT_ID]
        storage_id = data[STORAGE_ID]
        expected_values = {}
        if CONV_STATE_TASKS not in data:
            print(data)
        tasks: Dict[str, ActionConfig] = {key: ActionConfig(**value, name=key)
                                          for key, value in data.get(CONV_STATE_TASKS, {}).items()}

        for _, action in tasks.items():
            for branch_id, branch in action.branches.items():
                for expected_value in branch.values:
                    if expected_value.required:
                        continue
                    if expected_value.id not in expected_values:
                        expected_values[expected_value.id] = expected_value
                    else:
                        branch.expected_values[expected_value.id] = expected_values[expected_value.id]
            for expected_value in action.expectations.values:
                if expected_value.required:
                    continue
                if expected_value.id not in expected_values:
                    expected_values[expected_value.id] = expected_value
                else:
                    action.expectations.expected_values[expected_value.id] = expected_values[expected_value.id]

        for _, action in tasks.items():
            for branch_id, branch in action.branches.items():
                for expected_value in branch.values:
                    if expected_value.id in expected_values:
                        expected_value.add_neighbour(expected_values[expected_value.id])
                        expected_values[expected_value.id].add_neighbour(expected_value)
            for expected_value in action.expectations.values:
                if expected_value.id in expected_values:
                    expected_value.add_neighbour(expected_values[expected_value.id])
                    expected_values[expected_value.id].add_neighbour(expected_value)

        entry_points_data = data.get(CONV_STATE_EP, [])
        entry_points_data = entry_points_data if entry_points_data is not None else []
        entry_points: Dict[str, EntryPoint] = {
            value[CONV_STATE_EP_TAG]: EntryPoint(tag=value.get(CONV_STATE_EP_TAG),
                                                 responses=value.get(CONV_STATE_EP_RESPONSES),
                                                 actions=[tasks[action_name]
                                                          for action_name in
                                                          list(set(value.get(CONV_STATE_EP_ACTIONS, [])))],
                                                 is_global=value.get(CONV_STATE_EP_IS_GLOBAL, False))
            for value in entry_points_data}
        info_mapping: Dict[str, InfoMapping] = {key: InfoMapping(key=key, value=value) for key, value in
                                                data.get(CONV_STATE_MAPPING, {}).items()}
        expectations = StateActionConfig.get_json_value(data, CONV_STATE_EXPECTATIONS, {})
        branches = StateActionConfig.get_json_value(data, CONV_STATE_BRANCHES, {})
        return StateActionConfig(_id=obj_id,
                                 storage=storage,
                                 storage_id=storage_id,
                                 tasks=tasks,
                                 entry_points=entry_points,
                                 info_mapping=info_mapping,
                                 expected_values=expected_values,
                                 expectations=expectations,
                                 branches=branches)

    @staticmethod
    def default(storage, state_action_config_id: str = None):
        if state_action_config_id is None:
            state_action_config_id = "default"
        data = {
            "storage_id": "default",
            "id": state_action_config_id,
            "class": StateActionConfig.class_name()
        }
        return StateActionConfig.from_json(data, storage=storage)


class ScriptConfig(StateActionConfig):
    def __init__(self, _id: str = None, storage=None, storage_id: str = None,
                 tasks: Dict[str, StateActionConfig] = None, entry_points: Dict[str, EntryPoint] = None,
                 info_mapping: Dict[str, InfoMapping] = None, expected_values: Dict[str, ExpectedValue] = None):
        super(ScriptConfig, self).__init__(_id=_id, storage=storage, storage_id=storage_id,
                                           tasks=tasks, entry_points=entry_points, info_mapping=info_mapping,
                                           expected_values=expected_values)
        self.add_global_entry_points()
        self.update_info_mapping()

    def update_info_mapping(self, info_mapping: Dict[str, InfoMapping] = None):
        if info_mapping is None:
            info_mapping = self.information_mapping
        for task in self.tasks.values():
            task.update_info_mapping(info_mapping)

    def add_global_entry_points(self):
        for task_name, state_config in list(self.tasks.items()):
            task_entry_points: List[EntryPoint] = list(state_config.entry_points.values())
            for entry_point in task_entry_points:
                if entry_point.is_global:
                    if entry_point.tag not in self.entry_points:
                        self.entry_points[entry_point.tag] = EntryPoint(tag=entry_point.tag, actions=[state_config],
                                                                        is_global=True)
                    else:
                        if state_config not in self.entry_points[entry_point.tag].actions:
                            self.entry_points[entry_point.tag].actions.append(state_config)
        return

    @property
    def _json(self):
        return {
            NAME: self.name,
            CONV_SCRIPT_EP: [entry_point.json for entry_point in self.entry_points.values()],
            CONV_SCRIPT_MAPPING: {key: info_mapping.value for key, info_mapping in self.information_mapping.items()},
            CONV_SCRIPT_TASKS: {action_name: state_config.json
                                for action_name, state_config in self.tasks.items()}
        }

    @property
    def _all_data(self):
        return {
            NAME: self.name,
            CONV_SCRIPT_EP: [entry_point.json for entry_point in self.entry_points.values()],
            CONV_SCRIPT_MAPPING: {key: info_mapping.value for key, info_mapping in self.information_mapping.items()},
            CONV_SCRIPT_TASKS: {action_name: action.json for action_name, action in self.tasks.items()},
        }

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        obj_id = data[OBJECT_ID]
        storage_id = data[STORAGE_ID]
        expected_values = {}
        tasks: Dict[str, StateActionConfig] = {key: StateActionConfig.from_json(data=value, storage=storage,
                                                                                nodes=nodes)
                                               for key, value in data.get(CONV_SCRIPT_TASKS, {}).items() if
                                               value is not None}

        entry_points: Dict[str, EntryPoint] = {
            value[CONV_SCRIPT_EP_TAG]: EntryPoint(tag=value.get(CONV_SCRIPT_EP_TAG),
                                                  actions=[tasks[action_name] for action_name in
                                                           list(set(value.get(CONV_SCRIPT_EP_ACTIONS, [])))])
            for value in data.get(CONV_SCRIPT_EP, [])}
        info_mapping: Dict[str, InfoMapping] = {key: InfoMapping(key=key, value=value) for key, value in
                                                data.get(CONV_SCRIPT_MAPPING, {}).items()}
        return ScriptConfig(_id=obj_id,
                            storage=storage,
                            storage_id=storage_id,
                            tasks=tasks,
                            entry_points=entry_points,
                            info_mapping=info_mapping,
                            expected_values=expected_values)

    @staticmethod
    def default(storage, script_config_id: str = None, storage_id: str = "default"):
        if script_config_id is None:
            script_config_id = "default"
        data = {
            STORAGE_ID: storage_id,
            OBJECT_ID: script_config_id,
            CLASS: ScriptConfig.class_name()
        }
        return ScriptConfig.from_json(data, storage=storage)


if __name__ == "__main__":
    import json
    from TMTChatbot.Common.config.config import Config
    from TMTChatbot.Common.storage.mongo_client import MongoConnector

    _config = Config()
    _storage = MongoConnector(config=_config)
    path = "C:/nguyenpq/workspace/ChatBot/Common/TMTChatbot/StateController/scripts/templates/script_config.json"
    script_config = json.load(open(path, "r", encoding="utf8"))
    script_config = ScriptConfig.from_json(data=script_config, storage=_storage)
    print(json.dumps(script_config.json, indent=4, ensure_ascii=False))
    script_config.save(force=True)
    # path = "C:/nguyenpq/workspace/ChatBot/Common/TMTChatbot/StateController/scripts/templates/new_bill.json"
    # state_config_json = json.load(open(path, "r", encoding="utf8"))
    # state_config_json[OBJECT_ID] = "default"
    # state_config_json[STORAGE_ID] = "test"
    # state_config_json[NAME] = "StateActionConfig_test"
    # state_action_config = StateActionConfig.from_json(data=state_config_json, storage=_storage)
    # state_action_config.save(force=True)

    # LOAD FROM DB

    state_action_config_ = StateActionConfig.default(storage=_storage)
    script_config_ = ScriptConfig.default(storage=_storage)
    print(json.dumps(script_config_.json, indent=4, ensure_ascii=False))
    # print(state_action_config_.json)
