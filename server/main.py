from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.schemas import VideoRequest, Comment  
from etl.youtube_extraction import extract_video_id, fetch_comment_threads 
from server.outils.prediction_pipeline import predict_pipeline
from server.schemas import PredictionResponse
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
        stats = result.get("stats", {})

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
            "mean_sentiment": None,
            "max_sentiment": None
        }
        if comments and "sentiment" in comments[0]:
            sentimientos["mean_sentiment"] = sum(c.get("sentiment", 0) for c in comments) / total_comments
            sentimientos["max_sentiment"] = max(c.get("sentiment", 0) for c in comments)

        # 4. Porcentaje de comentarios con tags
        tags = ["is_toxic", "is_hatespeech", "is_abusive", "is_provocative", "is_racist",
                "is_obscene", "is_threat", "is_religious_hate", "is_nationalist",
                "is_sexist", "is_homophobic", "is_radicalism"]
        tagged = sum(
            any(c.get(tag) for tag in tags)
            for c in comments
        )
        porcentaje_tagged = (tagged / total_comments * 100) if total_comments else 0


        # 5. Mean y max de likes en comentarios
        if comments and "likeCountComment" in comments[0]:
            likes = [c.get("likeCountComment", 0) for c in comments]
            mean_likes = sum(likes) / len(likes) if likes else 0
            max_likes = max(likes) if likes else 0
        else:
            mean_likes = None
            max_likes = None

        return {
            "video_id": video_id,
            "cantidad_comentarios": cantidad_comentarios,
            "barras_toxicidad": barras,
            "sentimientos": sentimientos,
            "porcentaje_tagged": porcentaje_tagged,
            "mean_likes": mean_likes,
            "max_likes": max_likes,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))