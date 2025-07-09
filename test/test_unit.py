# Importing libraries -------------------------------------------------------------------------
import pytest
from server.outils.cleaning_pipeline import clean_text
from server.outils.prediction_pipeline import predict_sentiment, predict_toxicity
from unittest.mock import patch
from server.database.connection_db import test_connection
from unittest.mock import patch, MagicMock
import server.database.connection_db as db
from etl.youtube_extraction import fetch_comment_threads
# --------------------------------------------------------------------------------------------
def test_clean_text_removes_special_characters():
    text = "Hello!!! 😡🔥🔥 This is... weird."
    cleaned = clean_text(text)
    assert "!" not in cleaned
    assert "🔥" not in cleaned
    assert "😡" not in cleaned
# --------------------------------------------------------------------------------------------
def test_predict_sentiment_format():
    result = predict_sentiment("I hate everything.")
    assert "sentiment" in result
    assert result["sentiment"] in ["positive", "neutral", "negative"]

# YouTube Extraction --------------------------------------------------------------------------
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


# Data Base Connection -------------------------------------------------------------------------

@patch.object(db.supabase, "table")
def test_test_connection_success(mock_table):
    # Mock chain: .select().execute() → response.data = [{}]
    mock_select = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = [{}]
    mock_select.execute.return_value = mock_execute
    mock_table.return_value.select.return_value = mock_select

    result = db.test_connection()
    assert result is True
