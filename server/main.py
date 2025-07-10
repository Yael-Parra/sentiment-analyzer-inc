from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.schemas import VideoRequest, Comment, PredictionResponse  
from etl.youtube_extraction import extract_video_id, fetch_comment_threads 
from server.outils.prediction_pipeline import predict_pipeline
from server.database.save_comments import get_comments_by_video, delete_comments_by_video, get_video_statistics
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
@app.post("/CommentAnalyzer/", response_model=PredictionResponse)
def predict_from_youtube(request: VideoRequest):
    result = predict_pipeline(request.url_or_id, max_comments=request.max_comments)
    return result


# ---------------------------------------------------------------------------------------------------------   
# Endpoint GET para los gráficos, se traen por video_id:
from fastapi import Query

@app.get("/stats/")
def get_stats(
    video_id: str = Query(..., description="ID del video de YouTube"),
    max_comments: int = Query(None, description="Número máximo de comentarios a devolver (opcional)")
):
    """
    Recupera estadísticas guardadas para gráficos del frontend
    NO ejecuta pipeline - solo consulta base de datos
    """
    try:
        print(f"🔍 Recuperando estadísticas guardadas para: {video_id}")
        saved_stats = get_video_statistics(video_id)
        
        if not saved_stats:
            raise HTTPException(
                status_code=404, 
                detail=f"Video {video_id} no ha sido analizado. Usa /CommentAnalyzer/ primero."
            )
        
        # Filtrar comentarios si se especifica max_comments
        if max_comments is not None:
            # Aquí asumo que saved_stats contiene los comentarios completos
            # Si no es así, quita esta parte
            saved_stats["comments"] = saved_stats["comments"][:max_comments]
            saved_stats["total_comments"] = len(saved_stats["comments"])
        
        return {
            "video_id": video_id,
            "total_comments": saved_stats["total_comments"],
            "toxicity_distribution": saved_stats["toxicity_stats"],
            "sentiment_analysis": {
                "mean_score": saved_stats["mean_sentiment_score"],
                "sentiment_counts": saved_stats["sentiment_distribution"],
                "dominant_sentiment": max(
                    saved_stats["sentiment_distribution"].items(),
                    key=lambda x: x[1]
                )[0]
            },
            "engagement_stats": {
                "comments_with_urls": saved_stats["engagement_stats"].get("url_count", 0),
                "comments_with_tags": saved_stats["engagement_stats"].get("tag_count", 0),
                "url_percentage": saved_stats["porcentaje_tagged"],
                "mean_likes": saved_stats["mean_likes"],
                "max_likes": saved_stats["max_likes"]
            },
            "source": "database"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando estadísticas: {str(e)}")
# ---------------------------------------------------------------------------------------------------------   
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