#!/usr/bin/env python
import argparse
import json
from datetime import datetime
from typing import Any, Dict, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def load_evaluation_results(file_path: str) -> Dict[str, Any]:
    """
    Load evaluation results from a JSON file

    Args:
        file_path: Path to the evaluation results JSON file

    Returns:
        Dictionary containing the evaluation results
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(
            f"Failed to load evaluation results from {file_path}: {str(e)}"
        )


def generate_comparison(
    teapot_results: Dict[str, Any],
    openai_results: Dict[str, Any],
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate comparison metrics between TeapotAI and OpenAI evaluation results

    Args:
        teapot_results: TeapotAI evaluation results
        openai_results: OpenAI evaluation results
        output_file: Optional output file path to save comparison results

    Returns:
        Dictionary containing comparison metrics
    """
    comparison = {
        "comparison_date": datetime.now().isoformat(),
        "teapot_metrics": {
            "accuracy": teapot_results.get("accuracy", 0),
            "avg_confidence": teapot_results.get("avg_confidence", 0),
            "total_samples": teapot_results.get("total_samples", 0),
            "total_blogs": teapot_results.get("total_blogs", 0),
        },
        "openai_metrics": {
            "accuracy": openai_results.get("accuracy", 0),
            "avg_confidence": openai_results.get("avg_confidence", 0),
            "total_samples": openai_results.get("total_samples", 0),
            "total_blogs": openai_results.get("total_blogs", 0),
        },
        "differences": {
            "accuracy_diff": teapot_results.get("accuracy", 0)
            - openai_results.get("accuracy", 0),
            "confidence_diff": teapot_results.get("avg_confidence", 0)
            - openai_results.get("avg_confidence", 0),
        },
        "detailed_comparison": [],
    }

    # Match up individual results for detailed comparison
    teapot_blogs = {b["blog_text"][:50]: b for b in teapot_results.get("results", [])}
    openai_blogs = {b["blog_text"][:50]: b for b in openai_results.get("results", [])}

    common_blogs = set(teapot_blogs.keys()).intersection(set(openai_blogs.keys()))

    for blog_key in common_blogs:
        teapot_blog = teapot_blogs[blog_key]
        openai_blog = openai_blogs[blog_key]

        teapot_points = {
            p["key_point"][:50]: p for p in teapot_blog.get("key_points_results", [])
        }
        openai_points = {
            p["key_point"][:50]: p for p in openai_blog.get("key_points_results", [])
        }

        common_points = set(teapot_points.keys()).intersection(
            set(openai_points.keys())
        )

        point_comparisons = []
        for point_key in common_points:
            teapot_point = teapot_points[point_key]
            openai_point = openai_points[point_key]

            point_comparisons.append(
                {
                    "key_point": teapot_point["key_point"],
                    "teapot": {
                        "factual": teapot_point.get("factual", False),
                        "confidence": teapot_point.get("confidence", 0),
                        "correct": teapot_point.get("correct", False),
                    },
                    "openai": {
                        "factual": openai_point.get("factual", False),
                        "confidence": openai_point.get("confidence", 0),
                        "correct": openai_point.get("correct", False),
                    },
                    "agreement": teapot_point.get("factual", False)
                    == openai_point.get("factual", False),
                }
            )

        comparison["detailed_comparison"].append(
            {
                "blog_text": teapot_blog["blog_text"],
                "point_comparisons": point_comparisons,
            }
        )

    # Calculate agreement rate
    total_points = 0
    agreements = 0

    for blog in comparison["detailed_comparison"]:
        for point in blog["point_comparisons"]:
            total_points += 1
            if point["agreement"]:
                agreements += 1

    comparison["agreement_rate"] = agreements / total_points if total_points > 0 else 0

    if output_file:
        with open(output_file, "w") as f:
            json.dump(comparison, f, indent=2)

    return comparison


def display_comparison_report(comparison: Dict[str, Any], console: Console) -> None:
    """
    Display a rich formatted report of the comparison results

    Args:
        comparison: Comparison results
        console: Rich console for output
    """
    console.print(
        "\n[bold blue]TeapotFacts vs OpenAI Model Comparison Report[/bold blue]"
    )
    console.print(f"\nDate: {comparison['comparison_date']}")

    # Main metrics table
    metrics_table = Table(title="Performance Comparison", box=box.ROUNDED)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("TeapotFacts", style="green")
    metrics_table.add_column("OpenAI", style="yellow")
    metrics_table.add_column("Difference", style="magenta")

    teapot_acc = comparison["teapot_metrics"]["accuracy"]
    openai_acc = comparison["openai_metrics"]["accuracy"]
    acc_diff = comparison["differences"]["accuracy_diff"]

    teapot_conf = comparison["teapot_metrics"]["avg_confidence"]
    openai_conf = comparison["openai_metrics"]["avg_confidence"]
    conf_diff = comparison["differences"]["confidence_diff"]

    metrics_table.add_row(
        "Accuracy", f"{teapot_acc:.2%}", f"{openai_acc:.2%}", f"{acc_diff:.2%}"
    )
    metrics_table.add_row(
        "Avg Confidence", f"{teapot_conf:.2f}", f"{openai_conf:.2f}", f"{conf_diff:.2f}"
    )
    metrics_table.add_row(
        "Model Agreement Rate", f"{comparison['agreement_rate']:.2%}", "", ""
    )

    console.print(metrics_table)

    # Sample comparison
    if comparison["detailed_comparison"]:
        sample_blog = comparison["detailed_comparison"][0]

        if sample_blog["point_comparisons"]:
            sample_point = sample_blog["point_comparisons"][0]

            console.print("\n[bold]Sample Comparison:[/bold]")
            console.print(
                Panel(
                    sample_blog["blog_text"][:200] + "...",
                    title="Blog Text",
                    expand=False,
                )
            )

            console.print(
                Panel(
                    sample_point["key_point"][:200] + "...",
                    title="Key Point",
                    expand=False,
                )
            )

            comparison_table = Table(title="Model Responses")
            comparison_table.add_column("Model", style="cyan")
            comparison_table.add_column("Factual", style="green")
            comparison_table.add_column("Confidence", style="blue")

            comparison_table.add_row(
                "TeapotFacts",
                "✓" if sample_point["teapot"]["factual"] else "✗",
                f"{sample_point['teapot']['confidence']:.2f}",
            )

            comparison_table.add_row(
                "OpenAI",
                "✓" if sample_point["openai"]["factual"] else "✗",
                f"{sample_point['openai']['confidence']:.2f}",
            )

            console.print(comparison_table)

    # Agreement summary
    agreement_table = Table(title="Agreement Analysis")
    agreement_table.add_column("Metric", style="cyan")
    agreement_table.add_column("Value", style="magenta")

    agreement_table.add_row(
        "Total Points Compared", str(len(comparison["detailed_comparison"]))
    )
    agreement_table.add_row("Agreement Rate", f"{comparison['agreement_rate']:.2%}")

    console.print(agreement_table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare TeapotFacts and OpenAI model evaluation results"
    )
    parser.add_argument(
        "--teapot",
        type=str,
        default="evaluation_results.json",
        help="Path to TeapotFacts evaluation results (default: evaluation_results.json)",
    )
    parser.add_argument(
        "--openai",
        type=str,
        default="openai_evaluation_results.json",
        help="Path to OpenAI evaluation results (default: openai_evaluation_results.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="comparison_results.json",
        help="Output path for comparison results (default: comparison_results.json)",
    )
    args = parser.parse_args()

    console = Console()
    console.print(
        "[bold]Loading evaluation results and generating comparison...[/bold]"
    )

    try:
        teapot_results = load_evaluation_results(args.teapot)
        openai_results = load_evaluation_results(args.openai)

        comparison = generate_comparison(
            teapot_results=teapot_results,
            openai_results=openai_results,
            output_file=args.output,
        )

        display_comparison_report(comparison, console)
        console.print(f"\n[green]Detailed comparison saved to {args.output}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating comparison: {str(e)}[/red]")


if __name__ == "__main__":
    main()
