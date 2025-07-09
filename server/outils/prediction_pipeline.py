import pandas as pd
from etl.youtube_extraction import extract_video_id, fetch_comment_threads
from server.outils.cleaning_pipeline import clean_youtube_data
import sys
from pathlib import Path
from server.database.save_comments import save_comments_batch

MODEL_DIR = Path("models/bilstm_advanced")
sys.path.append(str(MODEL_DIR))

# Importamos el loader del modelo
from multitoxic_v1_0_20250709_003639_loader import MultitoxicLoader

print("🔄 Inicializando modelo MULTITOXIC...")
try:
    model_loader = MultitoxicLoader(MODEL_DIR)
    model_loader.load_model()
    print("✅ Modelo MULTITOXIC cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando modelo MULTITOXIC: {e}")
    model_loader = None

#Vamos a poner el orden del pipeline para las predicciones: 
def predict_pipeline(youtube_url_or_id, max_comments=100):
    # 1. Extracción
    video_id = extract_video_id(youtube_url_or_id)
    comments = fetch_comment_threads(video_id, max_total=max_comments)
    
    if not comments:
        return {
            "video_id": video_id,
            "total_comments": 0,
            "stats": {},
            "comments": []
        }
    
    # 2. Guardar en DataFrame EN MEMORIA 
    df = pd.DataFrame(comments)

    # 3. Función de limpieza
    df_clean = clean_youtube_data(df)

    # 4. Verificar que el modelo esté cargado
    if not model_loader:
        raise Exception("Modelo MULTITOXIC no disponible")

    # 5. Predicción fila por fila del DataFrame
    enriched_comments = []
    for _, row in df_clean.iterrows():  
        try:
            # Predicción individual con MULTITOXIC
            prediction = model_loader.predict(
                row["text"], 
                return_probabilities=True, 
                return_categories=False
            )
            # Extraer resultados del modelo
            probs = prediction.get("probabilities", {})
            detected_types = prediction.get("detected_types", [])

            # Construir comentario enriquecido
            comment_data = {
                "video_id": video_id,
                "text": row["text"],
                "toxic_probability": probs.get("toxic", 0.0),
                "hatespeech_probability": probs.get("hatespeech", 0.0),
                "abusive_probability": probs.get("abusive", 0.0),
                "provocative_probability": probs.get("provocative", 0.0),
                "racist_probability": probs.get("racist", 0.0),
                "obscene_probability": probs.get("obscene", 0.0),
                "threat_probability": probs.get("threat", 0.0),
                "religious_hate_probability": probs.get("religious_hate", 0.0),
                "nationalist_probability": probs.get("nationalist", 0.0),
                "sexist_probability": probs.get("sexist", 0.0),
                "homophobic_probability": probs.get("homophobic", 0.0),
                "radicalism_probability": probs.get("radicalism", 0.0),
                "is_toxic": "toxic" in detected_types,
                "is_hatespeech": "hatespeech" in detected_types,
                "is_abusive": "abusive" in detected_types,
                "is_provocative": "provocative" in detected_types,
                "is_racist": "racist" in detected_types,
                "is_obscene": "obscene" in detected_types,
                "is_threat": "threat" in detected_types,
                "is_religious_hate": "religious_hate" in detected_types,
                "is_nationalist": "nationalist" in detected_types,
                "is_sexist": "sexist" in detected_types,
                "is_homophobic": "homophobic" in detected_types,
                "is_radicalism": "radicalism" in detected_types,
                # CAMPOS ADICIONALES DE LIMPIEZA
                "sentiment_type": row.get("sentiment_type"),
                "sentiment_intensity": row.get("sentiment_intensity"),
                "is_self_promotional": row.get("is_self_promotional"),
                "has_url": row.get("has_url"),
                "has_tag": row.get("has_tag"),
                "like_count_comment": row.get("like_count_comment"),
                "reply_count": row.get("reply_count"),
                "author": row.get("author"),
            }
            enriched_comments.append(comment_data)
        except Exception as e:
            print(f"⚠️ Error prediciendo comentario: {e}")
            # Comentario sin predicciones en caso de error
            comment_data = {
                "video_id": video_id,
                "text": row["text"],
                **{f"{field}_probability": 0.0 for field in [
                    "toxic", "hatespeech", "abusive", "provocative", "racist", 
                    "obscene", "threat", "religious_hate", "nationalist", 
                    "sexist", "homophobic", "radicalism"
                ]},
                **{f"is_{field}": False for field in [
                    "toxic", "hatespeech", "abusive", "provocative", "racist", 
                    "obscene", "threat", "religious_hate", "nationalist", 
                    "sexist", "homophobic", "radicalism"
                ]},
                # Campos adicionales con valores por defecto
                "sentiment_type": row.get("sentiment_type", "neutral"),
                "sentiment_intensity": row.get("sentiment_intensity", 0.0),
                "is_self_promotional": row.get("is_self_promotional", False),
                "has_url": row.get("has_url", False),
                "has_tag": row.get("has_tag", False),
                "like_count_comment": row.get("like_count_comment", 0),
                "reply_count": row.get("reply_count", 0),
                "author": row.get("author", "unknown"),
            }
            enriched_comments.append(comment_data)

    # 6. Calcular estadísticas desde los comentarios enriquecidos
    total_comments = len(enriched_comments)
    stats = {}
    
    for field in ["toxic", "hatespeech", "abusive", "provocative", "racist", 
                  "obscene", "threat", "religious_hate", "nationalist", 
                  "sexist", "homophobic", "radicalism"]:
        positives = sum(1 for c in enriched_comments if c.get(f"is_{field}"))
        stats[f"is_{field}"] = {
            "count": positives,
            "percentage": (positives / total_comments * 100) if total_comments else 0
        }

    # 7. Guardar comentarios en supabase
    try:
        print(f"🔄 Guardando {len(enriched_comments)} comentarios en BD...")
        saved_comments = save_comments_batch(enriched_comments)
        print(f"✅ {len(saved_comments)} comentarios guardados exitosamente en BD")
    except Exception as e:
        print(f"⚠️ Error guardando en BD (el pipeline continúa): {e}")


    # 8. Resultado final
    return {
        "video_id": video_id,
        "total_comments": total_comments,
        "stats": stats,
        "comments": enriched_comments
    }

    # 6. Devuelve resultados, el id del video y también una lista de comentarios.
    # result = {
    #     "video_id": video_id,
    #     "total_comments": total_comments,
    #     "stats": stats,
    #     "comments": [
    #         {
    #         "video_id": row.get("video_id", video_id),
    #         "text": row.get("text"),
    #         "is_toxic": row.get("is_toxic"),
    #         "hatespeech_probability": row.get("hatespeech_probability"),
    #         "is_hatespeech": row.get("is_hatespeech"),
    #         "abusive_probability": row.get("abusive_probability"),
    #         "is_abusive": row.get("is_abusive"),
    #         "provocative_probability": row.get("provocative_probability"),
    #         "is_provocative": row.get("is_provocative"),
    #         "racist_probability": row.get("racist_probability"),
    #         "is_racist": row.get("is_racist"),
    #         "obscene_probability": row.get("obscene_probability"),
    #         "is_obscene": row.get("is_obscene"),
    #         "threat_probability": row.get("threat_probability"),
    #         "is_threat": row.get("is_threat"),
    #         "religious_hate_probability": row.get("religious_hate_probability"),
    #         "is_religious_hate": row.get("is_religious_hate"),
    #         "nationalist_probability": row.get("nationalist_probability"),
    #         "is_nationalist": row.get("is_nationalist"),
    #         "sexist_probability": row.get("sexist_probability"),
    #         "is_sexist": row.get("is_sexist"),
    #         "homophobic_probability": row.get("homophobic_probability"),
    #         "is_homophobic": row.get("is_homophobic"),
    #         "radicalism_probability": row.get("radicalism_probability"),
    #         "is_radicalism": row.get("is_radicalism"),
    #         }
    #         for _, row in df_clean.iterrows()
    #     ]
    # }

    # return result


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