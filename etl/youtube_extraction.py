# backend/etl/youtube_extraction.py
from dotenv import load_dotenv
import os
import requests
import time
import re
from pydantic import BaseModel
from typing import List, Optional

load_dotenv()
API_KEY = os.getenv("YouTube_Data_API_v3")

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

def extract_video_id(url_or_id: str) -> str:
    print(f"🔍 Extrayendo ID del vídeo de: {url_or_id}")
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url_or_id)
    if match:
        video_id = match.group(1)
        print(f"✅ ID extraído: {video_id}")
        return video_id
    else:
        print(f"⚠️ No se pudo extraer ID, asumiendo input es ID directo: {url_or_id}")
        return url_or_id

def fetch_comment_threads(video_id: str, max_total: int = 1000, delay: int = 1):
    print(f"▶️ Iniciando extracción de comentarios para video {video_id}")
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    token = None
    total = 0
    round_count = 0

    while total < max_total:
        round_count += 1
        print(f"\n🔁 Petición {round_count}: descargando comentarios...")
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": min(100, max_total - total),
            "textFormat": "plainText",
            "key": API_KEY
        }
        if token:
            params["pageToken"] = token

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])

        for item in items:
            s = item["snippet"]
            top = s["topLevelComment"]["snippet"]

            comments.append({
                "threadId": item["id"],
                "commentId": item["id"],
                "videoId": video_id,
                "author": top.get("authorDisplayName"),
                "authorChannelId": top.get("authorChannelId", {}).get("value"),
                "isReply": False,
                "parentCommentId": None,
                "publishedAtComment": top.get("publishedAt"),
                "text": top.get("textDisplay"),
                "likeCountComment": top.get("likeCount"),
                "replyCount": s.get("totalReplyCount")
            })
            total += 1

            for rep in item.get("replies", {}).get("comments", []):
                rps = rep["snippet"]
                comments.append({
                    "threadId": item["id"],
                    "commentId": rep["id"],
                    "videoId": video_id,
                    "author": rps.get("authorDisplayName"),
                    "authorChannelId": rps.get("authorChannelId", {}).get("value"),
                    "isReply": True,
                    "parentCommentId": rps.get("parentId"),
                    "publishedAtComment": rps.get("publishedAt"),
                    "text": rps.get("textDisplay"),
                    "likeCountComment": rps.get("likeCount"),
                    "replyCount": None
                })
                total += 1
                if total >= max_total:
                    break
            if total >= max_total:
                break

        token = data.get("nextPageToken")
        if not token:
            break

        time.sleep(delay)

    return comments

def extract_comments(request: VideoRequest) -> List[Comment]:
    video_id = extract_video_id(request.url)
    comments = fetch_comment_threads(video_id)
    return [Comment(**c) for c in comments]
