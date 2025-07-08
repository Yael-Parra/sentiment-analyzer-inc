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

#Vamos a poner el orden del pipeline para las predicciones: 
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

    # 6. Estadísticas por etiqueta

    total_comments = len(df_clean)
    stats = {}
    for col in model.config.id2label.values():
        positives = (df_clean[col + "_pred"] > 0.5).sum()
        stats[col] = {
            "count": int(positives),
            "percentage": float(positives) / total_comments * 100 if total_comments > 0 else 0
        }

    # 6. Devuelve resultados, el id del video y también una lista de comentarios.
    result = {
        "video_id": video_id,
        "total_comments": total_comments,
        "stats": stats,
        "comments": [
            {
            "video_id": row.get("video_id", video_id),
            "text": row.get("text"),
            "is_toxic": row.get("is_toxic"),
            "hatespeech_probability": row.get("hatespeech_probability"),
            "is_hatespeech": row.get("is_hatespeech"),
            "abusive_probability": row.get("abusive_probability"),
            "is_abusive": row.get("is_abusive"),
            "provocative_probability": row.get("provocative_probability"),
            "is_provocative": row.get("is_provocative"),
            "racist_probability": row.get("racist_probability"),
            "is_racist": row.get("is_racist"),
            "obscene_probability": row.get("obscene_probability"),
            "is_obscene": row.get("is_obscene"),
            "threat_probability": row.get("threat_probability"),
            "is_threat": row.get("is_threat"),
            "religious_hate_probability": row.get("religious_hate_probability"),
            "is_religious_hate": row.get("is_religious_hate"),
            "nationalist_probability": row.get("nationalist_probability"),
            "is_nationalist": row.get("is_nationalist"),
            "sexist_probability": row.get("sexist_probability"),
            "is_sexist": row.get("is_sexist"),
            "homophobic_probability": row.get("homophobic_probability"),
            "is_homophobic": row.get("is_homophobic"),
            "radicalism_probability": row.get("radicalism_probability"),
            "is_radicalism": row.get("is_radicalism"),
            }
            for _, row in df_clean.iterrows()
        ]
    }

    return result


######## Función para el mockeo, está probado y funciona:
# def predict_pipeline(youtube_url_or_id, max_comments=100):
#     comments = [
#         {
#             "video_id": "mock_video_id",
#             "text": f"Comentario de prueba {i+1}",
#             "toxic_probability": 0.5, 
#             "is_toxic": bool(i % 2),
#             "hatespeech_probability": 0.1 * i,
#             "is_hatespeech": i % 3 == 0,
#             "abusive_probability": 0.2 * i,
#             "is_abusive": i % 4 == 0,
#             "provocative_probability": 0.05 * i,
#             "is_provocative": i % 5 == 0,
#             "racist_probability": 0.0,
#             "is_racist": False,
#             "obscene_probability": 0.0,
#             "is_obscene": False,
#             "threat_probability": 0.0,
#             "is_threat": False,
#             "religious_hate_probability": 0.0,
#             "is_religious_hate": False,
#             "nationalist_probability": 0.0,
#             "is_nationalist": False,
#             "sexist_probability": 0.0,
#             "is_sexist": False,
#             "homophobic_probability": 0.0,
#             "is_homophobic": False,
#             "radicalism_probability": 0.0,
#             "is_radicalism": False,
#         }
#         for i in range(max_comments)
#     ]

#     stats = {
#         "is_toxic": {
#             "count": sum(c["is_toxic"] for c in comments),
#             "percentage": 100.0 * sum(c["is_toxic"] for c in comments) / max_comments if max_comments else 0
#         },
#         "is_hatespeech": {
#             "count": sum(c["is_hatespeech"] for c in comments),
#             "percentage": 100.0 * sum(c["is_hatespeech"] for c in comments) / max_comments if max_comments else 0
#         },
#     }

#     result = {
#         "video_id": "mock_video_id",
#         "total_comments": max_comments,
#         "stats": stats,
#         "comments": comments,
#     }
#     return result