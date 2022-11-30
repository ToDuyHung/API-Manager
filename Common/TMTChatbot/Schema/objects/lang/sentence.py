import logging

from queue import Queue

from TMTChatbot.Schema.objects.lang.common.sentence_types import SentenceTypes
from TMTChatbot.Schema.objects.lang.word import Word
from TMTChatbot.Schema.objects.lang.phrase import Phrase


class Sentence:
    def __init__(self, words: [Word], phrase_update_multi_func=None):
        self.logger = logging.getLogger(__class__.__name__)
        self.root = self.build_tree(words)
        self.words = words
        self.phrase_update_multi_func = phrase_update_multi_func
        self._noun_phrases = None
        self._verb_phrases = None
        self._question_word = None
        self.preprocess_words()
        self.phrase_root = self.build_phrase_tree()
        self._free_words = None

    def validate(self, candidate_phrases):
        if self.question_phrase is None or len(self.question_phrase.knowledge_nodes) == 0:
            return False, []
        mapped_candidate = []
        best_candidates = None
        for phrase in candidate_phrases:
            phrase.add_energy(1)
            if self.question_phrase.energy > 0:
                mapped_nodes = [node for node in self.question_phrase.knowledge_nodes if node.energy > 0]
                if len(mapped_nodes) > 0:
                    mapped_candidate.append(mapped_nodes)
                    if best_candidates is None or len(best_candidates) > len(mapped_nodes):
                        best_candidates = mapped_nodes
            phrase.free_energy()
        is_valid = len(mapped_candidate) >= len(candidate_phrases) * 0.9
        if is_valid:
            return True, best_candidates
        return False, []

    def preprocess_words(self):
        start = 0
        for w in self.words:
            w.start = start
            w.end = start + len(w)
            start = w.end + 1
            if w.is_question_word:
                self._question_word = w

    @property
    def noun_phrases(self):
        if self._noun_phrases is None:
            phrases = []
            for w in self.words:
                # if w.is_pronoun and w.is_question_word and w.parent.is_noun:
                #     continue
                if w.is_question_word or (w.is_noun and (not w.is_joined or w.is_question_word)) or w.is_unk:
                    phrase = Phrase(w, self.phrase_update_multi_func)
                    if len(phrase.words) > 0:
                        phrases.append(phrase)
            self._noun_phrases = phrases
        return self._noun_phrases

    @property
    def reversed_sorted_noun_phrases(self):
        noun_phrases = [p for p in self.noun_phrases]
        noun_phrases.sort(key=lambda n: n.level, reverse=True)
        return noun_phrases

    @property
    def sorted_noun_phrases(self):
        noun_phrases = [p for p in self.noun_phrases]
        noun_phrases.sort(key=lambda n: n.level, reverse=False)
        return noun_phrases

    @property
    def verb_phrases(self) -> [Phrase]:
        if self._verb_phrases is None:
            phrases = []
            for w in self.words:
                if w.is_verb:
                    phrases.append(Phrase(w, self.phrase_update_multi_func))
            self._verb_phrases = phrases
        return self._verb_phrases

    @property
    def phrases(self) -> [Phrase]:
        return self.verb_phrases + self.noun_phrases

    @property
    def waiting_noun_phrases(self):
        return [phrase for phrase in self.noun_phrases if phrase.is_waiting]

    @property
    def text(self):
        return " ".join([item.text for item in self.words])

    @staticmethod
    def build_tree(words) -> Word or None:
        def get_root_node(_words: [Word]) -> Word:
            for word in _words:
                if word.head_id == 0:
                    return word

        for i in range(len(words)):
            if i > 0:
                words[i].before_word = words[i - 1]
            if i < len(words) - 1:
                words[i].next_word = words[i + 1]
        root = get_root_node(words)
        if root is None:
            return

        for i in range(len(words) - 1):
            node = words[i]
            for j in range(i + 1, len(words)):
                candidate = words[j]
                if not candidate.is_question_word and node.index == candidate.index - 1 \
                        and candidate.head_id == node.index \
                        and ((node.is_noun and candidate.is_pronoun and candidate.is_nmod)
                             or (node.is_nc and candidate.is_nmod)
                             or (node.is_noun and candidate.is_unk)):
                    node.join(candidate)

        for node in words:
            for candidate in words:
                if candidate.head_id == node.index:
                    node.children.append(candidate)
                    candidate.parent = node
        return root

    def _depth_first_search(self, node: Word):
        for child in node.children:
            self._depth_first_search(child)

    def depth_first_search(self):
        self._depth_first_search(self.root)

    def build_phrase_tree(self):
        for i, phrase_i in enumerate(self.phrases):
            for j, phrase_j in enumerate(self.phrases):
                if i == j:
                    continue
                if phrase_i in phrase_j:
                    if phrase_i.parent is None or phrase_j in phrase_i.parent:
                        phrase_i.parent = phrase_j

        for i, phrase_i in enumerate(self.phrases):
            for j, phrase_j in enumerate(self.phrases):
                if phrase_i == phrase_j.parent and phrase_j not in phrase_i.children:
                    phrase_i.children.add(phrase_j)

        # DROP VERB PHRASE #######################################################
        done = False
        while not done:
            verb_phrases = self.verb_phrases
            remove_phrases = []
            for i, phrase_i in enumerate(verb_phrases):
                for j, phrase_j in enumerate(verb_phrases):
                    if phrase_i == phrase_j.parent and phrase_i.index == phrase_j.index - 1:
                        phrase_i.children.remove(phrase_j)
                        for p in phrase_j.children:
                            if p not in phrase_i.children:
                                phrase_i.children.add(p)
                            p.parent = phrase_i
                            phrase_i.child_indices = None
                        remove_phrases.append(phrase_j)
            for p in remove_phrases:
                self._verb_phrases.remove(p)
            done = len(remove_phrases) == 0
        ##########################################################################

        # DROP NOUN PHRASE #######################################################
        done = False
        while not done:
            noun_phrases = self.noun_phrases
            remove_phrases = []
            for i, phrase_i in enumerate(noun_phrases):
                for j, phrase_j in enumerate(noun_phrases):
                    if not phrase_j.is_question_phrase:
                        if phrase_i == phrase_j.parent and phrase_i.index == phrase_j.index - 1:
                            if not phrase_j.is_prd:
                                phrase_i.children.remove(phrase_j)
                                for p in phrase_j.children:
                                    if p not in phrase_i.children:
                                        phrase_i.children.add(p)
                                    p.parent = phrase_i
                                    phrase_i.child_indices = None
                                remove_phrases.append(phrase_j)
                        elif phrase_j == phrase_i.parent and phrase_i.index == phrase_j.index - 1:
                            phrase_j.children.remove(phrase_i)
                            for p in phrase_i.children:
                                if p not in phrase_j.children:
                                    phrase_j.children.add(p)
                                p.parent = phrase_j
                                phrase_j.child_indices = None
                            remove_phrases.append(phrase_i)
            for p in remove_phrases:
                self._noun_phrases.remove(p)
            done = len(remove_phrases) == 0
        ##########################################################################
        root_phrase = None
        for phrase in self.phrases:
            phrase.update_reference_phrase()
            if phrase.parent is None:
                root_phrase = phrase
        if root_phrase is not None:
            root_phrase.update_level(0)
        return root_phrase

    @property
    def top_phrases(self):
        return [item for item in self.noun_phrases if item.parent is None]

    @property
    def question_word(self):
        return self._question_word

    @property
    def question_phrase(self):
        for phrase in self.noun_phrases:
            if phrase.is_question_phrase:
                return phrase

    def drop_phrases(self, phrases: [Phrase]):
        for phrase in phrases:
            if phrase in self.noun_phrases:
                self.noun_phrases.remove(phrase)

    def to_phrase(self) -> Phrase:
        root_phrase = Phrase(root_word=self.root)
        root_phrase.parent = None
        root_phrase.children = self.top_phrases
        root_phrase.references.append(self.question_phrase)
        for phrase in self.top_phrases:
            phrase.parent = root_phrase
        return root_phrase

    @property
    def ner_phrases(self):
        return [p for p in self.noun_phrases if p.is_ner]

    @property
    def is_all_mapped(self):
        for phrase in self.noun_phrases:
            if phrase.is_waiting:
                return False
        return True

    def breath_first_search(self):
        queue = Queue()
        head_phrase = self.phrase_root
        head_phrase.breath_first_search(queue)
        while not queue.empty():
            node = queue.get()
            if isinstance(node, Phrase) and node.is_mapped:
                self.logger.info(f"SENTENCE breath_first_search {[n.name for n in node.knowledge_nodes], node.text}")
            else:
                self.logger.info(f"not map {node.text}")
            self.logger.info("+=====================")

    @property
    def replaced_text(self):
        self.breath_first_search()
        return self.text

    @property
    def type(self):
        if self.question_phrase is not None:
            return SentenceTypes.QUESTION
        if self.phrase_root.is_verb and self.words[0].is_verb:
            return SentenceTypes.COMMAND
        return SentenceTypes.NORMAL

    @property
    def is_question(self):
        return self.type == SentenceTypes.QUESTION

    @property
    def is_describe(self):
        return self.type == SentenceTypes.COMMAND and (self.words[0].is_describe or self.words[-1].is_describe)

    @property
    def target_describe_phrase(self) -> Phrase:
        return self.phrase_root.top_phrases[0]

    @property
    def answer(self) -> str:
        output = None
        if self.is_question:
            question_phrase = self.question_phrase
            if not question_phrase.is_mapped:
                self.logger.info(f"QUESTION PHRASE NOT MAP {self.replaced_text}")
            else:
                best_match_knowledge_node = self.question_phrase.best_match_knowledge_node
                for phrase in self.ner_phrases:
                    if best_match_knowledge_node in phrase.knowledge_nodes:
                        output = best_match_knowledge_node.name
                if output is None:
                    result_question = [n.name for n in self.question_phrase.best_match_knowledge_nodes
                                       if n.name is not None]
                    self.logger.info(f"RESULT QUESTION {result_question}")
                    output = ", ".join(set(n.name for n in self.question_phrase.best_match_knowledge_nodes
                                           if n.name is not None))
                    if len(output) == 0:
                        output = None
        elif self.is_describe:
            target_phrase = self.target_describe_phrase
            if target_phrase.is_mapped:
                knowledge_node = target_phrase.best_match_knowledge_node
                self.logger.info(f"RESULT DESCRIBE {knowledge_node.name}: {knowledge_node.description}")
                output = f"{knowledge_node.name}: {knowledge_node.description}"

        if output is not None:
            return output

    def get_answer(self, nodes, force=False):
        output = None
        if self.is_question:
            question_phrase = self.question_phrase
            if not question_phrase.is_mapped and not force:
                self.logger.info(f"QUESTION PHRASE NOT MAP {self.replaced_text}")
                # return
            else:
                self.logger.info(f"RESULT QUESTION {[n.name for n in nodes if n.name is not None]}")
                output = ", ".join(set(n.name for n in nodes if n.name is not None))
                if len(output) == 0:
                    output = None
        elif self.is_describe:
            target_phrase = self.target_describe_phrase
            if target_phrase.is_mapped:
                knowledge_node = target_phrase.best_match_knowledge_node
                self.logger.info(f"RESULT DESCRIBE {knowledge_node.name}: {knowledge_node.description}")
                output = f"{knowledge_node.name}: {knowledge_node.description}"

        if output is not None:
            return output

    @property
    def matched_phrases(self):
        output = [p for p in self.noun_phrases if p.is_mapped]
        output.sort(key=lambda p: p.score)
        return output

    def best_match(self):
        return self.matched_phrases[0]

    @property
    def best_information(self):
        output_infor = []
        image_urls = []
        for phrase in self.matched_phrases:
            best_match_knowledge_node = phrase.best_match_knowledge_node
            if best_match_knowledge_node is None:
                continue
            output_infor.append(best_match_knowledge_node.description_paragraph)
            image_urls += best_match_knowledge_node.image_urls
        return "\n".join(output_infor), image_urls

    @property
    def graph(self):
        output = []
        for phrase in self.phrases:
            if phrase.is_mapped or phrase.is_partially_mapped:
                for relation, score in phrase.out_relation_scores.items():
                    src_node = relation.src_node
                    dst_node = relation.dst_node
                    dst_phrases = dst_node.phrases
                    for dst_phrase in dst_phrases:
                        output.append(f"({phrase.text}: {src_node.name}: {phrase.knowledge_node_scores[src_node]}) ==["
                                      f"{relation.id}: {score}]==> ({dst_phrase.text}: {dst_node.name}: "
                                      f"{dst_phrase.knowledge_node_scores[dst_node]})")
        return output
