from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.schemas import VideoRequest, Comment, PredictionResponse  
from etl.youtube_extraction import extract_video_id, fetch_comment_threads 
from server.outils.prediction_pipeline import predict_pipeline
from server.database.connection_db import supabase 
from server.database.save_comments import get_comments_by_video, delete_comments_by_video, get_video_statistics
from typing import List
import json 
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

@app.get("/sentiment-analyzer/all")
def get_all_sentiment_analyzer():
    # Recupera TODOS los comentarios analizados de la tabla sentiment_analyzer

    try:
        print("🔍 Recuperando todos los comentarios de sentiment_analyzer...")
        response = supabase.table("sentiment_analyzer").select("*").execute()
        
        if response.data:
            return {
                "total_comments": len(response.data),
                "comments": response.data,
                "source": "sentiment_analyzer_table"
            }
        else:
            return {
                "total_comments": 0,
                "comments": [],
                "message": "No hay comentarios en la tabla sentiment_analyzer"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando comentarios: {str(e)}")

@app.get("/sentiment-analyzer/video/{video_id}")
def get_sentiment_analyzer_by_video_id(video_id: str):
     # Recupera comentarios de sentiment_analyzer por video_id específico
   
    try:
        print(f"🔍 Recuperando comentarios de sentiment_analyzer para video: {video_id}")
        comments = get_comments_by_video(video_id)
        
        if comments:
            return {
                "video_id": video_id,
                "total_comments": len(comments),
                "comments": comments,
                "source": "sentiment_analyzer_table"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontraron comentarios para el video {video_id} en sentiment_analyzer"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando comentarios: {str(e)}")

@app.get("/video-statistics/all")
def get_all_video_statistics():
    # Recupera TODAS las estadísticas de videos de la tabla video_statistics
    try:
        print("📊 Recuperando todas las estadísticas de video_statistics...")
        response = supabase.table("video_statistics").select("*").execute()
        
        if response.data:
            # Parsear campos JSON para cada registro
            parsed_stats = []
            for stat in response.data:
                parsed_stat = stat.copy()
                
                # Parsear campos JSON
                if parsed_stat.get("sentiment_distribution"):
                    parsed_stat["sentiment_distribution"] = json.loads(parsed_stat["sentiment_distribution"])
                if parsed_stat.get("toxicity_stats"):
                    parsed_stat["toxicity_stats"] = json.loads(parsed_stat["toxicity_stats"])
                if parsed_stat.get("engagement_stats"):
                    parsed_stat["engagement_stats"] = json.loads(parsed_stat["engagement_stats"])
                
                parsed_stats.append(parsed_stat)
            
            return {
                "total_videos": len(parsed_stats),
                "video_statistics": parsed_stats,
                "source": "video_statistics_table"
            }
        else:
            return {
                "total_videos": 0,
                "video_statistics": [],
                "message": "No hay estadísticas en la tabla video_statistics"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando estadísticas: {str(e)}")

@app.get("/video-statistics/video/{video_id}")
def get_video_statistics_by_video_id(video_id: str):
    # Recupera estadísticas de video_statistics por video_id específico
    try:
        print(f"📊 Recuperando estadísticas de video_statistics para video: {video_id}")
        saved_stats = get_video_statistics(video_id)
        
        if saved_stats:
            return {
                "video_id": video_id,
                "statistics": saved_stats,
                "source": "video_statistics_table"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontraron estadísticas para el video {video_id} en video_statistics"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando estadísticas: {str(e)}")

@app.post("/extract-comments/") 
def extract_comments_endpoint(request: VideoRequest):
    try:
        video_id = extract_video_id(request.url_or_id)
        comments = fetch_comment_threads(video_id, max_total=request.max_comments)
        return {
            "video_id": video_id,
            "total_comments": len(comments),
            "comments": comments,
            "source": "youtube_api"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo comentarios: {str(e)}")

# Endpoint predicción
@app.post("/CommentAnalyzer/", response_model=PredictionResponse)
def predict_from_youtube(request: VideoRequest):
    try:
        result = predict_pipeline(request.url_or_id, max_comments=request.max_comments)
        return result
    except Exception as e:
        print(f"❌ Error en predict_pipeline: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": f"Error en el análisis: {str(e)}"})


# Endpoint GET para los gráficos, se traen por video_id:
@app.get("/stats/")
def get_stats(video_id: str):
    # Recupera estadísticas guardadas para gráficos del frontend
    # NO ejecuta pipeline - solo consulta base de datos
    try:
        print(f"🔍 Recuperando estadísticas guardadas para: {video_id}")
        saved_stats = get_video_statistics(video_id)
        
        if saved_stats:
            return {
                "video_id": video_id,
                "cantidad_comentarios": saved_stats["total_comments"],
                "barras_toxicidad": saved_stats["toxicity_stats"],
                "sentimientos": {
                    "mean_sentiment_score": saved_stats["mean_sentiment_score"],
                    "sentiment_types_distribution": saved_stats["sentiment_distribution"]
                },
                "porcentaje_tagged": saved_stats["porcentaje_tagged"],
                "mean_likes": saved_stats["mean_likes"],
                "max_likes": saved_stats["max_likes"],
                "engagement_stats": saved_stats["engagement_stats"],
                "source": "database"
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Video {video_id} no ha sido analizado. Usa /CommentAnalyzer/ primero."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recuperando estadísticas: {str(e)}")


@app.delete("/sentiment-analyzer/video/{video_id}")
def delete_sentiment_analyzer_by_video_id(video_id: str):
    """Elimina todos los comentarios guardados de un video"""
    try:
        success = delete_comments_by_video(video_id)
        if success:
            return {"message": f"Comentarios del video {video_id} eliminados correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar comentarios")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))