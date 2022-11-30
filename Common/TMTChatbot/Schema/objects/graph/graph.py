from abc import ABC
from typing import List, Dict
from rank_bm25 import BM25Okapi
from datetime import datetime

from TMTChatbot.Common.common_keys import *
from TMTChatbot.Schema.objects.base_object import BaseObject
from TMTChatbot.Schema.objects.graph.graph_data import Node, Relation, User, Shop, Bill, Weather
from TMTChatbot.Common.utils.data_utils import jaccard_distance, text_ngram, normalize_text, remove_accents
from TMTChatbot.Schema.common.product_types import BillStatus


class Graph(BaseObject, ABC):
    schema_required = False

    def __init__(self, storage_id, nodes: [Node], storage=None):
        super(Graph, self).__init__(_id="GRAPH", storage=storage, storage_id=storage_id)
        self.nodes = {node.id: node for node in nodes}
        self.node_index = None
        self.node_id_mapping = None
        self._attribute_syllable_score = None
        self.node_name_index()

    def node_name_index(self):
        node_id_mapping = []
        node_names = []
        for node_id, node in self.nodes.items():
            for node_name in node.aliases:
                node_names.append(node_name)
                node_id_mapping.append(node_id)
        self.node_id_mapping = node_id_mapping
        tokenized_corpus = [text_ngram(node_name, n=3, c_mode=True) for node_name in node_names]
        self.node_index = BM25Okapi(tokenized_corpus)
        self._attribute_syllable_score = None

    def get_previous_node(self, candidates: List[Node] = None, mentioned_time_range: float = None,
                          node_class: str = None, return_latest: bool = True, k: int = None):
        if candidates is None or len(candidates) == 0:
            candidates = [node for node in self.nodes.values() if
                          (node_class is None or (node_class is not None and node.class_name() == node_class)) and
                          (mentioned_time_range is None or node.get_mentioned_time(-1) >= mentioned_time_range)]

        if return_latest or k is None:
            max_time = 0
            new_candidates = []
            for node in candidates:
                node_mention_time = node.get_mentioned_time(-1)
                if node_mention_time > max_time:
                    max_time = node_mention_time
                    new_candidates = []
                if node_mention_time == max_time:
                    new_candidates.append(node)
            candidates = new_candidates
        else:
            last_candidates = candidates
            for step in range(-4, -1, 1):
                max_time = 0
                new_candidates = []
                for node in candidates:
                    node_mention_time = node.get_mentioned_time(step)
                    if node_mention_time > max_time:
                        max_time = node_mention_time
                        new_candidates = []
                    if node_mention_time == max_time:
                        new_candidates.append(node)
                if 0 < len(new_candidates) <= len(candidates):
                    candidates = new_candidates
                if len(candidates) <= k:
                    break
                else:
                    last_candidates = candidates
            candidates = last_candidates
        # if max_time is not None:
        #     if mentioned_time_range is None or \
        #         (mentioned_time_range is not None and max_time >= mentioned_time_range):
        #         return candidates
        return candidates

    def get_node_by_id(self, node_id) -> Node:
        return self.nodes.get(node_id)

    def get_node_by_name(self, node_name) -> List[Node]:
        """
        Retrieve node by its name
        :param node_name: name of the query node
        :return: List of nodes with node.name = <node_name>
        """
        nodes: List[Node] = self.get_node_info([node_name], return_score=False)
        nodes = [node for node in nodes if node.name == node_name]
        return nodes

    @property
    def relations(self) -> List[Relation]:
        relations = set()
        for node in self.nodes.values():
            relations = relations.union(node.relations)
        return list(relations)

    @property
    def all_relations(self) -> List[Relation]:
        relations = set()
        for node in self.nodes.values():
            relations = relations.union(node.all_relations)
        return list(relations)

    def __repr__(self):
        return "GRAPH"

    @staticmethod
    def node_filter(candidates, nodes: List[Node], re_scoring_terms: Dict[str, float]):
        candidates_q_n_grams = [text_ngram(text, n=1, c_mode=False) for text in candidates]
        node_scores = []
        for node in nodes:
            node_score = []
            for query_n_grams in candidates_q_n_grams:
                node_score += [jaccard_distance(query_n_grams, text_ngram(node_name, n=1, c_mode=False),
                                                return_num=True, re_scoring_terms=re_scoring_terms)
                               for node_name in node.aliases]
            node_scores.append(max(node_score))
        max_score = max(node_scores)
        if max_score < 0.2:
            return []
        min_score = max_score * 0.8
        output = []
        for node_score, node in zip(node_scores, nodes):
            if node_score >= min_score:
                node.score = node_score
                output.append((node, node_score))
        return output

    def get_node_info(self, candidates, return_score=False) -> List[Node] or (List[Node], List[float]):
        node_ids = []
        for text in candidates:
            tokenized_query = text_ngram(text, n=3, c_mode=True)
            node_ids += self.node_index.get_top_n(tokenized_query, self.node_id_mapping, n=20)
        _nodes = list({self.nodes[node_id] for node_id in node_ids})
        nodes = self.node_filter(candidates, _nodes, self.attribute_syllable_score)
        if return_score:
            return nodes
        else:
            return [item[0] for item in nodes]

    @property
    def attribute_words(self):
        attributes = set()
        for node in self.nodes.values():
            attributes = attributes.union(node.attribute_words)
        return attributes

    @property
    def attribute_syllable_score(self):
        if self._attribute_syllable_score is None:
            output = {}
            for node in self.nodes.values():
                for word in node.attribute_words:
                    for item in text_ngram(word.replace("_", " "), n=3, c_mode=False):
                        if item not in output:
                            output[item] = {}
                        output[item]["attr"] = output[item].get("attr", 0) + 1
                for word in node.aliases:
                    for item in text_ngram(word.replace("_", " "), n=3, c_mode=False):
                        if item not in output:
                            output[item] = {}
                        output[item]["node"] = output[item].get("node", 0) + 1
            for item in output:
                output[item] = output[item].get("attr", 0) / \
                               max([(output[item].get("attr", 0) + output[item].get("node", 0)), 1])
            self._attribute_syllable_score = output
        return self._attribute_syllable_score

    @property
    def _json(self):
        return {
            NODES: [node.json for node in self.nodes.values()],
            RELATIONS: [relation.json for relation in self.relations],
            STORAGE_ID: self.storage_id
        }

    @property
    def all_data(self):
        return {
            NODES: [node.all_data for node in self.nodes.values()],
            RELATIONS: [relation.json for relation in self.relations],
            STORAGE_ID: self.storage_id
        }

    @property
    def static_info(self):
        return {
            NODES: [node.static_info for node in self.nodes.values()],
            RELATIONS: [relation.static_info for relation in self.relations],
            STORAGE_ID: self.storage_id
        }

    def add_node(self, node):
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self.node_name_index()
        return self.nodes[node.id]

    def add_nodes(self, nodes: List[Node], current_time: float = None) -> List[Node]:
        outputs = []
        new_node = False
        for node in nodes:
            if node.id not in self.nodes:
                self.nodes[node.id] = node
                new_node = True
            outputs.append(self.nodes[node.id])
        if new_node:
            self.node_name_index()

        if current_time is None:
            current_time = datetime.now().timestamp()

        for node in outputs:
            node.set_mentioned_time(current_time)
        return outputs

    def save(self, force=False, field_methods=None):
        [node.save(force=force) for node in self.nodes.values()]
        [relation.save(force=force) for relation in self.relations]


class SubGraph(Graph, ABC):
    def __init__(self, storage_id: str, nodes: [Node], user: User, shop: Shop, storage=None):
        super(SubGraph, self).__init__(nodes=nodes, storage=storage, storage_id=storage_id)
        self.user = user
        self.shop = shop
        if self.bill is None:
            self.init_bill()
        if self.weather is None:
            self.init_weather()
        self.add_node(self.bill)
        self.add_node(self.weather)

    @property
    def all_nodes(self):
        return self.nodes.values()

    @property
    def bills(self) -> List[Bill]:
        return [node for node in self.nodes.values() if node.class_name() == Bill.class_name()]

    @property
    def weathers(self) -> List[Weather]:
        return [node for node in self.nodes.values() if node.class_name() == Weather.class_name()]

    @property
    def confirmed_bills(self) -> List[Bill]:
        return [node for node in self.nodes.values() if node.class_name() == Bill.class_name()
                and node.status == BillStatus.CONFIRMED]

    @property
    def old_bills(self) -> List[Bill]:
        return [node for node in self.nodes.values() if node.class_name() == Bill.class_name()
                and node.status in [BillStatus.CONFIRMED, BillStatus.DONE]]

    @property
    def bill(self) -> Bill:
        bills = self.bills
        if len(bills) > 0:
            bills.sort(key=lambda bill: bill.created_time)
            return bills[-1]

    @property
    def weather(self) -> Weather:
        weathers = self.weathers
        if len(weathers) > 0:
            weathers.sort(key=lambda weather: weather.created_time)
            return weathers[0]

    def init_bill(self):
        """
        Add new bill object into User conversation
        This means a conversation will never end, user will have many bills
        The question now is of knowing which bills to used
        :return:
        """

        # TODO how to remove super old bills
        bill = Bill(storage_id=self.storage_id, user=self.user, shop=self.shop)
        self.add_node(bill)

    def init_weather(self):
        """
        Add new bill object into User conversation
        This means a conversation will never end, user will have many bills
        The question now is of knowing which bills to used
        :return:
        """
        weather = Weather(storage_id=self.storage_id, user=self.user, shop=self.shop)
        self.add_node(weather)

    def remove_node(self, node: Node):
        if node is not None and node.id in self.nodes:
            for relation in list(node.in_relations.values()) + list(node.out_relations.values()):
                relation.detach()
            del self.nodes[node.id]

    def remove_nodes(self, nodes: [Node]):
        for node in nodes:
            self.remove_node(node)

    def remove_all_nodes(self):
        self.remove_nodes([node for node in self.nodes.values() if node not in [self.user, self.shop]])

    def add_node(self, node):
        if node.id not in self.nodes:
            super().add_node(node)
            for node_id in self.nodes:
                if node_id == node.id:
                    continue
                self.load_pair_relations(node_id, node.id)

    def load_all_relations(self):
        if self.storage is None:
            return
        for src_id in self.nodes:
            for dst_id in self.nodes:
                if src_id == dst_id:
                    continue
                relation_data = self.storage.load_relations(src_id=src_id, dst_id=dst_id,
                                                            class_name=Relation.class_name(),
                                                            storage_id=self.storage_id)
                [Relation.from_json(data=data, storage=self.storage, graph_nodes=self.nodes) for data in relation_data]

    def load_pair_relations(self, src_id, dst_id):
        if self.storage is not None:
            relation_data = self.storage.load_relations(src_id=src_id, dst_id=dst_id,
                                                        class_name=Relation.class_name(),
                                                        storage_id=self.storage_id)
            [Relation.from_json(data=data, storage=self.storage, graph_nodes=self.nodes) for data in relation_data]
            relation_data = self.storage.load_relations(src_id=dst_id, dst_id=src_id,
                                                        class_name=Relation.class_name(),
                                                        storage_id=self.storage_id)
            [Relation.from_json(data=data, storage=self.storage, graph_nodes=self.nodes) for data in relation_data]

    @staticmethod
    def _from_json(data: dict, storage=None, schema_required=None, nodes: dict = None, **kwargs):
        nodes_info = data.get(NODES, {})
        all_nodes = []
        user_node = None
        shop_node = None
        bill_nodes: List[Bill] = []
        for node_info in nodes_info:
            node = Node.from_json(node_info, storage=storage, schema_required=schema_required, nodes=nodes)
            all_nodes.append(node)
            if node.class_name() == User.class_name():
                user_node = node
            elif node.class_name() == Shop.class_name():
                shop_node = node
            if node.class_name() == Bill.class_name():
                bill_nodes.append(node)

        for node in bill_nodes:
            node.user = user_node
            node.shop = shop_node

        graph = SubGraph(nodes=all_nodes, user=user_node, shop=shop_node, storage=storage,
                         storage_id=data[STORAGE_ID])
        graph.load_all_relations()
        return graph
