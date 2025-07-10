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
        sentiment_intensity=row.get("sentiment_intensity", 0.0),
        is_self_promotional=row.get("is_self_promotional", False),
        has_url=row.get("has_url", False),
        has_tag=row.get("has_tag", False),
        like_count_comment=row.get("like_count_comment", 0),
        reply_count=row.get("reply_count", 0),
        author=row.get("author", "unknown"),
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
    sentiment_intensities = [c.sentiment_intensity for c in comments 
                            if c.sentiment_intensity is not None]
    mean_sentiment_intensity = (sum(sentiment_intensities) / len(sentiment_intensities) 
                               if sentiment_intensities else 0.0)
    
    sentiment_counts = {}
    for c in comments:
        stype = c.sentiment_type or "neutral"
        sentiment_counts[stype] = sentiment_counts.get(stype, 0) + 1
    
    return {
        "mean_sentiment_intensity": mean_sentiment_intensity,
        "sentiment_types_distribution": sentiment_counts
    }


def _calculate_engagement_stats(comments: List[Comment]) -> Dict[str, Any]:

    total_comments = len(comments)
    
    # ✅ USAR ATRIBUTOS DE OBJETOS COMMENT
    comments_with_urls = sum(1 for c in comments if c.has_url)
    comments_with_tags = sum(1 for c in comments if c.has_tag)
    mean_likes = sum(c.like_count_comment or 0 for c in comments) / total_comments if total_comments else 0
    max_likes = max((c.like_count_comment or 0 for c in comments), default=0)
    
    # Porcentaje de comentarios con algún tag de toxicidad
    tagged_comments = sum(1 for c in comments 
                         if any(getattr(c, f"is_{field}", False) for field in TOXICITY_FIELDS))
    porcentaje_tagged = (tagged_comments / total_comments * 100) if total_comments else 0
    
    return {
        "comments_with_urls": comments_with_urls,
        "comments_with_tags": comments_with_tags,
        "url_percentage": (comments_with_urls / total_comments * 100) if total_comments else 0,
        "tag_percentage": (comments_with_tags / total_comments * 100) if total_comments else 0,
        "mean_likes": mean_likes,
        "max_likes": max_likes,
        "porcentaje_tagged": porcentaje_tagged
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
            comments=[]
        )
    
    # 2. Guardar en DataFrame EN MEMORIA 
    df = pd.DataFrame(comments)

    # 3. Función de limpieza
    df_clean = clean_youtube_data(df)

    # 4. Verificar que el modelo esté cargado
    if not model_loader:
        raise Exception("Modelo MULTITOXIC no disponible")

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
                sentiment_intensity=row.get("sentiment_intensity"),
                # Campos adicionales
                is_self_promotional=row.get("is_self_promotional"),
                has_url=row.get("has_url"),
                has_tag=row.get("has_tag"),
                like_count_comment=row.get("like_count_comment"),
                reply_count=row.get("reply_count"),
                author=row.get("author"),
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
    engagement_stats = _calculate_engagement_stats(enriched_comments)
    
    stats_dict = {k: {"count": v.count, "percentage": v.percentage} 
                  for k, v in toxicity_stats.items()}


    complete_stats = {
        "cantidad_comentarios": len(enriched_comments),
        "barras_toxicidad": {
            f"is_{field}": {
                "true": toxicity_stats[f"is_{field}"].count, 
                "false": len(enriched_comments) - toxicity_stats[f"is_{field}"].count
            } for field in TOXICITY_FIELDS
        },
        "sentimientos": sentiment_stats,
        "porcentaje_tagged": engagement_stats["porcentaje_tagged"],
        "mean_likes": engagement_stats["mean_likes"],
        "max_likes": engagement_stats["max_likes"],
        "engagement_stats": {
            k: v for k, v in engagement_stats.items() 
            if k not in ["mean_likes", "max_likes", "porcentaje_tagged"]
        }
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
        comments=enriched_comments  
    )

