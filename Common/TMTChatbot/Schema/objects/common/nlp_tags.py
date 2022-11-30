from typing import Optional, List, Any
from pydantic import BaseModel

from TMTChatbot.Common.utils.unit_parser import UnitParser


class Intent(BaseModel):
    tag: str
    score: Optional[float]
    subject: Optional[str]
    detail: Optional[List[str]]

    def __init__(self, tag: str, score: float = None, **kwargs):
        super(Intent, self).__init__(tag=tag, score=score)
        self.tag = tag
        if tag.count("@") == 1:
            self.subject, detail = self.tag.split("@")
        else:
            self.subject, detail = None, ""
        self.detail = detail.split("_")

    @property
    def action(self):
        if len(self.detail) > 0:
            return self.detail[0]

    @property
    def object(self):
        if len(self.detail) > 1:
            return self.detail[1]

    @property
    def object_detail(self):
        if len(self.detail) > 2:
            return "_".join(self.detail[2:])


class NerTag(BaseModel):
    text: str
    label: str
    begin: Optional[int]
    end: Optional[int]
    entity_id: Optional[str]
    labels: Optional[List[str]]
    extra_data: Optional[Any]
    normalized_value: Optional[Any]
    parsed_value: Optional[Any]

    def __init__(self, text: str, label: str, begin: int, end: int, entity_id: str = None, extra_data: Any = None,
                 normalized_value: str = None, parsed_value: Any = None, labels: list = None, **kwargs):
        super(NerTag, self).__init__(text=text, label=label, begin=begin, end=end, entity_id=entity_id,
                                     extra_data=extra_data, normalized_value=normalized_value)
        self.text = text.replace("_", " ").strip()
        self.label = label
        self.labels = labels if labels is not None else [label] if (label is not None and len(label) > 0) else []
        self.entity_id = entity_id
        self.extra_data = extra_data
        self.parsed_value = parsed_value if parsed_value is not None else UnitParser.normalize(self.text, self.label)
        self.normalized_value = normalized_value

    def __contains__(self, item):
        if self.begin is None or self.end is None or item.begin is None or item.end is None:
            return False
        return self.begin <= item.begin and self.end >= item.end

    def join(self, item):
        if item in self and item.label not in self.labels and len(item.label) > 0:
            self.labels.append(item.label)
            self.labels.sort(key=lambda label: label.isupper())
            self.label = self.labels[0]
            return self

    @property
    def id(self):
        return str(id(self))


class DependencyTag(BaseModel):
    form: str
    posTag: str
    head: int
    depLabel: str
    index: int

    def __init__(self, form: str, posTag: str, head: int, depLabel: str, index: int):
        super(DependencyTag, self).__init__(form=form, posTag=posTag, head=head, depLabel=depLabel, index=index)
        self.form = form
        self.posTag = posTag
        self.depLabel = depLabel


class Word(BaseModel):
    text: str
    pos: Optional[str]
    synonyms: Optional[List[str]]

    def __init__(self, text: str, synonyms: List[str] = None, pos: str = None):
        super(Word, self).__init__(text=text, pos=pos)
        self.synonyms = synonyms
        self.text = text
        self.pos = pos
