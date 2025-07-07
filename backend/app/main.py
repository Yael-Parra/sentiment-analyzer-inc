# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from etl.youtube_extraction import extract_comments, VideoRequest, Comment
from typing import List

app = FastAPI(
    title="YouTube Comments Extractor API",
    description="API para extraer comentarios de videos de YouTube por URL o ID.",
    version="1.0.0"
)

# CORS middleware (opcional para permitir conexiones externas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/extract-comments/", response_model=List[Comment])
def extract_comments_endpoint(request: VideoRequest):
    """
    Extrae comentarios (y respuestas) desde un video de YouTube.
    """
    try:
        return extract_comments(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
