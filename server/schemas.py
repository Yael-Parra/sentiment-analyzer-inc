from pydantic import BaseModel

class VideoRequest(BaseModel):
    url_or_id: str
    max_comments: int = 100 

class Comment(BaseModel):
    commentId: str
    text: str