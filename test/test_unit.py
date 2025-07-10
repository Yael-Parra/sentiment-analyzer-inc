# ==============================  Importing libraries  ============================
import pytest
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
from etl.youtube_extraction import fetch_comment_threads
import server.database.connection_db as connection_db
import server.database.save_comments as save_comments
from server.database import save_comments
from server.outils.pipeline_prediction import predict_pipeline 
from server.database.save_comments import save_comment,save_comments_batch,get_comments_by_video,delete_comments_by_video
from server.outils.pipeline_cleaning import clean_youtube_data, analyze_sentiment
from server.outils.pipeline_unified import UnifiedPipeline
# ==============================  Cleaning Pipeline  ==============================
def test_pipeline():
    print("🚀 Iniciando pruebas del UnifiedPipeline...")
    pipeline = UnifiedPipeline()
    
    # Datos de prueba COMPLETOS que simulan la salida real de clean_youtube_data
    test_data = {
        "text": ["Great video!", "Bad content"],
        "sentiment_type": ["positive", "negative"],  # Columnas requeridas
        "sentiment_intensity": ["strong", "moderate"],
        "published_at_comment": pd.to_datetime(["2024-01-01 12:00", "2024-01-01 18:00"]),
        "is_self_promotional": [False, False]
    }
    
    # Convertir a DataFrame
    df_clean = pd.DataFrame(test_data)
    
    print("\n🧪 Probando _enrich_comments() con datos COMPLETOS")
    enriched = pipeline._enrich_comments(df_clean, "test_video")
    
    if not enriched:
        print("❌ Falla - Lista vacía")
        return False
    
    print(f"✅ Comentarios enriquecidos: {len(enriched)}")
    print("Muestra:", enriched[0])
    
    # Prueba de stats
    print("\n🧪 Probando _calculate_stats()")
    stats = pipeline._calculate_stats(enriched)
    print("Estadísticas generadas:", stats.keys())
    
    return True

# =============================  YouTube Extraction  =============================
@patch("etl.youtube_extraction.requests.get")
def test_fetch_comment_threads(mock_get):
    # Simular respuesta de la API de YouTube
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "thread1",
                "snippet": {
                    "topLevelComment": {
                        "snippet": {
                            "authorDisplayName": "Test User",
                            "authorChannelId": {"value": "channel123"},
                            "publishedAt": "2022-01-01T00:00:00Z",
                            "textDisplay": "This is a test comment.",
                            "likeCount": 5
                        }
                    },
                    "totalReplyCount": 0
                }
            }
        ]
    }

    mock_get.return_value = mock_response

    comments = fetch_comment_threads("dQw4w9WgXcQ", max_total=1, delay=0)

    assert isinstance(comments, list)
    assert len(comments) == 1
    assert comments[0]["author"] == "Test User"
    assert comments[0]["text"] == "This is a test comment."

# # =================================  Predictions  =================================
# def test_predict_pipeline_mock_output_structure():
#     result = predict_pipeline("dummy_url", max_comments=5)

#     assert isinstance(result, dict)
#     assert "video_id" in result
#     assert "total_comments" in result
#     assert result["total_comments"] == 5
#     assert "stats" in result
#     assert "comments" in result
#     assert isinstance(result["comments"], list)
#     assert len(result["comments"]) == 5

#     comment = result["comments"][0]
#     expected_keys = {
#         "video_id", "text", "toxic_probability", "is_toxic",
#         "hatespeech_probability", "is_hatespeech", "abusive_probability", "is_abusive",
#         "provocative_probability", "is_provocative", "racist_probability", "is_racist",
#         "obscene_probability", "is_obscene", "threat_probability", "is_threat",
#         "religious_hate_probability", "is_religious_hate", "nationalist_probability", "is_nationalist",
#         "sexist_probability", "is_sexist", "homophobic_probability", "is_homophobic",
#         "radicalism_probability", "is_radicalism"
#     }
#     assert expected_keys.issubset(comment.keys())
# Sentiments -----------------------------------------------------------------------------------
def test_sentiment_vader():
    # Positive text
    result = analyze_sentiment("I love this product!")
    assert result['sentiment_type'] == 'positive'
    assert result['sentiment_intensity'] > 0

    # Negative text
    result = analyze_sentiment("I hate this so much.")
    assert result['sentiment_type'] == 'negative'
    assert result['sentiment_intensity'] < 0

    # Neutral text
    result = analyze_sentiment("It is a product.")
    assert result['sentiment_type'] == 'neutral'
    assert abs(result['sentiment_intensity']) < 0.05

    # Empty string or non-string input should be neutral
    result = analyze_sentiment("")
    assert result['sentiment_type'] == 'neutral'
    result = analyze_sentiment(None)
    assert result['sentiment_type'] == 'neutral'
# =============================  Data Base  =============================
# Data Base Connection -------------------------------------------------------------------------
@patch.object(connection_db.supabase, "table")
def test_connection_success(mock_table):
    mock_execute = MagicMock()
    mock_execute.data = [{}]
    mock_table.return_value.select.return_value.execute.return_value = mock_execute

    result = connection_db.test_connection()
    assert result is True

# Data Base Insertion -------------------------------------------------------------------------
@patch("server.database.save_comments.supabase")
def test_save_comment_valid(mock_supabase):
    # Mock response: simula lo que Supabase devuelve tras insertar
    mock_response = MagicMock()
    mock_response.data = [{
        "id": 123,
        "video_id": "test_video",
        "text": "Comentario válido"
    }]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response

    # Datos mínimos válidos según tu modelo (comment_id es ignorado al guardar)
    comment = {
        "video_id": "test_video",
        "text": "Comentario válido"
    }

    result = save_comments.save_comment(comment)

    # Validaciones
    assert result is not None
    assert result["video_id"] == "test_video"
    assert result["text"] == "Comentario válido"
# ----------------------------------------------
def test_save_comment_invalid():
    comment = {
        "text": "Falta el video_id"  # video_id es obligatorio según schema por lo que debería de ser inválido esto
    }

    result = save_comments.save_comment(comment)

    assert result is None
# ----------------------------------------------
# Get comment by video_id
# def test_get_comments_by_video_id (video_id:str)  -> List[Dict[str, Any]]:
#     try:

# ----------------------------------------------
@patch.object(connection_db.supabase, "table")
def test_get_comments_by_video(mock_table):
    mock_response = MagicMock()
    mock_response.data = [{"text": "Comentario 1"}, {"text": "Comentario 2"}]
    mock_table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    result = save_comments.get_comments_by_video("video_test")
    assert len(result) == 2
    assert result[0]["text"] == "Comentario 1"
# ----------------------------------------------
@patch.object(connection_db.supabase, "table")
def test_delete_comments_by_video(mock_table):
    mock_response = MagicMock()
    mock_table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response

    result = save_comments.delete_comments_by_video("video_test")
    assert result is True
# ----------------------------------------------
if __name__ == "__main__":
    import sys
    import pytest

# Ejecuta pytest en este archivo con salida detallada (-v)
    sys.exit(pytest.main([__file__, "-v"]))
