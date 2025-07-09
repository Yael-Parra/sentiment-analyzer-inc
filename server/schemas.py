from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class VideoRequest(BaseModel):
    url_or_id: str
    max_comments: int = 100 

class Comment(BaseModel):
    video_id: str
    text: str
    toxic_probability: Optional[float]
    is_toxic: Optional[bool]
    hatespeech_probability: Optional[float]
    is_hatespeech: Optional[bool]
    abusive_probability: Optional[float]
    is_abusive: Optional[bool]
    provocative_probability: Optional[float]
    is_provocative: Optional[bool]
    racist_probability: Optional[float]
    is_racist: Optional[bool]
    obscene_probability: Optional[float]
    is_obscene: Optional[bool]
    threat_probability: Optional[float]
    is_threat: Optional[bool]
    religious_hate_probability: Optional[float]
    is_religious_hate: Optional[bool]
    nationalist_probability: Optional[float]
    is_nationalist: Optional[bool]
    sexist_probability: Optional[float]
    is_sexist: Optional[bool]
    homophobic_probability: Optional[float]
    is_homophobic: Optional[bool]
    radicalism_probability: Optional[float]
    is_radicalism: Optional[bool]

    # Campos adicionales temporales
    sentiment_type: Optional[str] = None
    sentiment_intensity: Optional[float] = None
    is_self_promotional: Optional[bool] = None
    has_url: Optional[bool] = None
    has_tag: Optional[bool] = None
    like_count_comment: Optional[int] = None
    reply_count: Optional[int] = None
    author: Optional[str] = None
    
    class Config:
        extra = "allow"

class PredictionStats(BaseModel):
    count: int
    percentage: float

class PredictionResponse(BaseModel):
    video_id: str
    total_comments: int
    stats: Dict[str, PredictionStats]
    comments: List[Comment]