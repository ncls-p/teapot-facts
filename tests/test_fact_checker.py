import os
import sys
import unittest

# Add the parent directory to sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.fact_checker import TeapotFactChecker


class TestFactChecker(unittest.TestCase):
    def setUp(self):
        self.fact_checker = TeapotFactChecker()

    def test_factual_response_with_context(self):
        """Test that the fact checker can verify a statement with provided context"""
        context = """
        The Eiffel Tower is a wrought iron lattice tower in Paris, France. 
        It was designed by Gustave Eiffel and completed in 1889. 
        It stands at a height of 330 meters and is one of the most recognizable structures in the world.
        """

        result = self.fact_checker.check_fact(
            query="How tall is the Eiffel Tower?", context=context
        )

        self.assertIn("330 meters", result["answer"])
        self.assertTrue(result["factual"])
        self.assertGreater(result["confidence"], 0.5)

    def test_refusal_without_context(self):
        """Test that the fact checker refuses to answer without context"""
        result = self.fact_checker.check_fact(
            query="When was the Great Wall of China built?"
        )

        # The model should indicate it cannot answer without context
        self.assertLess(result["confidence"], 0.5)


if __name__ == "__main__":
    unittest.main()
