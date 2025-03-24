"""
TeapotFacts API - Fact checking with OpenAI-compatible API using TeapotLLM
"""

from .api import app
from .fact_checker import TeapotFactChecker

__all__ = ["TeapotFactChecker", "app"]
