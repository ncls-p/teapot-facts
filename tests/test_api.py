import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add the parent directory to sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model"] == "teapotllm"


def test_completion_api(client):
    """Test the OpenAI-compatible completion endpoint"""
    response = client.post(
        "/v1/completions",
        json={
            "model": "teapotllm",
            "prompt": "What is the capital of France?",
            "max_tokens": 50,
        },
    )
    assert response.status_code == 200
    assert "choices" in response.json()
    assert "text" in response.json()["choices"][0]
    assert "fact_check" in response.json()


def test_chat_completion_api(client):
    """Test the OpenAI-compatible chat completion endpoint"""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "teapotllm",
            "messages": [
                {
                    "role": "system",
                    "content": "Context: Paris is the capital of France.",
                },
                {"role": "user", "content": "What is the capital of France?"},
            ],
        },
    )
    assert response.status_code == 200
    assert "choices" in response.json()
    assert "message" in response.json()["choices"][0]
    assert "content" in response.json()["choices"][0]["message"]
    assert "fact_check" in response.json()
    assert response.json()["fact_check"]["factual"] is True


def test_fact_check_api(client):
    """Test the direct fact-checking endpoint"""
    response = client.post(
        "/fact-check",
        json={
            "query": "How tall is the Eiffel Tower?",
            "context": "The Eiffel Tower is 330 meters tall and located in Paris, France.",
        },
    )
    assert response.status_code == 200
    assert "factual" in response.json()
    assert "answer" in response.json()
    assert "confidence" in response.json()
    assert response.json()["factual"] is True
    assert "330 meters" in response.json()["answer"]
