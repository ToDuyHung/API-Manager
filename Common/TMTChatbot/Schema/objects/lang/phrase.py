import logging
from cached_property import cached_property
import numpy as np

from TMTChatbot.Schema.objects.lang.word import Word
from TMTChatbot.Schema.objects.lang.common.mapping_status import MappingSTT
from TMTChatbot.Schema.objects.lang.common.phrase_mask import PhraseMask
from TMTChatbot.Schema.objects.lang.common.common_phrases import POSITIONAL_WORDS, POSITIONAL_PRE_WORDS
from TMTChatbot.Schema.objects.lang.common.utils import *


class Phrase:
    def __init__(self, root_word: Word, update_multi_func=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.root_word = root_word
        self.parent = None
        self.references = []
        self.len = None
        self.child_indices = None
        self.children = set()
        self._words = None
        self.ner_tag = None
        self.ner_text = None
        self._knowledge_node = None
        self._knowledge_nodes = {}
        self.mapping_stt = MappingSTT.NEW
        self.update_multi_func = update_multi_func
        self.level = 0
        self._in_relation_scores = {}
        self._out_relation_scores = {}
        self.is_object = False

    @property
    def index(self):
        return self.root_word.index

    @property
    def energy(self):
        return sum(node.energy for node in self.knowledge_nodes)

    def add_energy(self, _energy):
        if _energy > self.energy:
            nodes = list(self._knowledge_nodes.keys())
            node_scores = np.array([self._knowledge_nodes[node] for node in nodes])
            node_scores = node_scores / np.sum(node_scores)
            for node, node_score in zip(nodes, node_scores):
                node.add_energy(_energy * node_score)

    def free_energy(self):
        for node in self._knowledge_nodes:
            node.free_energy()

    @property
    def in_relation_scores(self):
        return self._in_relation_scores

    @property
    def out_relation_scores(self):
        return self._out_relation_scores

    def set_in_relation_scores(self, relation, score):
        if relation.dst_node in self.knowledge_nodes:
            # self._knowledge_nodes[relation.dst_node] = score
            self._in_relation_scores[relation] = score

    def set_out_relation_scores(self, relation, score):
        if relation.src_node in self.knowledge_nodes:
            # self._knowledge_nodes[relation.src_node] = score
            self._out_relation_scores[relation] = score

    def set_cannot_mapped(self):
        self.mapping_stt = MappingSTT.IMPOSSIBLE

    def update_level(self, parent_level):
        self.level = parent_level + 1
        for child in self.children:
            child.update_level(self.level)

    @property
    def knowledge_nodes(self):
        return list(self._knowledge_nodes.keys())

    @property
    def knowledge_node_scores(self):
        return self._knowledge_nodes

    @property
    def out_relations_dict(self):
        output = {}
        for knowledge_node in self.knowledge_nodes:
            for relation_id, relation in knowledge_node.out_relations.items():
                output[relation_id] = relation
        return output

    @property
    def out_relations(self):
        return list(self.out_relations_dict.values())

    @property
    def in_relations_dict(self):
        output = {}
        for knowledge_node in self.knowledge_nodes:
            for relation_id, relation in knowledge_node.in_relations.items():
                output[relation_id] = relation
        return output

    @property
    def in_relations(self):
        return list(self.in_relations_dict.values())

    @property
    def best_match_knowledge_nodes(self):
        best_nodes = []
        best_score = 0
        for n in self.knowledge_nodes:
            if n.score > best_score:
                best_nodes = []
                best_score = n.score
            if n.score == best_score:
                best_nodes.append(n)
        if len(best_nodes) > 0:
            best_nodes = [n for n in best_nodes if n.name is not None]
        return best_nodes

    @property
    def best_match_knowledge_node(self):
        nodes = self.best_match_knowledge_nodes
        if len(nodes) > 0:
            return nodes[0]

    def get_best_match_node(self, threshold=0.9):
        node = self.best_match_knowledge_node
        if node is not None and node.score >= threshold:
            return node

    def update_internal_relation(self):
        if len(self.references) > 0:
            for r in self.references:
                for node in self.knowledge_nodes:
                    r.add_knowledge_candidate(node)

        if self.parent is not None:
            self.parent.transfer_knowledge_nodes_info(self, True)
        if len(self.children) > 0:
            for p in self.children:
                p.transfer_knowledge_nodes_info(self, False)

    def transfer_knowledge_nodes_info(self, phrase, upside):
        if self.update_multi_func is not None:
            self.update_multi_func(phrase, self, upside)
        else:
            self.logger.debug(f"{self.mask_text}: Cannot update due to None update function")

    def add_knowledge_candidate(self, node, score=None, with_update=True, is_object=False):
        if is_object:
            self.is_object = is_object
        if self.is_partially_mapped or self.is_mapped:
            return
        new = False
        if isinstance(node, list):
            if score is None:
                score = [1] * len(node)
            for n, s in zip(node, score):
                if n not in self._knowledge_nodes:
                    self._knowledge_nodes[n] = s
                    if not self.is_question_phrase:
                        # print(self, "UPDATE NEIGHBOUR", n)
                        n.update_neighbours()
                    n.add_phrase(self)
                    new = True
        elif node not in self._knowledge_nodes:
            if score is None:
                score = 1
            self._knowledge_nodes[node] = score
            if not self.is_question_phrase:
                # print(self, "UPDATE NEIGHBOUR", node)
                node.update_neighbours()
            node.add_phrase(self)
            new = True
        if new:
            if self.mapping_stt != MappingSTT.MAPPED and not with_update:
                self.mapping_stt = MappingSTT.PARTIALLY_MAPPED
            else:
                if len(self.knowledge_nodes) > 0:
                    self.mapping_stt = MappingSTT.MAPPED
            self.logger.debug(f"MAP NODE: {self} -> {[item.name for item in self._knowledge_nodes.keys()]}")
            if len(self.references) > 0:
                for r in self.references:
                    r.add_knowledge_candidate(node)
            if self.is_question_phrase and self.is_mapped:
                return
            if self.parent is not None and with_update:
                self.parent.wait_for_knowledge_nodes(self, True)
            if len(self.children) > 0:
                if with_update:
                    for p in self.children:
                        p.wait_for_knowledge_nodes(self, False)

    def wait_for_knowledge_nodes(self, phrase, upside):
        if not self.is_mapped:
            self.mapping_stt = MappingSTT.WAITING
            if self.update_multi_func is not None:
                self.update_multi_func(phrase, self, upside)
            else:
                self.logger.debug(f"{self.mask_text}: Cannot update due to None update function")
        else:
            self.logger.debug(f"{self.text} IS {self.mapping_stt}")

    def remove_knowledge_node(self, node):
        if isinstance(node, list):
            self.logger.debug(f"REMOVE KNODES {[n.name for n in node]}")
            for n in node:
                n.remove_phrase(self)
                if n in self._knowledge_nodes:
                    del self._knowledge_nodes[n]
        else:
            self.logger.debug(f"REMOVE KNODE {node.name}")
            node.remove_phrase(self)
            if node in self._knowledge_nodes:
                del self._knowledge_nodes[node]

    def keep_best_only(self):
        best_match_node = self.get_best_match_node()
        if best_match_node is not None:
            remove_nodes = [n for n in self.knowledge_nodes if n != best_match_node]
            self.remove_knowledge_node(remove_nodes)

    def get_other_child(self, current_child):
        question_child = None
        selected_child = None
        for child in self.children:
            if child != current_child:
                selected_child = child
                if child.is_question_phrase:
                    question_child = child
        if question_child is None:
            return selected_child
        return question_child

    @property
    def is_prd(self):
        return self.root_word.is_prd

    @property
    def is_pob(self):
        return self.root_word.is_pob

    @property
    def is_noun(self):
        return self.root_word.is_noun

    @property
    def is_nc(self):
        return self.root_word.is_nc

    @property
    def is_nmod(self):
        return self.root_word.is_nmod

    @property
    def is_verb(self):
        return self.root_word.is_verb

    @property
    def is_adj(self):
        return self.root_word.is_adj

    @cached_property
    def is_positional(self):
        if self.text in POSITIONAL_WORDS:
            return True

    @property
    def is_active(self):
        a_b = check_active_noun(self.free_words[-1].text)
        return a_b

    @property
    def is_belong_active(self):
        return check_belong_active_phrase(self.free_words[0].text)

    @property
    def is_partially_mapped(self):
        if self.is_mapped:
            return False
        if self.is_noun:
            return self.mapping_stt == MappingSTT.PARTIALLY_MAPPED
        for phrase in self.children:
            if not phrase.is_partially_mapped:
                return False
        return False

    @property
    def is_mapped(self):
        if self.is_noun:
            return self.mapping_stt in [MappingSTT.MAPPED, MappingSTT.IMPOSSIBLE]
        for phrase in self.children:
            if not phrase.is_mapped:
                return False
        return len(self.knowledge_nodes) > 0

    @property
    def is_waiting(self):
        return self.mapping_stt == MappingSTT.WAITING

    @property
    def before_word(self):
        output = self.words[0].before_word
        if output is None:
            return self.words[0]
        return output

    @property
    def next_word(self):
        output = self.words[-1].next_word
        if output is None:
            return self.words[-1]
        return output

    @cached_property
    def text(self):
        return " ".join([item.text for item in self.words])

    def get_words(self, node: Word, output=None):
        if output is None:
            output = {}
        if not node.is_joined:
            output[node.index] = node
        if node.is_leaf:
            return
        for child_node in node.children:
            self.get_words(child_node, output)

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def words(self):
        if self._words is None:
            child_words = {}
            self.get_words(self.root_word, child_words)
            child_words = list(child_words.values())
            child_words.sort(key=lambda w: w.index)
            self._words = child_words
        return self._words

    @cached_property
    def text_len(self):
        return len(self.text)

    def __len__(self):
        if self.len is None:
            self.len = len(self.words)
        return self.len

    def __repr__(self):
        words = self.words
        return self.mask + f"||\tLABEL\t: {self.ner_tag}\t||\tWITH_KN\t: {self.is_mapped} ||" \
                           f"\tIS_NOUN\t: {self.is_noun}\t||\tIS_QUESTION:\t{self.is_question_phrase} " \
               + " ".join([w.text for w in words])

    def __contains__(self, item):
        if self.child_indices is None:
            self.child_indices = {w.index for w in self.words}
        if isinstance(item, Phrase):
            return item.root_word.index in self.child_indices
        return item.index in self.child_indices

    @property
    def is_ner(self):
        return self.ner_tag is not None

    @property
    def free_words(self):
        free_words = []
        for w in self.words:
            if w.is_joined:
                continue
            is_free = True
            for child in self.children:
                if w in child:
                    is_free = False
                    break
            if is_free:
                free_words.append(w)
        free_words.sort(key=lambda item: item.index)
        return free_words

    @property
    def all_children(self):
        output = list(self.children) + self.free_words
        output.sort(key=lambda item: item.index)
        return output

    @property
    def is_pure_noun_phrase(self):
        for word in self.free_words:
            if not word.is_noun:
                return False
        return True

    @property
    def lower_phrases(self):
        if self.is_leaf:
            return []
        else:
            output = self.children
            for child in self.children:
                output += child.lower_phrases
            output = [item for item in output if not item.is_question_phrase]
        return output

    @property
    def start(self):
        return self.words[0].start

    @property
    def end(self):
        return self.words[-1].end

    @property
    def mask(self):
        return f"<MASK{self.index}>"

    @property
    def child_mask(self):
        if self.is_ner and "của" not in self.before_word.text:
            return f"của {self.mask}"
        else:
            return self.mask

    @property
    def is_question_phrase(self):
        is_question = len(self.free_words) > 0
        for w in self.free_words:
            if not w.is_question_word:
                is_question = False
                break
        if is_question:
            return True
        if self.is_verb and len(self.children) == 1 and self.children[0].is_question_phrase:
            return True
        return False

    def update_reference_phrase(self):
        if self.is_verb:
            if self.free_text.strip() in ["là"]:
                if len(self.top_phrases) == 2:
                    p1, p2 = self.top_phrases
                    p1.references.append(p2)
                    p2.references.append(p1)
                    self.logger.debug(f"REF PHRASE {p1.text} = {p2.text}")
                elif len(self.top_phrases) == 1 and self.parent is not None:
                    if self.parent.is_noun:
                        p2 = self.top_phrases[0]
                        p1 = self.parent
                        p1.references.append(p2)
                        p2.references.append(p1)
                        self.logger.debug(f"REF PHRASE {p1.text} = {p2.text}")
                    else:
                        p2 = self.top_phrases[0]
                        p1 = self
                        p1.references.append(p2)
                        p2.references.append(p1)
                        self.logger.debug(f"REF PHRASE {p1.text} = {p2.text}")
        elif self.is_noun:
            if self.is_prd:
                for child in self.children:
                    if child.is_pob or child.is_nmod:
                        self.references.append(child)
                        child.references.append(self)

    @property
    def top_phrases(self):
        return list(self.children)

    @property
    def all_phrases(self):
        return list(self.children) + [self]

    @property
    def mask_text(self):
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda item: item.index)
        if self.is_noun:
            return f"<MASK{self.index}> là " + " ".join([part.child_mask for part in parts])
        return " ".join([part.child_mask for part in parts])

    @staticmethod
    def post_process(_text):
        for item in ["của", "được", "là", "có", "ở", "bên", "phía", "đứng"]:
            dup_item = f"{item} {item}"
            while dup_item in _text:
                _text = _text.replace(dup_item, item)
        return " ".join(_text.split()).strip()

    def mask_sent(self, reverse=False, full=True):
        self.logger.debug(f"FREE WORDS {self.free_words}")
        self.logger.debug(f"TOP PHRASE {self.top_phrases}")
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda item: item.index)
        output = ""
        of = "của"
        if self.is_noun:
            offset = 1
            if self.is_mapped:
                begin = f"{self.knowledge_nodes[0].name} là"
            else:
                begin = "@A là"
            end = "@B"
        else:
            begin = "@A"
            # verb phrase has its main object standing at the beginning
            if isinstance(parts[0], Phrase):
                if parts[0].is_mapped:
                    begin = parts[0].knowledge_nodes[0].name
                parts = parts[1:]
            offset = 1
            end = "@B"
        for part in parts:
            if isinstance(part, Phrase):
                self.logger.debug("MASK SENT: " + str(part) + ">>>>>" + part.get_mask('@' + chr(ord('A') + offset),
                                                                                      full=full))
                self.logger.debug(
                    f"IS NOUN: {part.is_noun}|ISMAPPED: {part.is_mapped}|IS QUESTION: {part.is_question_phrase}")
                if (part.is_question_phrase and not part.is_mapped) or part.is_partially_mapped:
                    output += f" {part.get_mask('@' + chr(ord('A') + offset), full=full)}"
                    # print(part.text, '-> mask', part.get_mask('@' + chr(ord('A') + offset), full=full))
                    offset += 1
                elif part.is_mapped:
                    output += f" {part.knowledge_nodes[0].name}"
                    # print(part.text, '-> ', part.knowledge_nodes[0].name)
                else:
                    output += f" {part.text}"
                    # print(part.text, '-> is question', part.text, part.is_question_phrase)

            else:
                output += f" {part.child_mask}"
        output = f"{begin} {output}"

        # USED WHEN: input text is only a relation , not complete phrase
        if len(self.top_phrases) == 0:
            if self.is_belong_active:
                output = f"{output} {of} {end}"
            else:
                output = f"{output} {of} {end}"
        ################################################################

        output = self.post_process(output)
        if reverse:
            output = output.replace("@A", "@X")
            output = output.replace("@B", "@A")
            output = output.replace("@X", "@B")
        output = output.replace("@A", PhraseMask.SRC_MASK)
        output = output.replace("@B", PhraseMask.DST_MASK)
        self.logger.debug(f"OUTPUT {output}")
        return output

    def mask_sents(self, reverse=False, full=True):
        self.logger.debug(f"FREE WORDS {self.free_words}")
        self.logger.debug(f"TOP PHRASE {self.top_phrases}")
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda i: i.index)
        of = "của"
        if self.is_noun:
            offset = 1
            begins = ["@A là", "@A"]
            if self.is_mapped or self.is_partially_mapped:
                for knowledge_node in self.knowledge_nodes:
                    for alias in knowledge_node.aliases:
                        begins += [f"{alias} là", alias]
                        # begins += [f"{knowledge_node.name} là" for knowledge_node in self.knowledge_nodes] + \
                        #           [f"{knowledge_node.name}" for knowledge_node in self.knowledge_nodes]

            if self.is_object and parts[0] == self.root_word:
                parts = parts[1:]

            end = "@B"
        else:
            begins = ["@A"]
            # verb phrase has its main object standing at the beginning
            if isinstance(parts[0], Phrase):
                if parts[0].is_mapped or parts[0].is_partially_mapped:
                    begins += [knowledge_node.name for knowledge_node in parts[0].knowledge_nodes]
                parts = parts[1:]
            offset = 1
            end = "@B"
        outputs = [begins]
        for part in parts:
            if isinstance(part, Phrase):
                self.logger.debug("MASK SENT: " + str(part) + ">>>>>" + part.get_mask('@' + chr(ord('A') + offset),
                                                                                      full=full))
                self.logger.debug(
                    f"IS NOUN: {part.is_noun}|ISMAPPED: {part.is_mapped}|IS QUESTION: {part.is_question_phrase}")
                if (part.is_question_phrase and not part.is_mapped) or part.is_partially_mapped:
                    outputs.append([f" {part.get_mask('@' + chr(ord('A') + offset), full=full)}"])
                    # print(part.text, '-> mask', part.get_mask('@' + chr(ord('A') + offset), full=full))
                    offset += 1
                elif part.is_mapped:
                    outputs.append([f" {knowledge_node.name}" for knowledge_node in part.knowledge_nodes])
                    # print(part.text, '-> ', [knowledge_node.name for knowledge_node in part.knowledge_nodes])
                else:
                    done = False
                    for word in part.words:
                        if word.is_question_word:
                            outputs.append([f" {part.get_mask('@' + chr(ord('A') + offset), full=full)}"])
                            offset += 1
                            done = True
                            break
                    if not done:
                        outputs.append([f" {part.text}"])
                    # print(part.text, '-> is question', part.text, part.is_question_phrase)

            else:
                outputs.append([f" {part.child_mask}"])

        new_outputs = outputs[0]
        for items in outputs[1:]:
            current_paths = []
            for item in items:
                for old_item in new_outputs:
                    current_paths.append(f"{old_item} {item}")
            new_outputs = current_paths
        outputs = new_outputs
        # output = f"{begin} {output}"
        # USED WHEN: input text is only a relation , not complete phrase
        if len(self.top_phrases) == 0:
            if self.is_belong_active:
                outputs = [f"{output} {of} {end}" for output in outputs] + [f"{output} {end}" for output in outputs]
            else:
                outputs = [f"{output} {end}" for output in outputs]
        ################################################################
        new_outputs = []
        for output in outputs:
            output = self.post_process(output)
            if reverse:
                output = output.replace("@A", "@X")
                output = output.replace("@B", "@A")
                output = output.replace("@X", "@B")
            output = output.replace("@A", PhraseMask.SRC_MASK)
            output = output.replace("@B", PhraseMask.DST_MASK)
            self.logger.debug(f"OUTPUT {output}")
            new_outputs.append(output)
        return new_outputs

    def relation_text(self, full=True):
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda item: item.index)
        output = ""
        of = "của"
        if self.is_noun:
            offset = 1
            begin = ""
            end = ""
        else:
            begin = ""
            # verb phrase has its main object standing at the beginning
            if isinstance(parts[0], Phrase):
                parts = parts[1:]
            offset = 1
            end = ""
        for part in parts:
            if isinstance(part, Phrase):
                if (part.is_question_phrase and not part.is_mapped) or part.is_partially_mapped:
                    output += f" {part.get_mask('', full=full)}"
                    # output += f" {part.get_mask('@' + chr(ord('A') + offset), full=full)}"
                    offset += 1
                elif part.is_mapped:
                    output += f" {part.knowledge_nodes[0].name}"
                else:
                    output += f" {part.text}"
            else:
                output += f" {part.child_mask}"
        output = f"{begin} {output}"

        # USED WHEN: input text is only a relation , not complete phrase
        if len(self.top_phrases) == 0:
            if self.is_belong_active:
                output = f"{output} {of} {end}"
            else:
                output = f"{output} {of} {end}"
        ################################################################

        output = self.post_process(output)
        self.logger.debug(f"RELATION SENT {output}")
        return output

    def relation_texts(self, full=True):
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda i: i.index)
        of = "của"
        if self.is_noun:
            offset = 1
            begins = ["", parts[0].text]
            parts = parts[1:]
            end = ""
        else:
            begins = [""]
            # verb phrase has its main object standing at the beginning
            if isinstance(parts[0], Phrase):
                parts = parts[1:]
            offset = 1
            end = ""
        outputs = [begins]
        for part in parts:
            if isinstance(part, Phrase):
                if (part.is_question_phrase and not part.is_mapped) or part.is_partially_mapped:
                    outputs.append([f" {part.get_mask('', full=full)}", part.text])
                    # output += f" {part.get_mask('@' + chr(ord('A') + offset), full=full)}"
                    offset += 1
                elif part.is_mapped:
                    outputs.append([f" {knowledge_node.name}" for knowledge_node in part.knowledge_nodes])
                else:
                    outputs.append([f" {part.text}", f" {part.root_word.text}"])
            else:
                outputs.append([f" {part.child_mask}"])
        # output = f"{begin} {output}"
        new_outputs = outputs[0]
        for items in outputs[1:]:
            current_paths = []
            for item in items:
                for old_item in new_outputs:
                    current_paths.append(f"{old_item} {item}")
            new_outputs = current_paths
        outputs = new_outputs

        if len(self.top_phrases) == 0:
            if self.is_belong_active:
                outputs = [f"{output} {of} {end}" for output in outputs]
            else:
                outputs = [f"{output} {end}" for output in outputs]

        new_outputs = [self.post_process(output) for output in outputs]
        new_outputs = [item for item in new_outputs if len(item) > 0]

        # if len(new_outputs) > 0 and "có" in new_outputs:
        #     new_outputs = [item for item in new_outputs if item != "có"]
        self.logger.debug(f"RELATION SENT {new_outputs}")
        return new_outputs

    def phrase_to_candidates(self, reverse=False):
        output = []
        text = self.free_text
        if reverse:
            if self.is_active:
                src = PhraseMask.DST_MASK
                dst = PhraseMask.SRC_MASK
            else:
                src = PhraseMask.SRC_MASK
                dst = PhraseMask.DST_MASK
        else:
            if self.is_active:
                src = PhraseMask.SRC_MASK
                dst = PhraseMask.DST_MASK
            else:
                src = PhraseMask.DST_MASK
                dst = PhraseMask.SRC_MASK
        if self.is_noun:
            output.append(self.post_process(f"{src} có {text} là {dst}"))
            output.append(self.post_process(f"{dst} là {text} của {src}"))
            output.append(self.post_process(f"{text} của {src} là {dst}"))
        elif self.is_verb:
            if text in ["có", "với", "gần"]:
                output.append(self.post_process(f"{src} {text} {dst}"))
            elif self.free_words[-1].text in ["bởi", "cho"]:
                output.append(self.post_process(f"{src} được {text} {dst}"))
            elif self.free_words[0].text in ["thuộc"]:
                output.append(self.post_process(f"{src} {text} của {dst}"))
            else:
                if self.free_words[0].text in ["có"]:
                    output.append(self.post_process(f"{src} {text} là {dst}"))
                else:
                    output.append(self.post_process(f"{src} {text} {dst}"))
        elif self.is_positional:
            for pre_word in POSITIONAL_PRE_WORDS:
                output.append(self.post_process(f"{src} {pre_word} {text} {dst}"))
                output.append(self.post_process(f"{src} {pre_word} {text} của {dst}"))
        else:
            output.append(self.post_process(f"{src} {text} {dst}"))
        return output

    def get_question_node(self) -> Word:
        for w in self.words:
            if w.is_question_word:
                return w

    def drop_children(self):
        lower_phrases = self.lower_phrases
        self.children = set(phrase for phrase in self.children if phrase.is_question_phrase)
        return lower_phrases

    def lower_text(self):
        for word in self.free_words:
            word.text = word.text.lower()

    @cached_property
    def free_text(self):
        return " ".join([w.text for w in self.free_words])

    def breath_first_search(self, queue):
        parts = self.free_words + self.top_phrases
        parts.sort(key=lambda item: item.index)
        for part in parts:
            if isinstance(part, Word) or part.is_mapped:
                queue.put(part)
            else:
                part.breath_first_search(queue)

    def get_mask(self, mask, full):
        if full and self.is_question_phrase:
            output = ""
            for w in self.words:
                if w.is_question_word:
                    output += f" {w.get_question_mask(mask)}"
                else:
                    output += f" {w.text}"
            return output.strip()
        else:
            return mask

    @property
    def score(self):
        if len(self.knowledge_nodes) == 0:
            return 0
        return max([n.score for n in self.knowledge_nodes])
