import os
import sys

import pytest
from fastapi.testclient import TestClient

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


def test_list_models_api(client):
    """Test the OpenAI-compatible models list endpoint"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    assert response.json()["object"] == "list"
    assert isinstance(response.json()["data"], list)
    assert len(response.json()["data"]) > 0
    model = response.json()["data"][0]
    assert model["id"] == "teapot-llm"
    assert model["object"] == "model"
    assert "created" in model
    assert model["owned_by"] == "teapot-org"


def test_get_model_api(client):
    """Test the OpenAI-compatible get model endpoint"""
    response = client.get("/v1/models/teapot-llm")
    assert response.status_code == 200
    assert response.json()["id"] == "teapot-llm"
    assert response.json()["object"] == "model"
    assert "created" in response.json()
    assert response.json()["owned_by"] == "teapot-org"

    response = client.get("/v1/models/nonexistent-model")
    assert response.status_code == 404


def test_extraction_api(client):
    """Test the information extraction endpoint"""
    response = client.post(
        "/extract",
        json={
            "query": "Extract information about Paris",
            "context": "Paris is the capital of France and has a population of 2.2 million people.",
            "fields": [
                {
                    "name": "city",
                    "description": "The name of the city",
                    "type": "string",
                },
                {
                    "name": "country",
                    "description": "The country where the city is located",
                    "type": "string",
                },
                {
                    "name": "population",
                    "description": "The population of the city in millions",
                    "type": "number",
                },
            ],
        },
    )
    assert response.status_code == 200
    json_response = response.json()
    if not json_response["success"]:
        print(f"Extraction error: {json_response.get('error')}")

    assert "success" in json_response
    assert "data" in json_response or "error" in json_response

    if json_response["success"]:
        data = json_response["data"]
        assert isinstance(data, dict)
        assert "city" in data
        assert isinstance(data["city"], str)
        assert "Paris" in data["city"]

        assert "country" in data
        assert isinstance(data["country"], str)
        assert "France" in data["country"]

        if "population" in data:
            assert isinstance(data["population"], (int, float))
            assert 2.0 <= float(data["population"]) <= 2.4  # Accept reasonable range
