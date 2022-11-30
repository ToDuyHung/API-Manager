import json
import string
import sys
from abc import ABC
import inspect

import numpy as np
from typing import List, Dict, Union, Set, Text
from datetime import datetime
import random

from TMTChatbot.Common.constants import *
from TMTChatbot.Common.common_keys import *
from TMTChatbot.Common.common_phrases import INTENSIVE_WORDS
from TMTChatbot.Common.utils.data_utils import check_data_type
from TMTChatbot.Common.utils.text_formater import TextFormatter
from TMTChatbot.Schema.common.data_types import DataType
from TMTChatbot.Schema.common.graph_types import NodeTypes, RelationTypes, PhraseMask
from TMTChatbot.Schema.common.product_types import BillStatus, ProductStatus, PaymentStatus, BankVerificationMethod
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Schema.common.billing_method import PaymentMethod, ShipMethod


class Node(BaseObject):
    def __init__(self, storage_id: str, index, name: str, storage=None, aliases=None, parent_class=None, schema=None,
                 score=0, update_func=None, schema_required=None, mentioned_times: List[int] = None,
                 image_urls: List[str] = None, image_features: List = None, parent_id: str = None,
                 children: List = None, **kwargs):
        super(Node, self).__init__(_id=index, storage=storage, schema=schema, parent_class=parent_class,
                                   schema_required=schema_required, storage_id=storage_id, **kwargs)
        name, data_type = check_data_type(name)
        self.name = name if name is None else str(name)
        self.data_type = data_type
        self.in_relations: Dict[str, Relation] = {}
        self.out_relations: Dict[str, Relation] = {}
        self.attribute_relations: Dict[str, Relation] = {}
        self.attribute_relations_mapping: Dict[str, List[str]] = {}
        self.in_relations_score: Dict[Relation, float] = {}
        self.out_relations_score: Dict[Relation, float] = {}
        self.attribute_relations_score: Dict[Relation, float] = {}
        self.type = NodeTypes.ENTITY
        self._aliases = aliases if aliases is not None else []
        self.children = children if children is not None else []
        self.parent_id = parent_id
        self.parent = None
        self.init_empty_attributes()

        self._score = score
        self.phrases = set()
        self.update_func = update_func
        self.updated = False
        self._energy = 0
        self._mentioned_times = mentioned_times if mentioned_times is not None else []
        self._image_urls = image_urls if image_urls is not None else []
        self._image_features = image_features if image_features is not None else []
        self.alias = None

    @property
    def parent_class(self):
        return self._parent_class

    @parent_class.setter
    def parent_class(self, _parent_class):
        self._parent_class = _parent_class
        self.schema = self.load_schema()
        self.init_empty_attributes()
        for child in self.children:
            child.parent_class = _parent_class

    @property
    def image_urls(self) -> List[str]:
        output = set(self._image_urls)
        for child in self.children:
            output = output.union(child.image_urls)
        return list(output)

    @image_urls.setter
    def image_urls(self, _image_urls):
        self._image_urls = _image_urls

    @property
    def image_features(self):
        return self._image_features

    @image_features.setter
    def image_features(self, _image_features):
        self._image_features = _image_features

    def pre_process_name(self, intensive_words: Union[List[str], Set[str]] = None):
        if intensive_words is None:
            intensive_words = INTENSIVE_WORDS
        name = f" {self.name} ".lower()
        for c in string.punctuation:
            name = name.replace(c, f" {c} ")
        name_word_set = set(name.split())
        for word in name_word_set.intersection(intensive_words):
            name = name.replace(f" {word} ", " ")
        while "  " in name:
            name = name.replace("  ", " ")
        return name.strip()

    @property
    def has_children(self):
        children = self.children
        return children is not None and len(children) > 1

    @classmethod
    def skip_fields(cls):
        return [NODE_IMAGE_FEATURES]

    @property
    def mentioned_times(self):
        return self._mentioned_times

    def get_mentioned_time(self, step=-1):
        if self._mentioned_times is None or len(self._mentioned_times) == 0 or -step - 1 >= len(self._mentioned_times):
            return 0
        return self._mentioned_times[step]

    def set_mentioned_time(self, _mentioned_time):
        self._mentioned_times.append(_mentioned_time)
        self._mentioned_times = self._mentioned_times[-5:]

    def init_empty_attributes(self):
        if self.schema is None:
            return
        for attribute_name in self.schema.json_attributes:
            self.set_attr(attr=attribute_name, value=None, force=False)

    @property
    def relations(self):
        return list(self.in_relations.values()) + list(self.out_relations.values())

    @property
    def all_out_relations(self):
        return list(self.out_relations.values()) + list(self.attribute_relations.values())

    @property
    def all_relations(self):
        return list(self.in_relations.values()) + list(self.out_relations.values()) + \
               list(self.attribute_relations.values())

    def add_in_relation(self, relation, score=0):
        self.in_relations_score[relation] = score

    def add_out_relation(self, relation, score=0):
        if relation in self.out_relations:
            self.out_relations_score[relation] = score
        else:
            self.attribute_relations_score[relation] = score

    @property
    def aliases(self):
        output = list(
            item
            for item in {*self._aliases, self.name, self.parent_class}
            if item is not None
        )
        if self.alias is not None:
            output.append(self.alias)
        return output

    @aliases.setter
    def aliases(self, _aliases):
        self._aliases = list(set(self._aliases + _aliases))

    @property
    def attribute_words(self):
        attrs = set()
        for r in self.attribute_relations.values():
            attrs = attrs.union(set(r.words))
        return attrs

    def get_json_attribute_by_schema(self, attribute_type=None, restrict=False):
        if attribute_type is None:
            attribute_type = inspect.getframeinfo(inspect.currentframe().f_back).function

        attributes = getattr(self.schema, attribute_type)
        if attributes is not None:
            output = dict()
            for attribute_name in attributes:
                output[attribute_name] = []
            for r in self.attribute_relations.values():
                if r.name not in output and not restrict:
                    output[r.name] = []
                if r.dst_node.name is not None and r.name in output:
                    output[r.name].append([r.dst_node.name, r.mentioned_time])
            for relation_name in output:
                if len(output[relation_name]) > 0:
                    output[relation_name].sort(key=lambda item: item[1])
                output[relation_name] = [item[0] for item in output[relation_name]]
            return output
        else:
            self.logger.warning(f"{attribute_type} not exist in {self.schema.__class__.__name__}")
            return {}

    @property
    def json_attributes(self):
        return self.get_json_attribute_by_schema()

    @property
    def energy(self):
        return self._energy

    def add_energy(self, _energy):
        if self._energy == 0:
            self._energy = 1
            out_relations = list(self.all_out_relations)
            out_scores = np.array([self.out_relations_score[relation]
                                   if relation in self.out_relations else self.attribute_relations_score[relation]
                                   for relation in out_relations])
            out_scores[out_scores < EPSILON] = 0
            out_scores = out_scores / max([np.sum(out_scores), 1e-9])
            for out_relation, out_score in zip(out_relations, out_scores):
                if out_score >= EPSILON:
                    out_relation.dst_node.add_energy(1)

            in_relations = list(self.in_relations.values())
            in_scores = np.array([self.in_relations_score[relation] for relation in in_relations])
            in_scores[in_scores < EPSILON] = 0
            in_scores = in_scores / max([np.sum(in_scores), 1e-9])
            for in_relation, in_score in zip(in_relations, in_scores):
                if in_score >= EPSILON:
                    in_relation.src_node.add_energy(1)

    def free_energy(self):
        if self._energy != 0:
            self._energy = 0
            for relation in list(self.out_relations.values()) + list(self.in_relations.values()):
                relation.dst_node.free_energy()
                relation.src_node.free_energy()

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, _score):
        self._score = max([_score, self._score])

    @property
    def is_mapped(self):
        return len(self.phrases) > 0

    def add_phrase(self, phrase):
        self.phrases.add(phrase)

    def remove_phrase(self, phrase):
        if phrase in self.phrases:
            self.phrases.remove(phrase)

    def update_neighbours(self):
        if self.update_func is not None:
            self.update_func(self)

    def has_attr_value(self, attr, value):
        values = self.get_attr(attr)
        if values is None or len(values) == 0:
            return False
        return value in values

    def get_attr(self, attr):
        attr_relation_ids = self.attribute_relations_mapping.get(attr, [])
        attr_relations = [self.attribute_relations[attr_relation_id] for attr_relation_id in attr_relation_ids]
        if len(attr_relations) > 0:
            attr_relations.sort(key=lambda rel: rel.mentioned_time)
            output = [attr_relation.dst_node.name for attr_relation in attr_relations]
            output = [item for item in output if item is not None]
            return output
            # if len(output) == 1:
            #     return output[0]
            # else:
            #     return ", ".join(output)

    def get_last_attr_value(self, attr):
        values = self.get_attr(attr)
        if isinstance(values, list) and len(values) > 0:
            return values[-1]

    def set_attr(self, attr: str, value: str = None, force=True):
        """
        Create (or modify if existed) a new attribute for the current object node
        :param force: if relation is force replace in this object's out_relations else add if not exists
        :param attr: attribute name
        :param value: value of this attribute
        :return: None
        """
        is_required = attr in self.schema.required_attributes
        attr_node = self.get_attr(attr)
        if attr_node is None or force:
            attr_node = ValueNode(index=self.generate_hash(f"{self.id}{attr}{value}"), prop_name=attr, name=value,
                                  storage_id=self.storage_id)
            if is_required:
                attr_relation = RequiredAttributeRelation(src_node=self, dst_node=attr_node, name=attr,
                                                          storage=self.storage, storage_id=self.storage_id)
            else:
                attr_relation = AttributeRelation(src_node=self, dst_node=attr_node, name=attr, storage=self.storage,
                                                  storage_id=self.storage_id)

            if force or attr_relation.id not in self.attribute_relations:
                self.attribute_relations[attr_relation.id] = attr_relation
                self.attribute_relations_score[attr_relation] = 0
                if attr_relation.name not in self.attribute_relations_mapping:
                    self.attribute_relations_mapping[attr_relation.name] = []
                if attr_relation.id not in self.attribute_relations_mapping[attr_relation.name]:
                    self.attribute_relations_mapping[attr_relation.name].append(attr_relation.id)
                    remove_attr_ids = []
                    if len(self.attribute_relations_mapping[attr_relation.name]) > 1:
                        for attr_relation_id in self.attribute_relations_mapping[attr_relation.name]:
                            if self.attribute_relations[attr_relation_id].dst_node.name is None:
                                remove_attr_ids.append(attr_relation_id)
                        for attr_relation_id in remove_attr_ids:
                            relation = self.attribute_relations[attr_relation_id]
                            del self.attribute_relations[attr_relation_id]
                            del self.attribute_relations_score[relation]
                            self.attribute_relations_mapping[relation.name].remove(attr_relation_id)

    def drop_attr(self, attr):
        attr_relation_ids = self.attribute_relations_mapping.get(attr, [])
        for attr_relation_id in attr_relation_ids:
            relation = self.attribute_relations[attr_relation_id]
            del relation.dst_node
            del relation
            del self.attribute_relations[attr_relation_id]
        self.attribute_relations_mapping[attr] = []

    def drop_last_attr(self, attr):
        attr_relation_ids = self.attribute_relations_mapping.get(attr, [])
        if attr_relation_ids:
            last_attr_relation_id = attr_relation_ids[-1]
            relation = self.attribute_relations[last_attr_relation_id]
            del relation.dst_node
            del relation
            del self.attribute_relations[last_attr_relation_id]
            self.attribute_relations_mapping[attr] = self.attribute_relations_mapping[attr][:-1]

    def drop_all_attributes(self):
        for attr_relation_id in list(self.attribute_relations):
            relation = self.attribute_relations[attr_relation_id]
            del relation.dst_node
            del relation
            del self.attribute_relations[attr_relation_id]
        for relation_name in self.attribute_relations_mapping:
            self.attribute_relations_mapping[relation_name] = []

    @property
    def missing_required_attributes(self) -> List[str]:
        output = {}
        for attribute_name in self.schema.required_attributes:
            output[attribute_name] = []
        for r in self.attribute_relations.values():
            if r.name not in output:
                continue
            if r.dst_node.name is not None:
                output[r.name].append([r.dst_node.name, r.mentioned_time])

        return [attribute_name for attribute_name in output if len(output[attribute_name]) == 0]

    def __repr__(self):
        return self.id

    @property
    def image_url(self):
        if isinstance(self, ValueNode) and self.data_type == DataType.IMAGE_URL:
            return self.name

    @property
    def original_image_urls(self):
        return self._image_urls

    @property
    def full_info(self):
        return self.name is not None

    def src_dst_relations(self, other, rel_type):
        joined_relations = set(self.out_relations).intersection(other.in_relations)
        joined_relations = [self.out_relations[r_id] for r_id in joined_relations]
        joined_relations = [item for item in joined_relations if item.name == rel_type]
        return joined_relations

    def remove_relation(self, relation):
        if relation.id in self.in_relations:
            del self.in_relations[relation]
        if relation.id in self.out_relations:
            del self.out_relations[relation]

    def create_relation(self, dst_node, rel_name):
        relation = Relation(src_node=self, dst_node=dst_node, name=rel_name, storage=self.storage,
                            storage_id=self.storage_id)
        relation.save(force=True)

    def get_children_by_attr(self, attr: str, value: str, children: List = None):
        if children is None:
            children = self.children
        children = [child for child in children if child.has_attr_value(attr, value)]
        return children

    @property
    def _json(self):
        return {
            NAME: self.name,
            NODE_ALIASES: self.aliases,
            NODE_DATA_TYPE: self.data_type.name,
            NODE_CLASS: self.class_name(),
            NODE_PARENT_CLASS: self.parent_class,
            NODE_ATTRIBUTES: self.json_attributes,
            MENTIONED_TIMES: self.mentioned_times,
            NODE_IMAGE_URLS: self._image_urls,
            ENABLE: self.is_enable,
            NODE_CHILDREN: self.children if self.children is None else [child.static_info for child in self.children],
            NODE_PARENT_ID: self.parent_id
        }

    @property
    def _all_data(self):
        return {
            NAME: self.name,
            NODE_ALIASES: self.aliases,
            NODE_DATA_TYPE: self.data_type.name,
            NODE_CLASS: self.class_name(),
            NODE_PARENT_CLASS: self.parent_class,
            NODE_ATTRIBUTES: self.json_attributes,
            NODE_IMAGE_URLS: self._image_urls,
            ENABLE: self.is_enable,
            NODE_CHILDREN: self.children if self.children is None else [child.all_data for child in self.children],
            NODE_PARENT_ID: self.parent_id
        }

    @staticmethod
    def get_class_by_type(object_class):
        return getattr(sys.modules[__name__], object_class)

    def update_children_attributes(self):
        for attribute in self.schema.variant_attributes:
            for child in self.children:
                attr_value = child.get_attr(attribute)
                if attr_value is not None and len(attr_value) > 0:
                    self.set_attr(attribute, attr_value[0], force=True)

    @classmethod
    def _from_json(cls, data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        node_class_name = data[NODE_CLASS]
        node_class = cls.get_class_by_type(node_class_name)
        data["index"] = data[OBJECT_ID]
        children = cls.get_json_value(data, NODE_CHILDREN, [])
        if NODE_CHILDREN in data:
            del data[NODE_CHILDREN]
        if children is not None and len(children) > 0:
            children = [Node.from_json(storage=storage, schema_required=schema_required, data=child, nodes=nodes)
                        for child in children]
        else:
            children = []

        node: Node = node_class(storage=storage,
                                schema_required=schema_required,
                                children=children,
                                **data)

        if node.parent_id is None:
            node.parent_id = node.id
        for child in children:
            child.parent = node
            child.parent_id = node.id
            child.schema = node.schema

        attributes = data.get(NODE_ATTRIBUTES, {})
        for attribute, values in attributes.items():
            if isinstance(values, list):
                value_set = set(values)
                if len(values) > len(value_set):
                    values = value_set
                for value in values:
                    node.set_attr(attribute, value, force=True)
            else:
                node.set_attr(attribute, values, force=True)
        node.update_children_attributes()
        return node

    @property
    def static_info(self):
        info = super().static_info
        info[MENTIONED_TIMES] = self.mentioned_times
        return info

    def save(self, force=False, field_methods=None):
        super().save(force=force, field_methods={NODE_CHILDREN: "addToSet"})
        [child.save(force=force, field_methods=field_methods) for child in self.children]


class ValueNode(Node):
    schema_required = False
    force_accept = False

    def __init__(self, storage_id, prop_name="attr", name=None, aliases=None, index=None, src_index=None, storage=None,
                 **kwargs):
        if index is None:
            index = f"{src_index}_{prop_name}_{name}"
        super(ValueNode, self).__init__(storage_id, index, name, aliases=aliases, storage=storage)
        self.type = NodeTypes.VALUE

    @property
    def aliases(self):
        aliases = super().aliases
        if self.name.isnumeric():
            aliases += [self.name[:3], self.name[:4], self.name[-3:], self.name[-4:]]
        aliases = list(set(aliases))
        return aliases

    @staticmethod
    def _from_json(data, storage=None, **kwargs):
        return ValueNode(index=data.get(OBJECT_ID),
                         prop_name=data.get(NAME),
                         aliases=data.get(NODE_ALIASES, []),
                         storage=storage,
                         storage_id=data[STORAGE_ID])


class Relation(BaseObject, ABC):
    schema_required = False

    def __init__(self, storage_id, src_node: Node, dst_node: Node, name: str, words=None, storage=None, index=None,
                 schema=None, sentences: List[str] = None, mentioned_time: float = None):
        self.src_node = src_node
        self.dst_node = dst_node
        if index is None:
            index = self.get_relation_id(self.src_node.id, self.dst_node.id, name)
        super(Relation, self).__init__(_id=index, storage=storage, schema=schema, storage_id=storage_id)
        self.name = name
        self.type = RelationTypes.REL
        if words is None:
            words = [self.name]
        else:
            words.append(self.name)
            words = list(set(words))
        self.words = words
        self.sentences = sentences if sentences is not None else {}
        self._p2p_scores = {}
        self._score = 0
        self.mentioned_time = 0

    @property
    def score(self):
        if self._score > EPSILON:
            return self.src_node.score * self._score
        else:
            return self._score

    @score.setter
    def score(self, _score):
        self._score = max([self._score, _score])
        self.dst_node.add_in_relation(self, self._score)
        self.src_node.add_out_relation(self, self._score)

    def set_phase_to_phrase_score(self, src_phrase, dst_phrase, score):
        r_index = f"{src_phrase.index}_{dst_phrase.index}"
        self._p2p_scores[r_index] = max([self._p2p_scores.get(r_index, 0), score])

    @property
    def relation_text(self):
        output = [item for item in self.sentences if self.sentences[item]]
        output = [item.replace(PhraseMask.SRC_MASK, "").replace(PhraseMask.DST_MASK, "").replace("  ", " ").strip()
                  for item in output]
        return output

    @property
    def sents_all_mask(self):
        original_sentences = [item for item in self.sentences if self.sentences[item]]
        output = [item for item in original_sentences]
        for item in original_sentences:
            if self.src_node.name is not None:
                output += [item.replace(PhraseMask.SRC_MASK, name) for name in self.src_node.aliases]
            if self.dst_node.name is not None:
                output += [item.replace(PhraseMask.DST_MASK, name).replace(PhraseMask.SRC_MASK, PhraseMask.DST_MASK)
                           for name in self.dst_node.aliases]
        return list(set(output))

    @property
    def is_filled(self):
        return self.dst_node.name is not None

    @property
    def read_only(self):
        output = self.src_node.read_only or self.dst_node.read_only
        return output

    @property
    def full_info(self):
        return self.src_node.full_info and self.dst_node.full_info

    @classmethod
    def get_relation_id(cls, src_node_id, dst_node_id, name):
        key = f"{src_node_id}-[{name}]->{dst_node_id}"
        return cls.generate_hash(key)

    def __repr__(self):
        return f"({self.src_node.id}) -[{self.name}: {self.type}]-> ({self.dst_node.id})"

    @property
    def _json(self):
        return {
            REL_SRC: self.src_node.id,
            REL_DST: self.dst_node.id,
            NAME: self.name,
            REL_TYPE: self.type.name,
            REL_WORDS: self.words,
            REL_CLASS: self.class_name(),
            REL_MENTIONED_TIME: self.mentioned_time
        }

    @staticmethod
    def get_class_by_type(object_class):
        return getattr(sys.modules[__name__], object_class)

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, graph_nodes: dict = None, **kwargs):
        relation_id = data.get(OBJECT_ID)
        rel_class_name = data[REL_CLASS]
        src_id = data[REL_SRC]
        dst_id = data[REL_DST]
        src_node = graph_nodes.get(src_id)
        dst_node = graph_nodes.get(dst_id)
        name = data[NAME]
        words = data.get(REL_WORDS, [])
        if src_node is None or dst_node is None:
            return

        if rel_class_name == Relation.__name__:
            relation = Relation(index=relation_id, src_node=src_node, dst_node=dst_node, name=name, words=words,
                                storage=storage, storage_id=data[STORAGE_ID])
        else:
            rel_class = Relation.get_class_by_type(rel_class_name)
            relation = rel_class(index=relation_id, src_node=src_node, dst_node=dst_node, relation_id=name, words=words,
                                 storage=storage, storage_id=data[STORAGE_ID])

        src_node.out_relations[relation.id] = relation
        dst_node.in_relations[relation.id] = relation
        return relation

    def detach(self):
        self.src_node.remove_relation(self)
        self.dst_node.remove_relation(self)

    def complete_end_nodes(self):
        src_node, dst_node = self.src_node, self.dst_node
        src_node.out_relations[self.id] = self
        src_node.out_relations_score[self] = 0
        dst_node.in_relations[self.id] = self
        dst_node.in_relations_score[self] = 0

    def save(self, force=False, field_methods=None):
        super().save(force=force)
        self.src_node.save(force=force)
        self.dst_node.save(force=force)


class AttributeRelation(Relation, ABC):
    force_accept = False

    def __init__(self, storage_id: str, src_node: Node, dst_node: Node, name: str, words=None, storage=None,
                 schema=None, sentences: List[str] = None, mentioned_time: float = None):
        super(AttributeRelation, self).__init__(storage_id, src_node, dst_node, name, words, storage=storage,
                                                schema=schema, sentences=sentences, mentioned_time=mentioned_time)
        self.type = RelationTypes.ATTR
        self.mentioned_time = mentioned_time if mentioned_time is not None else float(datetime.now().timestamp())


class RequiredAttributeRelation(AttributeRelation, ABC):

    def __init__(self, storage_id: str, src_node: Node, name: str, words=None, dst_node: Node = None, storage=None,
                 schema=None, sentences: List[str] = None, mentioned_time: float = None):
        dst_node = dst_node if dst_node is not None else ValueNode(src_index=src_node.id, prop_name=name,
                                                                   storage_id=storage_id)
        super(RequiredAttributeRelation, self).__init__(storage_id, src_node, dst_node, name, words, storage=storage,
                                                        schema=schema, sentences=sentences,
                                                        mentioned_time=mentioned_time)
        self.type = RelationTypes.R_ATTR


class OptionalAttributeRelation(AttributeRelation, ABC):
    def __init__(self, storage_id: str, src_node: Node, name: str, words=None, dst_node: Node = None, storage=None,
                 schema=None, sentences: List[str] = None):
        dst_node = dst_node if dst_node is not None else ValueNode(src_index=src_node.id, prop_name=name,
                                                                   storage_id=storage_id)
        super(OptionalAttributeRelation, self).__init__(storage_id, src_node, dst_node, name, words, storage=storage,
                                                        schema=schema, sentences=sentences)
        self.type = RelationTypes.O_ATTR


class Shop(Node):
    def __init__(self, storage_id: str, name: str = None, index=None, aliases=None, storage=None, schema=None,
                 parent_class=None, schema_required=None, bank_accounts: List[Dict] = None, branches: List[Dict] = None,
                 policies: List[Dict] = None, **kwargs):
        super(Shop, self).__init__(index=index, name=name, storage=storage, aliases=aliases, schema=schema,
                                   parent_class=parent_class, schema_required=schema_required, storage_id=storage_id)
        self.bank_accounts = [] if bank_accounts is None else [item if isinstance(item, BankAccount)
                                                               else BankAccount.from_json(item, storage=storage)
                                                               for item in bank_accounts]
        self.branches = [] if branches is None else [item if isinstance(item, ShopBranch)
                                                     else ShopBranch.from_json(item, storage=storage)
                                                     for item in branches]
        self.policies = [] if policies is None else [item if isinstance(item, Policy)
                                                     else Policy.from_json(item, storage=storage)
                                                     for item in policies]

    @property
    def shop_id(self):
        return self.id

    @property
    def shop_name(self):
        return self.name

    def add_product(self, product):
        self.create_relation(product, self.schema)

    def get_random_product(self, k=3):
        # TODO may traceback
        # products = self.storage.load_random(class_name=Product.class_name(), storage_id=self.storage_id, limit=k,
        #                                     conditions={NODE_IMAGE_URLS: {"$ne": None}})
        products = self.storage.load_random(class_name=Product.class_name(), storage_id=self.storage_id, limit=k)
        products = [Product.from_json(product_data, storage=self.storage) for product_data in products]
        return products

    @property
    def _json(self):
        json_data = super()._json
        json_data[BANK_ACCOUNTS] = [bank_account.static_info for bank_account in self.bank_accounts]
        json_data[SHOP_BRANCH] = [branch.static_info for branch in self.branches]
        json_data[POLICIES] = [policy.static_info for policy in self.policies]
        return json_data

    @property
    def _all_data(self):
        json_data = super()._all_data
        json_data[BANK_ACCOUNTS] = [bank_account.all_data for bank_account in self.bank_accounts]
        json_data[SHOP_BRANCH] = [branch.all_data for branch in self.branches]
        json_data[POLICIES] = [policy.all_data for policy in self.policies]
        return json_data

    def save(self, force=False, field_methods=None):
        super().save(force=force, field_methods=field_methods)
        [bank_account.save(force=force) for bank_account in self.bank_accounts]
        [branch.save(force=force) for branch in self.branches]
        [policy.save(force=force) for policy in self.policies]

    @classmethod
    def _from_json(cls, data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        for keyword, class_ in zip([BANK_ACCOUNTS, SHOP_BRANCH, POLICIES], [BankAccount, ShopBranch, Policy]):
            if keyword in data:
                objects = class_.get_json_value(data, keyword, [])
                objects = [class_.from_json(obj, storage=storage, nodes=nodes) for obj in objects]
                data[keyword] = objects

        bill = super()._from_json(data, storage=storage, schema_required=schema_required, nodes=nodes, **kwargs)
        return bill


class User(Node):
    def __init__(self, storage_id, index=None, name: str = "default", storage=None, aliases=None, schema=None,
                 parent_class=None, schema_required=None, **kwargs):
        super(User, self).__init__(index=index, name=name, storage=storage, aliases=aliases, schema=schema,
                                   parent_class=parent_class, schema_required=schema_required, storage_id=storage_id)
        self.read_only = False

    @property
    def favor(self):
        return

    @property
    def user_id(self):
        return self.id

    @property
    def user_name(self):
        output = self.get_last_attr_value(NAME)
        if output is None:
            output = self.name
        return output

    @property
    def gender(self):
        return self.get_last_attr_value(GENDER)

    @property
    def json_attributes(self):
        output = dict()
        for attribute_name in self.schema.json_attributes:
            output[attribute_name] = []
        for r in self.attribute_relations.values():
            if r.name not in output:
                output[r.name] = []
            if r.dst_node.name is not None:
                output[r.name].append([r.dst_node.name, r.mentioned_time])
        for relation_name in output:
            if len(output[relation_name]) > 0:
                output[relation_name].sort(key=lambda item: item[1])
            output[relation_name] = [item[0] for item in output[relation_name]][-3:]
        return output


class Product(Node):
    force_accept = False

    def __init__(self, storage_id: str, index=None, name: str = "product", storage=None, aliases=None,
                 schema=None, parent_class=None, schema_required=None, code: str = None,
                 mentioned_times: int = None, image_urls: List[str] = None, alias: str = None, parent_id: str = None,
                 children: List = None, price: float = None, current_price: float = None,
                 enable: bool = True, **kwargs):
        super(Product, self).__init__(index=index, name=name, storage=storage, aliases=aliases,
                                      parent_class=parent_class, schema=schema, schema_required=schema_required,
                                      storage_id=storage_id, mentioned_times=mentioned_times, image_urls=image_urls,
                                      children=children, parent_id=parent_id, enable=enable)
        self.code = code
        self.alias = alias if alias is not None else self.pre_process_name()
        self._price = price
        self._current_price = current_price

    @property
    def category(self):
        return self.parent_class

    @property
    def variant_attributes(self):
        return self.get_json_attribute_by_schema(restrict=True)

    @property
    def info_schema(self):
        json_attr = {
            attr: self.get_last_attr_value(attr)
            for attr in self.schema.variant_attributes
        }
        json_attr = {
            attr: value
            for attr, value in json_attr.items() if value
        }
        return {NAME: self.name, **json_attr}

    @property
    def required_attributes(self):
        return self.get_json_attribute_by_schema(restrict=True)

    @property
    def is_unique(self):
        return len(self.children) == 1

    @classmethod
    def skip_fields(cls):
        return [NODE_IMAGE_FEATURES]

    @property
    def image_url(self):
        if len(self.image_urls) > 0:
            return self.image_urls[0]
        else:
            return ""

    @property
    def image_description(self):
        return f"* image {self.image_url} * {self.name}"

    @property
    def product_id(self):
        return self.id

    @property
    def discount(self):
        if self.price != 0:
            return (self.current_price - self.price) / self.price
        else:
            return 0

    @property
    def current_price(self):
        if self._current_price is not None:
            return self._current_price
        return self.price

    @property
    def price(self):
        if self._price is not None:
            return self._price
        return 100000

    @property
    def original_price(self):
        # TODO how to get price of this product
        return self.price

    @property
    def current_price_text(self):
        return TextFormatter.format_money(self.current_price)

    @property
    def price_text(self):
        return TextFormatter.format_money(self.price)

    @property
    def original_price_text(self):
        return TextFormatter.format_money(self.original_price)

    @property
    def _json(self):
        _json_data = super()._json
        _json_data[CODE] = self.code
        _json_data[NODE_ALIAS] = self.alias
        _json_data[PRODUCT_PRICE] = self._price
        _json_data[PRODUCT_CURRENT_PRICE] = self._current_price
        return _json_data

    @property
    def _all_data(self):
        _json_data = super()._all_data
        _json_data[CODE] = self.code
        _json_data[NODE_ALIAS] = self.alias
        _json_data[PRODUCT_PRICE] = self._price
        _json_data[PRODUCT_CURRENT_PRICE] = self._current_price
        return _json_data

    @classmethod
    def default(cls, storage=None, storage_id: str = None, parent_class: str = "Shirt"):
        return Product.from_json({
            CLASS: Product.class_name(),
            STORAGE_ID: storage_id,
            NAME: f"default_{Product.class_name()}",
            PARENT_CLASS: parent_class,
            OBJECT_ID: f"default_{Product.class_name()}"
        }, storage=storage)

    @classmethod
    def defaults(cls, storage=None, storage_id: str = None):
        return [cls.default(storage=storage, storage_id=storage_id, parent_class="Shirt"),
                cls.default(storage=storage, storage_id=storage_id, parent_class="Pants")]

    def get_user_attribute_with_product(self, attribute):
        return f"{attribute}"#_{self.parent_class}"

class VariantProduct(Product):
    pass


class BillProduct(Product):

    def __init__(self, storage_id: str, index=None, name: str = "product", storage=None, aliases=None, schema=None,
                 parent_class=None, number: int = None, schema_required=None, code: str = None,
                 status: str = ProductStatus.NONE, image_urls: List[str] = None, price: float = None,
                 parent_id: str = None, children: List = None, selected_children: List = None, **kwargs):
        """
        Implement for one product -> only one variant is chosen
        current_variant stands for what user choose
        self: current parent product -> use incase user change variant -> choose the most appropriate variant for user
        """
        super(BillProduct, self).__init__(index=index, name=name, storage=storage, aliases=aliases,
                                          parent_class=parent_class, schema=schema, schema_required=schema_required,
                                          storage_id=storage_id, code=code, image_urls=image_urls,
                                          parent_id=parent_id, children=children, price=price)
        self.number = number if number is not None else 1
        self.status = status
        self.selected_children = selected_children \
            if selected_children is not None else [child for child in self.children]

    @classmethod
    def schema_class_name(cls):
        return Product.class_name()

    @property
    def selected_child(self):
        if self.children is not None and len(self.children):
            return self.children[-1]
        return self

    @property
    def similar_variants(self):
        for key in self.schema.variant_attributes:
            pass
        # TODO find similar variants
        return

    @property
    def info_schema(self):
        # _info = super().info_schema
        child = self.selected_children[0] if self.selected_children else None
        _info = child.info_schema if child else super().info_schema
        _info[BILL_NUMBER_PRODUCTS] = str(self.number)
        return _info

    @property
    def multiple_value_attribute(self):
        # TODO just use variant attributes for selecting items
        # attrs = [key for key in self.attribute_relations_mapping
        attrs = [key for key in self.schema.variant_attributes
                 if key not in ["ảnh", "image", "image_url"]
                 and len(self.attribute_relations_mapping[key]) > 1]
        if len(attrs) > 0:
            attrs.sort()
            return attrs[0]

    @property
    def has_multiple_value_attributes(self):
        return self.multiple_value_attribute is not None

    def set_unique_attr(self, attr: str, value: str = None, force=True):
        if not value or value in self.get_attr(attr):
            self.drop_attr(attr)
            # TODO if user choose a value that make selected child empty -> ???????
            selected_children = self.get_children_by_attr(attr, value, self.selected_children or None)
            self.set_attr(attr, value, force)
            self.selected_children = selected_children

    def get_variant(self, keys_values):
        json_data = self.json
        variant: Product = Product.from_json(json_data)
        for key, value in keys_values.items():
            variant.drop_attr(key)
            variant.set_attr(key, value)
        return variant

    @property
    def confirmed(self):
        return self.status == ProductStatus.CONFIRMED

    @property
    def is_cared(self):
        return self.status == ProductStatus.CARE

    @property
    def is_canceled(self):
        return self.status == ProductStatus.CANCELED

    def care(self):
        if self.status != ProductStatus.CONFIRMED:
            self.status = ProductStatus.CARE

    def confirm(self):
        self.status = ProductStatus.CONFIRMED

    def cancel(self):
        self.status = ProductStatus.CANCELED

    @property
    def product_id(self):
        return self.id

    @property
    def _json(self):
        _json_data = super()._json
        _json_data[BILL_NUMBER_PRODUCTS] = self.number
        _json_data[BILL_STATUS] = self.status
        _json_data[BILL_SELECTED_CHILDREN] = self.selected_children \
            if self.selected_children is None \
            else [child.all_data for child in self.selected_children]
        return _json_data

    @property
    def _all_data(self):
        _json_data = super()._all_data
        _json_data[BILL_NUMBER_PRODUCTS] = self.number
        _json_data[BILL_STATUS] = self.status
        _json_data[BILL_SELECTED_CHILDREN] = self.selected_children \
            if self.selected_children is None \
            else [child.all_data for child in self.selected_children]
        return _json_data

    @classmethod
    def _from_json(cls, data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        selected_children = [Node.from_json(child, storage=storage, nodes=nodes)
                             for child in Node.get_json_value(data, BILL_SELECTED_CHILDREN, [])]
        data[BILL_SELECTED_CHILDREN] = selected_children
        return super()._from_json(data, storage=storage, nodes=nodes)

    @staticmethod
    def from_product(product: Product):
        product_data = product.json
        product_data[BILL_NUMBER_PRODUCTS] = 1
        product_data[CLASS] = BillProduct.class_name()
        output = BillProduct.from_json(product_data, storage=product.storage, schema_required=product.schema_required)
        return output


class BankAccount(Node):
    use_random_key = False

    def __init__(self, storage_id: str, name: str, shop_id: str, owner: str = None, bank: str = None,
                 index=None, storage=None, aliases=None, parent_class=None, schema=None, score=0, update_func=None,
                 schema_required=None, mentioned_times: List[int] = None,
                 verification_method: str = BankVerificationMethod.NONE, **kwargs):
        index = index if index is not None else self.generate_id(f"{self.class_name()}-{shop_id}-{owner}-{bank}-{name}")
        super(BankAccount, self).__init__(storage_id=storage_id, index=index, name=name, aliases=aliases,
                                          parent_class=parent_class, schema=schema, score=score,
                                          update_func=update_func, schema_required=schema_required,
                                          mentioned_times=mentioned_times, storage=storage)
        self.owner = owner
        self.bank = bank
        self.shop_id = shop_id
        self.verification_method = verification_method

    @property
    def info_schema(self):
        return {
            BANK_ACCOUNT_BANK: self.bank,
            BANK_ACCOUNT_OWNER: self.owner,
            BANK_ACCOUNT_NUMBER: self.name
        }

    @property
    def _json(self):
        json_data = super()._json
        json_data[BANK_ACCOUNT_OWNER] = self.owner
        json_data[BANK_ACCOUNT_BANK] = self.bank
        json_data[CONV_MESSAGE_SHOP_ID] = self.shop_id
        json_data[BANK_VERIFICATION_METHOD] = self.verification_method
        return json_data

    @property
    def _all_data(self):
        json_data = super()._all_data
        json_data[BANK_ACCOUNT_OWNER] = self.owner
        json_data[BANK_ACCOUNT_BANK] = self.bank
        json_data[CONV_MESSAGE_SHOP_ID] = self.shop_id
        json_data[BANK_VERIFICATION_METHOD] = self.verification_method
        return json_data

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, **kwargs):
        return Node._from_json(data=data, storage=storage, schema_required=schema_required, **kwargs)


class Bill(Node):
    def __init__(self, storage_id: str, user: User = None, shop: Shop = None, products: List[Dict] = None,
                 index=None, name: str = "bill", storage=None, aliases=None, parent_class="bill", schema=None,
                 schema_required=None, status: str = BillStatus.INIT, order_status: Text = "",
                 created_time: int = None, confirmed_time: int = None, code: Text = "",
                 payment_status: str = PaymentStatus.INIT,
                 bank_account: Dict = None, **kwargs):
        super(Bill, self).__init__(index=index, name=name, storage=storage, aliases=aliases, parent_class=parent_class,
                                   schema=schema, schema_required=schema_required, storage_id=storage_id)
        self._read_only = False
        if isinstance(user, dict):
            user = User.from_json(user)
        self.user = user
        if isinstance(shop, dict):
            shop = Shop.from_json(shop)
        self.shop = shop

        # bank_account_: BankAccount = None if bank_account is None else BankAccount.from_json(bank_account,
        #                                                                                      storage=self.storage)
        # if bank_account_:
        #     self.set_attr(BILL_BANK_ACCOUNT, json.dumps(bank_account_.info_schema, indent=4, ensure_ascii=False))

        products = [
            BillProduct.from_json(product_data, storage=self.storage) for product_data in products
        ] if products is not None else []

        self._products = {product.id: product for product in products}
        self.status = status
        self.order_status = order_status
        self.code = code  # Note: mã vận đơn
        self.confirmed_time = confirmed_time
        self.created_time = created_time if created_time is not None else int(datetime.now().timestamp())
        self.payment_status = payment_status

    @property
    def confirmed(self):
        return self.status == BillStatus.CONFIRMED

    @property
    def is_processing(self):
        return self.status == BillStatus.PROCESSING

    def processing(self):
        self.status = BillStatus.PROCESSING

    def confirm(self):
        self.confirmed_time = int(datetime.now().timestamp())
        self.status = BillStatus.CONFIRMED

    def cancel(self):
        self.status = BillStatus.CANCELED

    @property
    def aliases(self):
        aliases = super(Bill, self).aliases
        confirmed_date_str = (
            datetime
            .fromtimestamp(self.confirmed_time)
            .strftime('%d / %m / %Y') if self.confirmed_time else ""
        )
        return list({*aliases, self.code, f"{confirmed_date_str}"})

    @property
    def is_empty(self):
        return len(self.products) == 0

    @property
    def default_receiving_method(self):
        return ShipMethod.DIRECTLY if self.get_attr(BILL_RECEIVE_SHOWROOM) else ShipMethod.SHIP

    @property
    def default_payment_method(self):
        return PaymentMethod.COD

    @property
    def default_address(self):
        return "{User@address}" if (self.user is None or self.user.get_attr("address") == []) else \
            self.user.get_attr("address")[-1]

    @property
    def default_phone_number(self):
        return "{User@phone_number}" if (self.user is None or self.user.get_attr("phone_number") == []) \
            else self.user.get_attr("phone_number")[-1]

    @property
    def default_receiving_time(self):
        return "default"

    def get_default_value(self, value):
        func_name = f"default_{value}"
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            return func
        else:
            return None

    @property
    def attributes_info_schema(self):
        output = {}
        for key in self.schema.attributes:
            value = self.get_last_attr_value(key)
            if value is not None:
                if isinstance(value, BankAccount):
                    value = value.info_schema
                output[key] = value
            else:
                output[key] = self.get_default_value(key)
        return output

    @property
    def info_schema(self):
        # bill_products = [{NAME: product.name, BILL_NUMBER_PRODUCTS: product.number, **product.json_attributes}
        #                  for product in self.products if product.confirmed]
        bill_products = [product.info_schema for product in self.products if product.confirmed]
        output = {
            BILL_USER: "{User@name}" if self.user is None else self.user.name,
            BILL_SHOP: "{Shop@name}" if self.shop is None else self.shop.name,
            BILL_PRODUCTS: bill_products,
            BILL_STATUS: self.status,
            BILL_ORDER_STATUS: self.order_status,
            BILL_CREATED_TIME: str(datetime.fromtimestamp(self.created_time)),
            BILL_CONFIRMED_TIME: str(datetime.fromtimestamp(self.created_time)),
            BILL_PRICE: self.price,
            BILL_PAYMENT_STATUS: self.payment_status,
            # BILL_BANK_ACCOUNT: None
            # if self.bank_account is None or self.receiving_showroom else self.bank_account.info_schema
            BILL_CODE: self.code
        }
        return {**output, **self.attributes_info_schema}

    @property
    def products(self):
        return list(self._products.values())

    @products.setter
    def products(self, _products):
        self._products = {product.id: product for product in _products}

    @property
    def confirmed_products(self) -> List[BillProduct]:
        return [p for p in self.products if p.confirmed]

    @property
    def price(self):
        return sum([product.current_price for product in self.confirmed_products])

    @staticmethod
    def _from_json(data, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        bill = super()._from_json(data=data, storage=storage, schema_required=schema_required, nodes=nodes, **kwargs)
        products_data = data.get(BILL_PRODUCTS, [])

        products = [
            BillProduct.from_json(data=product_data, storage=storage, schema_required=schema_required, nodes=nodes)
            for product_data in products_data
        ]

        bill.products = products
        user_data = data.get(BILL_USER)
        if user_data is not None:
            user = User.from_json(user_data, nodes=nodes)
            bill.user = user
        shop_data = data.get(BILL_SHOP)
        if shop_data is not None:
            shop = Shop.from_json(shop_data, nodes=nodes)
            bill.shop = shop
        return bill

    @property
    def _json(self):
        json_data = super()._json
        json_data[BILL_USER] = self.user.static_info if self.user is not None else None
        json_data[BILL_SHOP] = self.shop.static_info if self.shop is not None else None
        json_data[BILL_PRODUCTS] = [product.json for product in self.products]
        json_data[BILL_PRICE] = self.price
        json_data[BILL_STATUS] = self.status
        json_data[BILL_ORDER_STATUS] = self.order_status
        json_data[BILL_CREATED_TIME] = self.created_time
        json_data[BILL_CONFIRMED_TIME] = self.confirmed_time
        json_data[BILL_PAYMENT_STATUS] = self.payment_status
        # json_data[BILL_BANK_ACCOUNT] = None if self.bank_account is None else self.bank_account.static_info
        json_data[BILL_CODE] = self.code
        return json_data

    @property
    def _all_data(self):
        json_data = super()._all_data
        json_data[BILL_USER] = self.user.all_data if self.user is not None else None
        json_data[BILL_SHOP] = self.shop.all_data if self.shop is not None else None
        json_data[BILL_PRODUCTS] = [product.all_data for product in self.products]
        json_data[BILL_PRICE] = self.price
        json_data[BILL_STATUS] = self.status
        json_data[BILL_ORDER_STATUS] = self.order_status
        json_data[BILL_CREATED_TIME] = self.created_time
        json_data[BILL_CONFIRMED_TIME] = self.confirmed_time
        json_data[BILL_PAYMENT_STATUS] = self.payment_status
        # json_data[BILL_BANK_ACCOUNT] = None if self.bank_account is None else self.bank_account.json
        json_data[BILL_CODE] = self.code
        return json_data

    def add_product(self, product: BillProduct):
        if product.id not in self._products:
            self._products[product.id] = product
        self.processing()
        return self._products[product.id]

    def get_product(self, product: BillProduct):
        return self._products.get(product.id)

    def save(self, force=False, field_methods=None):
        super().save(force=force, field_methods=field_methods)

    @property
    def required_attributes(self):
        return self.schema.required_attributes

    @property
    def attributes(self):
        return self.schema.attributes

    @property
    def variant_attributes(self):
        return self.schema.variant_attributes

    @property
    def missing_required_infor(self) -> List[str]:
        output_infor = []
        required_information = self.required_attributes
        for value in required_information:
            if not self.get_last_attr_value(value):
                output_infor.append(value)
        return output_infor

    @property
    def missing_attributes(self) -> List[str]:
        output_infor = []
        for value in self.attributes:
            if not self.get_last_attr_value(value):
                output_infor.append(value)
        return output_infor

    @property
    def sub_total_cost(self):
        return sum([product.price for product in self.confirmed_products])

    @property
    def total_cost(self):
        return self.price

    @property
    def payment(self):
        _payment = self.get_last_attr_value(BILL_PAYMENT)
        _payment = int(_payment) if _payment else 0
        return _payment

    @property
    def payment_text(self):
        return TextFormatter.format_money(self.payment)

    @property
    def remain_payment(self):
        _payment = self.payment
        return max(0, self.price - _payment)

    @property
    def remain_payment_text(self):
        return TextFormatter.format_money(self.remain_payment)


class Weather(Node):
    def __init__(self, storage_id: str, name: str = "weather", index=None, aliases=None, storage=None, schema=None,
                 parent_class=None, schema_required=None, created_time: int = None, location: str = None,
                 date: str = None, **kwargs):
        super(Weather, self).__init__(index=index, name=name, storage=storage, aliases=aliases,
                                      parent_class=parent_class, schema=schema, schema_required=schema_required,
                                      storage_id=storage_id)
        self.read_only = False
        self.created_time = created_time if created_time is not None else int(datetime.now().timestamp())
        self.location = location
        self.date = date

    @property
    def _json(self):
        json_data = super()._json
        json_data[LOCATION] = self.location
        json_data[DATE] = self.date
        return json_data


class ShopBranch(Node):
    def __init__(self, storage_id: str, name: str, address: str, phone_number: str, working_time: List[str],
                 index=None, aliases=None, storage=None, schema=None,
                 parent_class=None, schema_required=None, main_branch: bool = False, **kwargs):
        index = index if index is not None else self.generate_id(f"{self.class_name()}-{name}-{address}-{phone_number}")
        super(ShopBranch, self).__init__(index=index, name=name, storage=storage, aliases=aliases,
                                         parent_class=parent_class, schema=schema, schema_required=schema_required,
                                         storage_id=storage_id)
        self.address = address
        self.phone_number = phone_number
        self.working_time = working_time
        self.main_branch = main_branch

    @property
    def _json(self):
        json_data = super()._json
        json_data[BRANCH_ADDRESS] = self.address
        json_data[BRANCH_PHONE_NUMBER] = self.phone_number
        json_data[BRANCH_WORKING_TIME] = self.working_time
        json_data[MAIN_BRANCH] = self.main_branch
        return json_data

    @property
    def _all_data(self):
        json_data = super()._json
        json_data[BRANCH_ADDRESS] = self.address
        json_data[BRANCH_PHONE_NUMBER] = self.phone_number
        json_data[BRANCH_WORKING_TIME] = self.working_time
        json_data[MAIN_BRANCH] = self.main_branch
        return json_data


class Policy(Node):
    def __init__(self, storage_id: str, name: str, index=None, aliases=None, storage=None, schema=None,
                 parent_class=None, schema_required=None, **kwargs):
        super(Policy, self).__init__(index=index, name=name, storage=storage, aliases=aliases,
                                     parent_class=parent_class, schema=schema, schema_required=schema_required,
                                     storage_id=storage_id)
