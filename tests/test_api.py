import os
import sys
import unittest

from fastapi.testclient import TestClient

# Add the parent directory to sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["model"], "teapotllm")

    def test_completion_api(self):
        """Test the OpenAI-compatible completion endpoint"""
        response = self.client.post(
            "/v1/completions",
            json={
                "model": "teapotllm",
                "prompt": "What is the capital of France?",
                "max_tokens": 50,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("choices", response.json())
        self.assertIn("text", response.json()["choices"][0])
        self.assertIn("fact_check", response.json())

    def test_chat_completion_api(self):
        """Test the OpenAI-compatible chat completion endpoint"""
        response = self.client.post(
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
        self.assertEqual(response.status_code, 200)
        self.assertIn("choices", response.json())
        self.assertIn("message", response.json()["choices"][0])
        self.assertIn("content", response.json()["choices"][0]["message"])
        self.assertIn("fact_check", response.json())
        self.assertTrue(response.json()["fact_check"]["factual"])

    def test_fact_check_api(self):
        """Test the direct fact-checking endpoint"""
        response = self.client.post(
            "/fact-check",
            json={
                "query": "How tall is the Eiffel Tower?",
                "context": "The Eiffel Tower is 330 meters tall and located in Paris, France.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("factual", response.json())
        self.assertIn("answer", response.json())
        self.assertIn("confidence", response.json())
        self.assertTrue(response.json()["factual"])
        self.assertIn("330 meters", response.json()["answer"])


if __name__ == "__main__":
    unittest.main()
