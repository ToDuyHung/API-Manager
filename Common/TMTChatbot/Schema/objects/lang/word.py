from TMTChatbot.Schema.objects.lang.common.utils import check_question_word, replace_question_mask
from TMTChatbot.Schema.objects.lang.common.common_phrases import DESCRIBE_WORDS


class Word:
    def __init__(self, text, pos, head_id, dep_label, index, ner_label=None):
        self.text = text.replace("_", " ")
        self.pos = pos
        self.head_id = head_id
        self.dep_label = dep_label
        self.index = index
        self.is_question_word = check_question_word(text)
        self.parent = None
        self.children = []
        self.start = None
        self.end = None
        self.before_word = None
        self.next_word = None
        self.is_joined = False
        self.can_parent_question = True
        self.ner_label = ner_label

    @property
    def is_pob(self):
        return self.dep_label == "pob"

    @property
    def is_prd(self):
        return self.dep_label == "prd"

    @property
    def is_e(self):
        return self.pos == "E"

    @property
    def is_noun(self):
        return self.pos[0] in "NP" or self.text.isnumeric()

    @property
    def is_nc(self):
        return self.pos == "Nc"

    @property
    def is_nmod(self):
        return self.dep_label == "nmod"

    @property
    def is_pronoun(self):
        return self.pos[0] in "P"

    @property
    def is_verb(self):
        return self.pos[0] in "V"

    @property
    def is_adj(self):
        return self.pos[0] in "A"

    @property
    def is_unk(self):
        return self.pos in "XM"

    @property
    def is_ner(self):
        return self.ner_label is not None and self.ner_label != "O"

    @property
    def is_describe(self):
        return self.text in DESCRIBE_WORDS

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return f"index: {self.index} | text: {self.text} | pos: {self.pos} | ner: {self.is_ner} | head: {self.head_id}"\
               f" | dep: {self.dep_label} | is_question_word: {self.is_question_word}"

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def child_phrase(self):
        print(type(self))
        words = self.children + [self]
        words.sort(key=lambda w: w.index)
        return words

    @property
    def mask(self):
        return self.text

    @property
    def child_mask(self):
        return self.text

    def get_question_mask(self, mask):
        return replace_question_mask(self.text, mask)

    def join(self, other):
        self.text = f"{self.text} {other.text}"
        other.is_joined = True
        self.is_question_word = self.is_question_word or (other.is_question_word and other.can_parent_question)
        self.can_parent_question = False

    def update_index(self, offset):
        self.index += offset
        if self.next_word is not None:
            self.next_word.update_index(offset)
