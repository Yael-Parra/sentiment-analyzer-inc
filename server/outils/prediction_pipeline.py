import pandas as pd
from etl.youtube_extraction import extract_video_id, fetch_comment_threads
from server.outils.cleaning_pipeline import clean_youtube_data
import sys
from pathlib import Path
from server.schemas import Comment, PredictionStats, PredictionResponse
from server.database.save_comments import save_comments_batch
from typing import List, Dict, Any

MODEL_DIR = Path("models/bilstm_advanced")
sys.path.append(str(MODEL_DIR))

from multitoxic_v1_0_20250709_003639_loader import MultitoxicLoader

print("🔄 Inicializando modelo MULTITOXIC...")
try:
    model_loader = MultitoxicLoader(MODEL_DIR)
    model_loader.load_model()
    print("✅ Modelo MULTITOXIC cargado exitosamente")
except Exception as e:
    print(f"❌ Error cargando modelo MULTITOXIC: {e}")
    model_loader = None

TOXICITY_FIELDS = [
    "toxic", "hatespeech", "abusive", "provocative", "racist", 
    "obscene", "threat", "religious_hate", "nationalist", 
    "sexist", "homophobic", "radicalism"
]

def _create_comment_from_error(video_id: str, row: pd.Series) -> Comment:
    return Comment(
        video_id=video_id,
        text=row["text"],
        # Todos los Optional van a None automáticamente por Pydantic
        sentiment_type=row.get("sentiment_type", "neutral"),
        sentiment_score=row.get("sentiment_score", 0.0),
        sentiment_intensity=row.get("sentiment_intensity", "weak"), 
        total_likes_comment=row.get("like_count_comment", 0),
    )

def _calculate_toxicity_stats(comments: List[Comment]) -> Dict[str, PredictionStats]:
    """
    Calcula estadísticas de toxicidad usando objetos Comment
    """
    total_comments = len(comments)
    stats = {}
    
    for field in TOXICITY_FIELDS:
        # ✅ USAR ATRIBUTOS DE OBJETOS COMMENT
        positives = sum(1 for c in comments if getattr(c, f"is_{field}", False))
        stats[f"is_{field}"] = PredictionStats(
            count=positives,
            percentage=(positives / total_comments * 100) if total_comments else 0
        )
    
    return stats


def _calculate_sentiment_stats(comments: List[Comment]) -> Dict[str, Any]:
  
    # ✅ USAR ATRIBUTOS DE OBJETOS COMMENT
    sentiment_scores = [c.sentiment_score for c in comments 
                       if c.sentiment_score is not None]  # ← ANTES: sentiment_intensity
    mean_sentiment_score = (sum(sentiment_scores) / len(sentiment_scores) 
                           if sentiment_scores else 0.0)  # ← ANTES: mean_sentiment_intensity
    
    sentiment_counts = {}
    for c in comments:
        stype = c.sentiment_type or "neutral"
        sentiment_counts[stype] = sentiment_counts.get(stype, 0) + 1
    

    return {
        "mean_sentiment_score": mean_sentiment_score,
        "sentiment_types_distribution": sentiment_counts,
    }

def _calculate_basic_stats(comments: List[Comment]) -> Dict[str, Any]:
    """
    Calcula estadísticas básicas que van directamente a la tabla video_statistics
    """
    total_comments = len(comments)
    
    # Likes
    total_likes = sum(c.total_likes_comment or 0 for c in comments)
    mean_likes = total_likes / total_comments if total_comments else 0
    max_likes = max((c.total_likes_comment or 0 for c in comments), default=0)
    
    # Self promotion
    # self_promotion = sum(1 for c in comments if c.is_self_promotional)
    
    # Toxicity percentage
    tagged_comments = sum(1 for c in comments 
                         if any(getattr(c, f"is_{field}", False) for field in TOXICITY_FIELDS))
    percentage_tagged = (tagged_comments / total_comments * 100) if total_comments else 0
    
    return {
        "total_comments": total_comments,
        "total_likes": total_likes,
        "mean_likes": mean_likes,
        "max_likes": max_likes,
        # "self_promotion": self_promotion,
        "percentage_tagged": percentage_tagged
    }

#Vamos a poner el orden del pipeline para las predicciones: 
def predict_pipeline(youtube_url_or_id: str, max_comments: int = 100) -> PredictionResponse:
    # 1. Extracción
    video_id = extract_video_id(youtube_url_or_id)
    comments = fetch_comment_threads(video_id, max_total=max_comments)
    
    if not comments:
        return PredictionResponse(
            video_id=video_id,
            total_comments=0,
            stats={},
            complete_stats={},
            comments=[]
            
        )
    
    # 2. Guardar en DataFrame EN MEMORIA 
    df = pd.DataFrame(comments)

    # 3. Función de limpieza
    df_clean = clean_youtube_data(df)

    print(f"🔍 Columnas después de cleaning: {df_clean.columns.tolist()}")
    print(f"🔍 Sample like_count_comment: {df_clean['like_count_comment'].head().tolist()}")
    print(f"🔍 Total likes en DataFrame: {df_clean['like_count_comment'].sum()}")
    # 4. Verificar que el modelo esté cargado
    if not model_loader:
        raise Exception("Modelo MULTITOXIC no disponible")
    
    self_promotional_count = df_clean['is_self_promotional'].sum() if 'is_self_promotional' in df_clean.columns else 0
    
    # 5. Predicción fila por fila del DataFrame
    enriched_comments: List[Comment] = []        
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
            comment_obj = Comment(
                video_id=video_id,
                text=row["text"],
                # USAR DICT COMPREHENSION PARA PROBABILIDADES
                **{f"{field}_probability": probs.get(field, 0.0) for field in TOXICITY_FIELDS},
                # USAR DICT COMPREHENSION PARA BOOLEANOS
                **{f"is_{field}": field in detected_types for field in TOXICITY_FIELDS},
                # Análisis de sentimientos (del cleaning pipeline)
                sentiment_type=row.get("sentiment_type"),
                sentiment_score=row.get("sentiment_score"),
                sentiment_intensity=row.get("sentiment_intensity"), 
                total_likes_comment=row.get("like_count_comment", 0),
            )
            enriched_comments.append(comment_obj)

        except Exception as e:
            print(f"⚠️ Error prediciendo comentario: {e}")
            # Comentario sin predicciones en caso de error
            error_comment = _create_comment_from_error(video_id, row)
            enriched_comments.append(error_comment)

    # 6. Calcular estadísticas desde los comentarios enriquecidos
    toxicity_stats = _calculate_toxicity_stats(enriched_comments)
    sentiment_stats = _calculate_sentiment_stats(enriched_comments)
    basic_stats = _calculate_basic_stats(enriched_comments)
    stats_dict = {k: {"count": v.count, "percentage": v.percentage} 
                  for k, v in toxicity_stats.items()}


    complete_stats = {
        # Campos directos para video_statistics
        "total_comments": basic_stats["total_comments"],
        "mean_likes": basic_stats["mean_likes"],
        "max_likes": basic_stats["max_likes"],
        "total_likes": basic_stats["total_likes"],
        "self_promotional": int(self_promotional_count), 
        "percentage_tagged": basic_stats["percentage_tagged"],
        
        # Campos JSON para video_statistics
        "sentiment_distribution": sentiment_stats["sentiment_types_distribution"],
        "toxicity_stats": {
            f"is_{field}": {
                "true": toxicity_stats[f"is_{field}"].count, 
                "false": len(enriched_comments) - toxicity_stats[f"is_{field}"].count
            } for field in TOXICITY_FIELDS
        },
        "mean_sentiment_score": sentiment_stats["mean_sentiment_score"],
    }

    
    # 7. Guardar comentarios en supabase
    try:
        print(f"🔄 Guardando {len(enriched_comments)} comentarios en BD...")
        enriched_dicts = [comment.model_dump() for comment in enriched_comments]
        saved_comments = save_comments_batch(enriched_dicts)
        print(f"✅ {len(saved_comments)} comentarios guardados exitosamente en BD")
    except Exception as e:
        print(f"⚠️ Error guardando en BD (el pipeline continúa): {e}")

    try:
        from server.database.save_comments import save_video_statistics
        print(f"📊 Guardando estadísticas del video...")
        saved_stats = save_video_statistics(video_id, complete_stats)
        print(f"✅ Estadísticas del video guardadas exitosamente")
    except Exception as e:
        print(f"⚠️ Error guardando estadísticas del video (el pipeline continúa): {e}")

    # 8. Resultado final
    return PredictionResponse(
        video_id=video_id,
        total_comments=len(enriched_comments),
        stats=stats_dict,
        complete_stats=complete_stats,
        comments=enriched_comments  
    )

