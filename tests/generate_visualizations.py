"""Generate visualizations from benchmark results.

This script creates visualizations to help illustrate repominify's impact on code generation.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def safe_get_metric(data: dict, path: list, default: any = 0) -> any:
    """Safely get a metric value from nested dictionary.
    
    Args:
        data: Dictionary to traverse
        path: List of keys to follow
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    try:
        value = data
        for key in path:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def load_results(results_dir: str = "benchmark_results") -> tuple:
    """Load benchmark results from JSON files."""
    results_dir = Path(results_dir)
    
    with open(results_dir / "baseline_results.json") as f:
        baseline = json.load(f)
    
    with open(results_dir / "enhanced_results.json") as f:
        enhanced = json.load(f)
    
    with open(results_dir / "aggregate_metrics.json") as f:
        aggregate = json.load(f)
    
    return baseline, enhanced, aggregate

def create_code_size_comparison(baseline, enhanced, output_dir: str):
    """Create code size comparison visualization."""
    tasks = list(baseline.keys())
    baseline_sizes = [
        safe_get_metric(baseline[task], ["metrics", "complexity", "lines"])
        for task in tasks
    ]
    enhanced_sizes = [
        safe_get_metric(enhanced[task], ["metrics", "complexity", "lines"])
        for task in tasks
    ]
    
    # Filter out tasks with no size data
    valid_tasks = []
    valid_baseline = []
    valid_enhanced = []
    for i, task in enumerate(tasks):
        if baseline_sizes[i] > 0 or enhanced_sizes[i] > 0:
            valid_tasks.append(task)
            valid_baseline.append(baseline_sizes[i])
            valid_enhanced.append(enhanced_sizes[i])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(valid_tasks))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], valid_baseline, width, label='Without Repominify')
    ax.bar([i + width/2 for i in x], valid_enhanced, width, label='With Repominify')
    
    ax.set_ylabel('Lines of Code')
    ax.set_title('Code Size Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(valid_tasks, rotation=45)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/code_size_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_integration_score_radar(baseline, enhanced, output_dir: str):
    """Create integration score radar chart."""
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    
    metrics = ['Project Imports', 'Pattern Adoption', 'Component Reuse']
    angles = [n / float(len(metrics)) * 2 * 3.14159 for n in range(len(metrics))]
    angles += angles[:1]
    
    # Get average scores
    baseline_scores = [0, 0, 0]  # Project imports, patterns, reuse
    enhanced_scores = [0, 0, 0]
    task_count = 0
    
    for task in baseline:
        b_metrics = safe_get_metric(baseline[task], ["metrics", "integration"], {})
        if b_metrics:
            task_count += 1
            baseline_scores[0] += int(b_metrics.get("uses_project_imports", False))
            baseline_scores[1] += b_metrics.get("follows_patterns", 0)
            baseline_scores[2] += int(b_metrics.get("reuses_components", False))
    
    for task in enhanced:
        e_metrics = safe_get_metric(enhanced[task], ["metrics", "integration"], {})
        if e_metrics:
            enhanced_scores[0] += int(e_metrics.get("uses_project_imports", False))
            enhanced_scores[1] += e_metrics.get("follows_patterns", 0)
            enhanced_scores[2] += int(e_metrics.get("reuses_components", False))
    
    if task_count > 0:
        baseline_scores = [s/task_count for s in baseline_scores]
        enhanced_scores = [s/task_count for s in enhanced_scores]
    
    baseline_scores += baseline_scores[:1]
    enhanced_scores += enhanced_scores[:1]
    
    ax.plot(angles, baseline_scores, 'o-', linewidth=2, label='Without Repominify')
    ax.fill(angles, baseline_scores, alpha=0.25)
    ax.plot(angles, enhanced_scores, 'o-', linewidth=2, label='With Repominify')
    ax.fill(angles, enhanced_scores, alpha=0.25)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_title('Integration Score Components')
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/integration_radar.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_timing_breakdown(baseline, enhanced, output_dir: str):
    """Create timing breakdown visualization."""
    tasks = list(baseline.keys())
    baseline_gen = [safe_get_metric(baseline[task], ["timing", "generation"]) for task in tasks]
    baseline_analysis = [safe_get_metric(baseline[task], ["timing", "analysis"]) for task in tasks]
    enhanced_gen = [safe_get_metric(enhanced[task], ["timing", "generation"]) for task in tasks]
    enhanced_analysis = [safe_get_metric(enhanced[task], ["timing", "analysis"]) for task in tasks]
    
    # Filter out tasks with no timing data
    valid_tasks = []
    valid_baseline_gen = []
    valid_baseline_analysis = []
    valid_enhanced_gen = []
    valid_enhanced_analysis = []
    
    for i, task in enumerate(tasks):
        if any([baseline_gen[i], baseline_analysis[i], enhanced_gen[i], enhanced_analysis[i]]):
            valid_tasks.append(task)
            valid_baseline_gen.append(baseline_gen[i])
            valid_baseline_analysis.append(baseline_analysis[i])
            valid_enhanced_gen.append(enhanced_gen[i])
            valid_enhanced_analysis.append(enhanced_analysis[i])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Baseline timing
    ax1.bar(valid_tasks, valid_baseline_gen, label='Generation')
    ax1.bar(valid_tasks, valid_baseline_analysis, bottom=valid_baseline_gen, label='Analysis')
    ax1.set_title('Without Repominify')
    ax1.set_ylabel('Time (seconds)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.legend()
    
    # Enhanced timing
    ax2.bar(valid_tasks, valid_enhanced_gen, label='Generation')
    ax2.bar(valid_tasks, valid_enhanced_analysis, bottom=valid_enhanced_gen, label='Analysis')
    ax2.set_title('With Repominify')
    ax2.set_ylabel('Time (seconds)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/timing_breakdown.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_improvement_summary(aggregate, output_dir: str):
    """Create improvement summary visualization."""
    improvements = [
        safe_get_metric(aggregate, ["improvements", "code_reduction"]),
        safe_get_metric(aggregate, ["improvements", "integration_improvement"])
    ]
    labels = ['Code Size\nReduction', 'Integration\nImprovement']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(labels, improvements)
    ax.set_ylabel('Improvement (%)')
    ax.set_title('Overall Improvements with Repominify')
    
    # Add value labels on bars
    for i, v in enumerate(improvements):
        ax.text(i, v, f'{v:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/improvement_summary.png", dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all visualizations."""
    # Create visualizations directory
    output_dir = "benchmark_results/visualizations"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load results
    baseline, enhanced, aggregate = load_results()
    
    # Generate visualizations
    create_code_size_comparison(baseline, enhanced, output_dir)
    create_integration_score_radar(baseline, enhanced, output_dir)
    create_timing_breakdown(baseline, enhanced, output_dir)
    create_improvement_summary(aggregate, output_dir)
    
    print(f"Visualizations saved to {output_dir}/")

if __name__ == "__main__":
    main() 