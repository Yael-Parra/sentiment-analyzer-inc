# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from etl.youtube_extraction import extract_comments, VideoRequest, Comment
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
    return extract_comments(request)
