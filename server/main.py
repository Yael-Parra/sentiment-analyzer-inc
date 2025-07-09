from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.schemas import VideoRequest, Comment  
from etl.youtube_extraction import extract_video_id, fetch_comment_threads 
from server.outils.prediction_pipeline import predict_pipeline
from server.schemas import PredictionResponse
from server.database.save_comments import get_comments_by_video, delete_comments_by_video
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

@app.post("/extract-comments/", response_model=List[Comment])
def extract_comments_endpoint(request: VideoRequest):
    video_id = extract_video_id(request.url_or_id)
    comments = fetch_comment_threads(video_id)
    return comments

# Endpoint predicción
@app.post("/predict/", response_model=PredictionResponse)
def predict_from_youtube(request: VideoRequest):
    result = predict_pipeline(request.url_or_id, max_comments=request.max_comments)
    return result


# Endpoint GET para los gráficos, se traen por video_id:
@app.get("/stats/")
def get_stats(video_id: str, max_comments: int = 100):
    try:
        # Vamos a esperar a que ya esté en producción para confirmar el pipeline
        result = predict_pipeline(video_id, max_comments=max_comments)
        comments = result.get("comments", [])
        total_comments = result.get("total_comments", 0)

        # 1. Cantidad total de comentarios
        cantidad_comentarios = total_comments

        # 2. Gráfico de barras, por cada etiqueta 
        etiquetas = [
            "is_toxic", "is_hatespeech", "is_abusive", "is_provocative", "is_racist",
            "is_obscene", "is_threat", "is_religious_hate", "is_nationalist",
            "is_sexist", "is_homophobic", "is_radicalism"
        ]
        barras = {
            etiqueta: {
                "true": sum(1 for c in comments if c.get(etiqueta) is True),
                "false": sum(1 for c in comments if c.get(etiqueta) is False)
            }
            for etiqueta in etiquetas
        }

        # 3. Sentimientos e intensidad:
        sentimientos = {
            "mean_sentiment_intensity": None,
            "sentiment_types_distribution": {},
        }
        if comments:
            # Intensidad promedio (VADER score)
            intensities = []
            for c in comments:
                intensity = c.get("sentiment_intensity", 0)
                if isinstance(intensity, (int, float)):  # ← Solo números
                    intensities.append(float(intensity))
                elif isinstance(intensity, str):  # ← Si es string, convertir
                    try:
                        intensities.append(float(intensity))
                    except ValueError:
                        # Si no se puede convertir, usar 0
                        intensities.append(0.0)

            if intensities:
                sentimientos["mean_sentiment_intensity"] = sum(intensities) / len(intensities)
            
            # Distribución de tipos de sentimiento
            sentiment_counts = {}
            for c in comments:
                stype = c.get("sentiment_type", "neutral")
                sentiment_counts[stype] = sentiment_counts.get(stype, 0) + 1
            sentimientos["sentiment_types_distribution"] = sentiment_counts

        # 4. Porcentaje de comentarios con tags
        tagged = sum(
            any(c.get(tag) for tag in etiquetas)
            for c in comments
        )
        porcentaje_tagged = (tagged / total_comments * 100) if total_comments else 0


        # 5. Mean y max de likes en comentarios
        likes = [c.get("like_count_comment", 0) for c in comments if c.get("like_count_comment") is not None]
        mean_likes = sum(likes) / len(likes) if likes else 0
        max_likes = max(likes) if likes else 0

        # 6. Estadísticas de engagement
        has_url_count = sum(1 for c in comments if c.get("has_url"))
        has_tag_count = sum(1 for c in comments if c.get("has_tag"))
        
        return {
            "video_id": video_id,
            "cantidad_comentarios": cantidad_comentarios,
            "barras_toxicidad": barras,
            "sentimientos": sentimientos,
            "porcentaje_tagged": porcentaje_tagged,
            "mean_likes": mean_likes,
            "max_likes": max_likes,
            "engagement_stats": {
                "comments_with_urls": has_url_count,
                "comments_with_tags": has_tag_count,
                "url_percentage": (has_url_count / total_comments * 100) if total_comments else 0,
                "tag_percentage": (has_tag_count / total_comments * 100) if total_comments else 0,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/saved-comments/{video_id}")
def get_saved_comments(video_id: str):
    """Recupera comentarios guardados de un video específico"""
    try:
        comments = get_comments_by_video(video_id)
        return {
            "video_id": video_id,
            "total_saved_comments": len(comments),
            "comments": comments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/saved-comments/{video_id}")
def delete_saved_comments(video_id: str):
    """Elimina todos los comentarios guardados de un video"""
    try:
        success = delete_comments_by_video(video_id)
        if success:
            return {"message": f"Comentarios del video {video_id} eliminados correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar comentarios")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))