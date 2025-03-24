import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.fact_checker import TeapotFactChecker


@pytest.fixture
def fact_checker():
    """Fixture to create and return a TeapotFactChecker instance."""
    return TeapotFactChecker()


def test_factual_response_with_context(fact_checker):
    """Test that the fact checker can verify a statement with provided context"""
    context = """
    The Eiffel Tower is a wrought iron lattice tower in Paris, France. 
    It was designed by Gustave Eiffel and completed in 1889. 
    It stands at a height of 330 meters and is one of the most recognizable structures in the world.
    """
    result = fact_checker.check_fact(
        query="How tall is the Eiffel Tower?", context=context
    )
    assert "330 meters" in result["answer"]
    assert result["factual"] is True
    assert result["confidence"] > 0.5


def test_refusal_without_context(fact_checker):
    """Test that the fact checker refuses to answer without context"""
    result = fact_checker.check_fact(query="When was the Great Wall of China built?")
    assert result["confidence"] < 0.5
