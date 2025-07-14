import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import httpx
import requests
from server.outils.prediction_pipeline import predict_toxicity_for_text
import os
from dotenv import load_dotenv

load_dotenv(override=True)
API_KEY = os.getenv("YouTube_Data_API_v3")
print(f"🔑 [DEBUG] Clave de API cargada: ...{API_KEY[-4:] if API_KEY else 'NINGUNA'}")

if not API_KEY:
    print("❌ ERROR: No se pudo cargar la variable de entorno 'YouTube_Data_API_v3'. Revisa tu archivo .env.")


class LiveChatMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.monitor_data: Dict[str, Dict] = {}
        self.client = httpx.AsyncClient()

    async def get_live_chat_id(self, video_id: str) -> str:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={self.api_key}"
        try:
            res = await self.client.get(url)
            res.raise_for_status()
            data = res.json()
            return data["items"][0]["liveStreamingDetails"]["activeLiveChatId"]
        except (httpx.HTTPStatusError, KeyError, IndexError) as e:
            print(f"❌ No se pudo obtener el liveChatId para video {video_id}: {e}")
            return None

    async def start_monitoring(self, video_id: str):
        if video_id in self.active_monitors:
            print(f"⚠️ Video {video_id} ya está siendo monitoreado")
            return False

        chat_id = await self.get_live_chat_id(video_id)
        if not chat_id:
            return False

        task = asyncio.create_task(self._monitor_chat_loop(video_id, chat_id))
        self.active_monitors[video_id] = task
        self.monitor_data[video_id] = {
            "started_at": datetime.now(),
            "total_messages": 0,
            "toxic_messages": 0,
            "comments": []
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

                response = await self.client.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                next_page_token = data.get("nextPageToken")
                wait = data.get("pollingIntervalMillis", 2000) / 1000

                for item in data.get("items", []):
                    self.monitor_data[video_id]["total_messages"] += 1
                    
                    message = item["snippet"]["displayMessage"]
                    author = item["authorDetails"]["displayName"]

                    toxicity_result = predict_toxicity_for_text(message)
                    
                    comment_data = {
                        "Autor": author,
                        "Mensaje": message,
                        "Es Tóxico": toxicity_result["is_toxic"],
                        "Hora": datetime.now().strftime("%H:%M:%S")
                    }
                    self.monitor_data[video_id]["comments"].insert(0, comment_data)
                    # Limitamos a los últimos 50 comentarios para no saturar la memoria
                    self.monitor_data[video_id]["comments"] = self.monitor_data[video_id]["comments"][:50]

                    if toxicity_result["is_toxic"]:
                        self.monitor_data[video_id]["toxic_messages"] += 1

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
            print(f"🛑 Monitoreo detenido para video {video_id}")

    def get_status(self):
        return self.monitor_data

live_monitor = LiveChatMonitor(API_KEY)
