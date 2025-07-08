import pandas as pd
from etl.youtube_extraction import extract_video_id, fetch_comment_threads
from server.outils.cleaning_pipeline import clean_youtube_data
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_PATH = "cuando tengamos el modelo"  
TOKENIZER_PATH = "tokenizador modelo"

try:
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()  # Modo evaluación
except Exception as e:
    print(f"⚠️ Error cargando modelo/tokenizador: {e}")
    tokenizer = None
    model = None

# Vamos a poner el orden del pipeline para las predicciones: 
def predict_pipeline(youtube_url_or_id, max_comments=100):
    # 1. Extracción
    video_id = extract_video_id(youtube_url_or_id)
    comments = fetch_comment_threads(video_id, max_total=max_comments)
    df = pd.DataFrame(comments)
    if df.empty:
        return {"error": "No se extrajeron comentarios."}

    # 2. Limpieza
    df_clean = clean_youtube_data(df)

    # 3. Tokenización
    texts = df_clean["text"].astype(str).tolist()
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
    # 4. Predicción
    with torch.no_grad():
        outputs = model(**inputs)
        preds = torch.sigmoid(outputs.logits).cpu().numpy()

    # 5. Agrega predicciones al DataFrame
    for i, col in enumerate(model.config.id2label.values()):
        df_clean[col + "_pred"] = preds[:, i]

    # 6. Devuelve resultados
    return {
        "video_id": video_id,
        "comments": df_clean.to_dict(orient="records")
    }