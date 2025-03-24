import argparse
from datetime import datetime
import json
from typing import Dict, Sequence, Optional, Any, cast

from datasets import (
    load_dataset,
    Dataset,
    DatasetDict,
    IterableDataset,
    IterableDatasetDict,
)
from rich.console import Console
from rich.table import Table
from rich.progress import track

from app.fact_checker import TeapotFactChecker


def evaluate_fact_checking(
    fact_checker: TeapotFactChecker,
    blogs: Sequence[Dict[str, Any]],
    num_samples: int = 10,
) -> Dict:
    """
    Evaluate the fact checker on blog posts and their key points

    Args:
        fact_checker: The TeapotFactChecker instance
        blogs: Sequence of blog posts with key points
        num_samples: Number of samples to evaluate (default: 10)

    Returns:
        Dictionary with evaluation metrics and detailed results
    """
    total_correct = 0
    total_confidence = 0
    results = []

    # Take a subset of samples for evaluation
    evaluation_samples = list(blogs)[:num_samples]

    # Track progress with rich
    for blog in track(evaluation_samples, description="Evaluating samples"):
        text = blog["input"]
        key_points = blog["output"].strip().split("\n")

        blog_results = []
        for point in key_points:
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

    # Print summary metrics
    console.print("\n[bold blue]TeapotFacts Model Evaluation Report[/bold blue]")
    console.print(f"\nDate: {metrics['evaluation_date']}")
    console.print(f"Total blogs evaluated: {metrics['total_blogs']}")
    console.print(f"Total key points evaluated: {metrics['total_samples']}")

    # Create metrics table
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="magenta")

    metrics_table.add_row("Accuracy", f"{metrics['accuracy']:.2%}")
    metrics_table.add_row("Average Confidence", f"{metrics['avg_confidence']:.2f}")

    console.print(metrics_table)

    # Sample results table
    results_table = Table(title="Sample Results")
    results_table.add_column("Key Point", style="cyan")
    results_table.add_column("Factual", style="green")
    results_table.add_column("Confidence", style="blue")
    results_table.add_column("Correct", style="magenta")

    # Show first 5 key points as samples
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

    # Save detailed results to JSON if requested
    if output_json:
        with open(output_json, "w") as f:
            json.dump(metrics, f, indent=2)
        console.print(f"\n[green]Detailed results saved to {output_json}[/green]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate TeapotFacts model on blog key points dataset"
    )
    parser.add_argument(
        "--samples", type=int, default=10, help="Number of blog samples to evaluate"
    )
    parser.add_argument(
        "--output", type=str, help="Output JSON file for detailed results"
    )
    args = parser.parse_args()

    # Initialize rich console
    console = Console()

    # Load dataset and initialize fact checker
    console.print("[bold]Loading dataset and initializing model...[/bold]")
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

    fact_checker = TeapotFactChecker()

    # Run evaluation
    metrics = evaluate_fact_checking(fact_checker, train_data, num_samples=args.samples)

    # Generate report
    generate_report(metrics, console, args.output)


if __name__ == "__main__":
    main()
