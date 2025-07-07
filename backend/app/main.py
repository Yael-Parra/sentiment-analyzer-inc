from fastapi import FastAPI
from app.schemas import TextIn, PredictionOut
from app.predict import predict_hate

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hate speech detector is running."}

@app.post("/predict", response_model=PredictionOut)
def predict(comment: TextIn):
    hate, prob = predict_hate(comment.comment)
    return {"hate_speech": hate, "probability": prob}
