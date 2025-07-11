import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
from server.outils.prediction_pipeline import predict_pipeline
from server.database.save_comments import get_comments_by_video, get_video_statistics
from etl.youtube_extraction import extract_video_id, fetch_comment_threads

class VideoMonitor:
    def __init__(self):
        self.active_monitors: Dict[str, asyncio.Task] = {}
        self.monitor_data: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, List] = {}
        self.known_comment_ids: Dict[str, Set[str]] = {}
    
    async def start_monitoring(self, video_id: str, interval_minutes: int = 5):
        
        #Inicia monitoreo de un video específico
        if video_id in self.active_monitors:
            print(f"⚠️ Video {video_id} ya está siendo monitoreado")
            return False
        await self._initialize_known_comments(video_id)
        # Crear tarea de monitoreo
        task = asyncio.create_task(self._monitor_video_loop(video_id, interval_minutes))
        self.active_monitors[video_id] = task
        
        # Inicializar datos del monitor
        self.monitor_data[video_id] = {
            "started_at": datetime.now(),
            "last_check": None,
            "interval_minutes": interval_minutes,
            "total_checks": 0,
            "new_comments_found": 0,
            "toxic_comments_found": 0,
            "known_comments": len(self.known_comment_ids.get(video_id, set()))
        }
        
        print(f"🔄 Monitoreo iniciado para video {video_id} (cada {interval_minutes} min)")
        print(f"📊 Comentarios conocidos: {len(self.known_comment_ids.get(video_id, set()))}")
        return True
    
    async def _initialize_known_comments(self, video_id: str):
        #Inicializa la lista de comentarios desde la BD

        try:
            existing_comments = get_comments_by_video(video_id)
            comment_ids = set()
            for comment in existing_comments:
                comment_id = comment.get('comment_id') or comment.get('commentId') or comment.get('id')
                if comment_id:
                    comment_ids.add(str(comment_id))
            
            self.known_comment_ids[video_id] = comment_ids
            print(f"📋 Inicializados {len(comment_ids)} comentarios conocidos para video {video_id}")
        except Exception as e:
            print(f"⚠️ Error inicializando comentarios conocidos: {e}")
            self.known_comment_ids[video_id] = set()

    async def _monitor_video_loop(self, video_id: str, interval_minutes: int):
        # Loop principal de monitoreo para un video

        while True:
            try:
                await self._check_for_new_comments_only(video_id)
                await asyncio.sleep(interval_minutes * 60)
            except asyncio.CancelledError:
                print(f"🛑 Monitoreo cancelado para video {video_id}")
                break
            except Exception as e:
                print(f"❌ Error en monitoreo de {video_id}: {e}")
                await asyncio.sleep(60)
    
    async def _check_for_new_comments_only(self, video_id: str):
        # Verifica si hay cambios en el video
        print(f"🔍 Verificando cambios en video {video_id}...")
        try:
            # 1. Obtener comentarios actuales en BD
            current_comments = get_comments_by_video(video_id)
            known_ids = self.known_comment_ids.get(video_id, set())
            current_count = len(current_comments)
            
            # 2. Ejecutar tu pipeline completo (como antes)
            result = predict_pipeline(video_id, max_comments=20)
            new_count = result.total_comments
            
            # 3. Actualizar estadísticas del monitor
            self.monitor_data[video_id]["last_check"] = datetime.now()
            self.monitor_data[video_id]["total_checks"] += 1
            
            # 4. Detectar si hay nuevos comentarios
            if new_count > current_count:
                new_comments_count = new_count - current_count
                
                # 5. Obtener los últimos comentarios (nuevos)
                latest_comments = result.comments[-new_comments_count:]
                
                # 6. Filtrar solo los realmente nuevos por ID
                truly_new_comments = []
                for comment in latest_comments:
                    comment_id = getattr(comment, 'commentId', None) or getattr(comment, 'comment_id', None)
                    if comment_id and str(comment_id) not in known_ids:
                        truly_new_comments.append(comment)
                
                if truly_new_comments:
                    print(f"🆕 Encontrados {len(truly_new_comments)} comentarios REALMENTE nuevos")
                    
                    for comment in truly_new_comments:
                        author = getattr(comment, 'author', 'unknown')
                        text = getattr(comment, 'text', 'N/A')[:100] + "..." if len(getattr(comment, 'text', '')) > 100 else getattr(comment, 'text', 'N/A')
                        print(f"📝 Nuevo comentario de {author}: {text}")
                    # 7. Detectar comentarios tóxicos
                    toxic_comments = []
                    TOXICITY_FIELDS = [
                        "is_toxic", "is_hatespeech", "is_abusive", "is_provocative", 
                        "is_racist", "is_obscene", "is_threat", "is_religious_hate", 
                        "is_nationalist", "is_sexist", "is_homophobic", "is_radicalism"
                    ]
                    
                    for comment in truly_new_comments:
                        if any(getattr(comment, field, False) for field in TOXICITY_FIELDS):
                            toxic_comments.append({
                                "text": getattr(comment, 'text', 'N/A'),
                                "author": getattr(comment, 'author', 'unknown'),
                                "comment_id": getattr(comment, 'commentId', 'unknown'),
                                "detected_types": [field.replace('is_', '') for field in TOXICITY_FIELDS 
                                                 if getattr(comment, field, False)]
                            })

                    for comment in truly_new_comments:
                        comment_id = getattr(comment, 'commentId', None) or getattr(comment, 'comment_id', None)
                        if comment_id:
                            self.known_comment_ids[video_id].add(str(comment_id))

                    self.monitor_data[video_id]["new_comments_found"] += len(truly_new_comments)

                    if toxic_comments:
                        self.monitor_data[video_id]["toxic_comments_found"] += len(toxic_comments)
                        
                        await self._notify_websocket_clients(video_id, {
                            "type": "new_toxic_comments",
                            "count": len(toxic_comments),
                            "new_comments": len(truly_new_comments),
                            "timestamp": datetime.now().isoformat(),
                            "comments": toxic_comments
                        })
                        
                        print(f"⚠️ {len(toxic_comments)} comentarios tóxicos nuevos encontrados")
                    else:
                        print(f"✅ {len(truly_new_comments)} comentarios nuevos (no tóxicos)")
                else:
                    print(f"📊 No hay comentarios realmente nuevos (ya conocidos)")
            else:
                print(f"📊 No hay comentarios nuevos en video {video_id}")
                
        except Exception as e:
            print(f"❌ Error analizando comentarios nuevos: {e}")


    
    async def _notify_websocket_clients(self, video_id: str, message: Dict):
     # Envía notificaciones a clientes WebSocket conectados

        if video_id in self.websocket_connections:
            disconnected = []
            for websocket in self.websocket_connections[video_id]:
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(websocket)

            for ws in disconnected:
                self.websocket_connections[video_id].remove(ws)
    
    def stop_monitoring(self, video_id: str):
     # Detiene monitoreo de un video

        if video_id in self.active_monitors:
            self.active_monitors[video_id].cancel()
            del self.active_monitors[video_id]
            if video_id in self.monitor_data:
                del self.monitor_data[video_id]
            if video_id in self.known_comment_ids:
                del self.known_comment_ids[video_id]
            print(f"🛑 Monitoreo detenido para video {video_id}")
            return True
        return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
    # Obtiene estado actual de todos los monitores

        return {
            "active_monitors": list(self.active_monitors.keys()),
            "monitor_data": self.monitor_data,
            "total_active": len(self.active_monitors)
        }
    
    def add_websocket_connection(self, video_id: str, websocket):
    # Añade conexión WebSocket para un video

        if video_id not in self.websocket_connections:
            self.websocket_connections[video_id] = []
        self.websocket_connections[video_id].append(websocket)
    
    def remove_websocket_connection(self, video_id: str, websocket):
    # Remueve conexión WebSocket

        if video_id in self.websocket_connections:
            try:
                self.websocket_connections[video_id].remove(websocket)
            except ValueError:
                pass
# Inicializar el monitor de videos
video_monitor = VideoMonitor()