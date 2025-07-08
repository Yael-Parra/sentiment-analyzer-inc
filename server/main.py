from fastapi import FastAPI
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
def get_stats(video_id: str):
    stats = {
        "video_id": video_id,
        "positive_comments": 0,
        "negative_comments": 0,
        "neutral_comments": 0,
    }
    return stats