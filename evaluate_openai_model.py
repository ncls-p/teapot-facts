import argparse
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, cast

import openai
from datasets import (
    Dataset,
    DatasetDict,
    IterableDataset,
    IterableDatasetDict,
    load_dataset,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from rich.console import Console
from rich.progress import track
from rich.table import Table

from app.services.fact_checker_utils import (
    contains_refusal_phrases,
    estimate_confidence,
    process_sources,
)


class OpenAIFactChecker:
    """
    Fact checker using OpenAI models via their API.
    This reimplements the core functionality of TeapotFactChecker but using OpenAI's models.
    """

    def __init__(self, api_key=None, base_url=None, model="gpt-3.5-turbo"):
        """
        Initialize the OpenAI client
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Base URL for the API (defaults to OPENAI_API_BASE env var or OpenAI's default)
            model: Model to use (defaults to gpt-3.5-turbo)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_API_BASE")

        # Create client with only the necessary parameters to avoid type errors
        client_kwargs = {}
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = openai.OpenAI(**client_kwargs)
        self.model = model
        self.stored_documents = []

    def check_fact(
        self,
        query: str,
        context: Optional[str] = None,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if a statement is factual based on provided context
        Args:
            query: The statement or question to verify
            context: Optional text context to use for verification
            documents: Optional list of documents for RAG-based verification
        Returns:
            Dictionary with verification results
        """
        try:
            if documents:
                return self._process_with_documents(query, documents)
            elif context:
                return self._process_with_context(query, context)
            else:
                return self._process_without_context(query)
        except Exception as e:
            return {
                "factual": False,
                "answer": f"Error occurred during fact checking: {str(e)}",
                "confidence": 0.1,
                "sources": [],
            }

    def _process_with_documents(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a query using RAG with provided documents"""
        self.stored_documents = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            self.stored_documents.append({"content": content, "metadata": metadata})

        combined_context = "\n\n".join(
            [
                doc.get("content", "")
                for doc in self.stored_documents
                if doc.get("content")
            ]
        )

        if not combined_context:
            return self._process_without_context(query)

        return self._process_with_context(query, combined_context)

    def _process_with_context(self, query: str, context: str) -> Dict[str, Any]:
        """Process a query with provided context"""
        system_message = (
            "You are a highly accurate and factual assistant. "
            "Please analyze the following statement based on the context provided. "
            "Determine if the statement is factually correct according to the context. "
            "Be concise and focus only on facts from the provided context."
        )

        # Create properly typed messages for the OpenAI API
        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system_message),
            ChatCompletionUserMessageParam(
                role="user",
                content=f"Context: {context}\n\nStatement to verify: {query}",
            ),
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,  # Low temperature for more factual responses
            max_tokens=150,
        )

        result = response.choices[0].message.content
        if result is None:
            result = "No response generated."

        return self._process_result(result, has_context=True)

    def _process_without_context(self, query: str) -> Dict[str, Any]:
        """Process a query without context (likely to get hallucination resistance)"""
        system_message = (
            "You are a highly accurate and factual assistant. "
            "Please analyze the following statement. "
            "If you don't have enough information to verify it, clearly state that. "
            "Be concise and focus only on facts you are certain about."
        )

        # Create properly typed messages for the OpenAI API
        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system_message),
            ChatCompletionUserMessageParam(
                role="user", content=f"Statement to verify: {query}"
            ),
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,  # Low temperature for more factual responses
            max_tokens=150,
        )

        result = response.choices[0].message.content
        if result is None:
            result = "No response generated."

        return self._process_result(result, has_context=False)

    def _process_result(self, result: str, has_context: bool = True) -> Dict[str, Any]:
        """Process the result from the API response"""
        is_factual = not contains_refusal_phrases(result)
        confidence = estimate_confidence(result, has_context)
        sources = process_sources(self.stored_documents, None)

        return {
            "factual": is_factual,
            "answer": result,
            "confidence": confidence,
            "sources": sources,
        }


def evaluate_fact_checking(
    fact_checker: OpenAIFactChecker,
    blogs: Sequence[Dict[str, Any]],
    num_samples: int = 10,
) -> Dict:
    """
    Evaluate the fact checker on blog posts and their key points
    Args:
        fact_checker: The OpenAIFactChecker instance
        blogs: Sequence of blog posts with key points
        num_samples: Number of samples to evaluate (default: 10)
    Returns:
        Dictionary with evaluation metrics and detailed results
    """
    total_correct = 0
    total_confidence = 0
    results = []

    evaluation_samples = list(blogs)[:num_samples]

    for blog in track(evaluation_samples, description="Evaluating samples"):
        text = blog["input"]
        key_points = blog["output"].strip().split("\n")

        blog_results = []
        for point in key_points:
            # Add a small delay to avoid API rate limits
            time.sleep(0.5)

            result = fact_checker.check_fact(query=point, context=text)
            is_correct = result["factual"] and result["confidence"] > 0.7
            total_correct += int(is_correct)
            total_confidence += result["confidence"]

            blog_results.append(
                {
                    "key_point": point,
                    "factual": result["factual"],
                    "confidence": result["confidence"],
                    "correct": is_correct,
                    "model_answer": result["answer"],
                }
            )

        results.append(
            {
                "blog_text": text[:200] + "..." if len(text) > 200 else text,
                "key_points_results": blog_results,
            }
        )

    total_points = sum(
        len(blog["output"].strip().split("\n")) for blog in evaluation_samples
    )

    metrics = {
        "accuracy": total_correct / total_points,
        "avg_confidence": total_confidence / total_points,
        "total_samples": total_points,
        "total_blogs": len(evaluation_samples),
        "evaluation_date": datetime.now().isoformat(),
        "results": results,
    }

    return metrics


def generate_report(
    metrics: Dict, console: Console, output_json: Optional[str] = None
) -> None:
    """Generate a rich formatted report and optionally save detailed results to JSON"""
    console.print("\n[bold blue]OpenAI Model Evaluation Report[/bold blue]")
    console.print(f"\nDate: {metrics['evaluation_date']}")
    console.print(f"Total blogs evaluated: {metrics['total_blogs']}")
    console.print(f"Total key points evaluated: {metrics['total_samples']}")

    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="magenta")

    metrics_table.add_row("Accuracy", f"{metrics['accuracy']:.2%}")
    metrics_table.add_row("Average Confidence", f"{metrics['avg_confidence']:.2f}")

    console.print(metrics_table)

    results_table = Table(title="Sample Results")
    results_table.add_column("Key Point", style="cyan")
    results_table.add_column("Factual", style="green")
    results_table.add_column("Confidence", style="blue")
    results_table.add_column("Correct", style="magenta")

    sample_count = 0
    for blog_result in metrics["results"]:
        for key_point_result in blog_result["key_points_results"]:
            if sample_count >= 5:
                break

            results_table.add_row(
                key_point_result["key_point"][:50] + "..."
                if len(key_point_result["key_point"]) > 50
                else key_point_result["key_point"],
                "✓" if key_point_result["factual"] else "✗",
                f"{key_point_result['confidence']:.2f}",
                "✓" if key_point_result["correct"] else "✗",
            )
            sample_count += 1

    console.print(results_table)

    if output_json:
        with open(output_json, "w") as f:
            json.dump(metrics, f, indent=2)
        console.print(f"\n[green]Detailed results saved to {output_json}[/green]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate OpenAI models on blog key points dataset"
    )
    parser.add_argument(
        "--samples", type=int, default=10, help="Number of blog samples to evaluate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="openai_evaluation_results.json",
        help="Output JSON file for detailed results",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-3.5-turbo",
        help="OpenAI model to use (default: gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for the API (defaults to OPENAI_API_BASE env var)",
    )
    args = parser.parse_args()

    console = Console()
    console.print("[bold]Loading dataset and initializing model...[/bold]")

    # Ensure API key is set
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("OPENAI_API_BASE"):
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        console.print("Please set it with: export OPENAI_API_KEY=your_api_key")
        return

    try:
        dataset = load_dataset("ncls-p/blog-key-points")
        if not isinstance(dataset, (DatasetDict, IterableDatasetDict)):
            raise TypeError(
                "Expected dataset to be a DatasetDict or IterableDatasetDict"
            )

        train_split = dataset["train"]
        if not isinstance(train_split, (Dataset, IterableDataset)):
            raise TypeError("Expected train split to be a Dataset or IterableDataset")

        train_data = [cast(Dict[str, Any], item) for item in train_split]
    except Exception as e:
        console.print(f"[red]Error loading dataset: {str(e)}[/red]")
        return

    fact_checker = OpenAIFactChecker(base_url=args.base_url, model=args.model)
    metrics = evaluate_fact_checking(fact_checker, train_data, num_samples=args.samples)
    generate_report(metrics, console, args.output)


if __name__ == "__main__":
    main()
