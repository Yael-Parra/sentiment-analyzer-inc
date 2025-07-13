import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
import asyncio
import time
from datetime import datetime
from typing import Dict
import requests
from server.outils.prediction_pipeline import predict_pipeline
import os
from dotenv import load_dotenv



class LiveChatMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.monitor_data: Dict[str, Dict] = {}

    def get_live_chat_id(self, video_id: str) -> str:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={self.api_key}"
        res = requests.get(url).json()
        try:
            return res["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
        except Exception:
            print(f"❌ No se pudo obtener el liveChatId para video {video_id}")
            return None

    async def start_monitoring(self, video_id: str):
        if video_id in self.active_monitors:
            print(f"⚠️ Video {video_id} ya está siendo monitoreado")
            return False

        chat_id = self.get_live_chat_id(video_id)
        if not chat_id:
            return False

        task = asyncio.create_task(self._monitor_chat_loop(video_id, chat_id))
        self.active_monitors[video_id] = task
        self.monitor_data[video_id] = {
            "started_at": datetime.now(),
            "total_messages": 0,
            "toxic_messages": 0
        }
        print(f"📡 Monitoreo en vivo iniciado para video {video_id}")
        return True

    async def _monitor_chat_loop(self, video_id: str, chat_id: str):
        next_page_token = None
        base_url = "https://www.googleapis.com/youtube/v3/liveChat/messages"

        while True:
            try:
                params = {
                    "liveChatId": chat_id,
                    "part": "snippet,authorDetails",
                    "key": self.api_key
                }
                if next_page_token:
                    params["pageToken"] = next_page_token

                response = requests.get(base_url, params=params).json()
                next_page_token = response.get("nextPageToken")
                wait = response.get("pollingIntervalMillis", 2000) / 1000

                for item in response.get("items", []):
                    author = item["authorDetails"]["displayName"]
                    message = item["snippet"]["displayMessage"]
                    published_at = item["snippet"]["publishedAt"]
                    comment_id = item["id"]

                    self.monitor_data[video_id]["total_messages"] += 1

                    # Detectar toxicidad
                    result = predict_pipeline(message)
                    if result.get("is_toxic"):
                        self.monitor_data[video_id]["toxic_messages"] += 1
                        print(f"⚠️ Comentario tóxico detectado: {author}: {message}")
                    else:
                        print(f"💬 {author}: {message}")

                await asyncio.sleep(wait)
            except asyncio.CancelledError:
                print(f"🛑 Monitoreo cancelado para video {video_id}")
                break
            except Exception as e:
                print(f"❌ Error en el monitoreo de {video_id}: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self, video_id: str):
        if video_id in self.active_monitors:
            self.active_monitors[video_id].cancel()
            del self.active_monitors[video_id]
            del self.monitor_data[video_id]
            print(f"🛑 Monitoreo detenido para video {video_id}")

    def get_status(self):
        return self.monitor_data



load_dotenv()
API_KEY = os.getenv("YouTube_Data_API_v3")
live_monitor = LiveChatMonitor(API_KEY)
