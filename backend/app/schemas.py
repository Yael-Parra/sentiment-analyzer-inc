from pydantic import BaseModel

class TextIn(BaseModel):
    comment: str

class PredictionOut(BaseModel):
    hate_speech: bool
    probability: float
