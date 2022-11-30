from typing import Optional, Any
from pydantic import BaseModel


class ChoiceResult(BaseModel):
    choice: Optional[Any]
    score: Optional[float]

    def __init__(self, choice: Any = None, score: float = None):
        super(ChoiceResult, self).__init__(choice=choice, score=score)
        self.choice = choice
