from pydantic import BaseModel,  HttpUrl
from typing import List, Optional

class VideoRequest(BaseModel):
    url_or_id: str
    max_comments: int = 100 

class Comment(BaseModel):
    commentId: str
    text: str

class VideoRequest(BaseModel):
    url: str

class Comment_youtube(BaseModel):
    threadId: str
    commentId: str
    videoId: str
    author: Optional[str]
    authorChannelId: Optional[str]
    isReply: bool
    parentCommentId: Optional[str]
    publishedAtComment: Optional[str]
    text: str
    likeCountComment: Optional[int]
    replyCount: Optional[int]

class CommentList(BaseModel):
    comments: List[Comment]