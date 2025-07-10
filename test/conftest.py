# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from server.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_youtube_url():
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def mock_comment_list():
    return [
        "This video is amazing!",
        "Worst thing I've seen",
        "You're such a moron."
    ]
