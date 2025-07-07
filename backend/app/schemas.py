# backend/app/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class VideoRequest(BaseModel):
    url: str

class Comment(BaseModel):
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