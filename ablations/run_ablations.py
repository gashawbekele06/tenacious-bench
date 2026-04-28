"""
ablations/run_ablations.py

Runs three ablations and writes results to ablation_results.json.

Delta A: Trained model vs Week 10 baseline on Tenacious-Bench held-out
Delta B: Trained model vs prompt-engineered version (no training) on same backbone
Delta C: Trained model vs Week 10 τ²-Bench score (informational only, reuse existing)

Statistical testing: paired bootstrap resampling, 95% CI, p < 0.05.

Usage:
    python ablations/run_ablations.py \
        --held_out tenacious_bench_v0.1/held_out/ \
        --baseline_outputs ablations/baseline_outputs.jsonl \
        --trained_outputs ablations/trained_outputs.jsonl \
        --prompted_outputs ablations/prompted_outputs.jsonl \
        --tau2_score 0.61 \
        --seed 42
"""

import argparse
import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timezone


def load_outputs(path: str) -> dict:
    """Load {task_id: output} from JSONL."""
    outputs = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                outputs[rec["task_id"]] = rec["output"]
    return outputs


def load_tasks(held_out_dir: str) -> list[dict]:
    tasks = []
    for p in sorted(Path(held_out_dir).glob("*.json")):
        with open(p) as f:
            tasks.append(json.load(f))
    return tasks


def score_output(task: dict, output: str) -> float:
    """Run programmatic scoring (without LLM judge for speed in ablations)."""
    import re
    rubric = task["rubric"]
    total_weight = 0.0
    weighted_score = 0.0

    for dim in rubric["dimensions"]:
        if dim["check_type"] == "llm_score":
            continue  # Skip LLM checks in ablation for cost reasons; add separately if needed
        weight = dim["weight"]
        total_weight += weight
        check_value = dim.get("check_value", "")
        text = output.lower()

        if dim["check_type"] == "not_contains":
            patterns = [p.strip() for p in check_value.split("|") if p.strip()]
            passed = not any(p in text for p in patterns)
        elif dim["check_type"] == "contains":
            patterns = [p.strip() for p in check_value.split("|") if p.strip()]
            passed = any(p in text for p in patterns)
        elif dim["check_type"] == "regex":
            passed = bool(re.search(check_value, output, re.IGNORECASE))
        else:
            passed = False

        weighted_score += weight * (1.0 if passed else 0.0)

    return weighted_score / total_weight if total_weight > 0 else 0.0


def paired_bootstrap_test(scores_a: list[float], scores_b: list[float], n_bootstrap: int = 10000, seed: int = 42) -> dict:
    """
    Paired bootstrap test for mean(A) > mean(B).
    Returns mean_a, mean_b, delta, p_value, ci_lower, ci_upper.
    """
    rng = np.random.default_rng(seed)
    scores_a = np.array(scores_a)
    scores_b = np.array(scores_b)
    n = len(scores_a)
    observed_delta = scores_a.mean() - scores_b.mean()

    deltas = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, n, size=n)
        boot_a = scores_a[indices].mean()
        boot_b = scores_b[indices].mean()
        deltas.append(boot_a - boot_b)

    deltas = np.array(deltas)
    p_value = float((deltas <= 0).mean())
    ci_lower = float(np.percentile(deltas, 2.5))
    ci_upper = float(np.percentile(deltas, 97.5))

    return {
        "mean_a": float(scores_a.mean()),
        "mean_b": float(scores_b.mean()),
        "delta": float(observed_delta),
        "p_value": p_value,
        "significant": p_value < 0.05,
        "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
        "n": n,
        "n_bootstrap": n_bootstrap,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--held_out", default="tenacious_bench_v0.1/held_out/")
    parser.add_argument("--baseline_outputs", required=True)
    parser.add_argument("--trained_outputs", required=True)
    parser.add_argument("--prompted_outputs", required=True, help="Prompt-engineered (no training) outputs")
    parser.add_argument("--tau2_score", type=float, default=None, help="Reuse existing Week 10 τ²-Bench score")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("Loading held-out tasks and agent outputs...")
    tasks = load_tasks(args.held_out)
    baseline_outputs = load_outputs(args.baseline_outputs)
    trained_outputs = load_outputs(args.trained_outputs)
    prompted_outputs = load_outputs(args.prompted_outputs)

    print(f"Tasks: {len(tasks)}")

    baseline_scores, trained_scores, prompted_scores, traces = [], [], [], []

    for task in tasks:
        tid = task["task_id"]
        b_out = baseline_outputs.get(tid, "")
        t_out = trained_outputs.get(tid, "")
        p_out = prompted_outputs.get(tid, "")

        b_score = score_output(task, b_out)
        t_score = score_output(task, t_out)
        p_score = score_output(task, p_out)

        baseline_scores.append(b_score)
        trained_scores.append(t_score)
        prompted_scores.append(p_score)
        traces.append({
            "task_id": tid,
            "baseline_score": round(b_score, 4),
            "trained_score": round(t_score, 4),
            "prompted_score": round(p_score, 4),
        })

    print("\nComputing Delta A (trained vs baseline)...")
    delta_a = paired_bootstrap_test(trained_scores, baseline_scores, seed=args.seed)

    print("Computing Delta B (trained vs prompted)...")
    delta_b = paired_bootstrap_test(trained_scores, prompted_scores, seed=args.seed)

    results = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "n_held_out_tasks": len(tasks),
        "delta_a": {
            "description": "Trained model vs Week 10 baseline on Tenacious-Bench held-out",
            **delta_a,
        },
        "delta_b": {
            "description": "Trained model vs prompt-engineered (no training) on same backbone",
            **delta_b,
        },
        "delta_c": {
            "description": "Trained model vs Week 10 τ²-Bench score (informational only)",
            "week10_tau2_score": args.tau2_score,
            "trained_mean": delta_a["mean_a"],
            "note": "Reused Week 10 score — no re-running of τ²-Bench this week.",
        },
    }

    with open("ablations/ablation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    with open("ablations/held_out_traces.jsonl", "w") as f:
        for trace in traces:
            f.write(json.dumps(trace) + "\n")

    print(f"\n=== Ablation Results ===")
    print(f"Delta A (trained vs baseline): {delta_a['delta']:+.4f} | p={delta_a['p_value']:.4f} | {'✓ significant' if delta_a['significant'] else '✗ not significant'}")
    print(f"Delta B (trained vs prompted): {delta_b['delta']:+.4f} | p={delta_b['p_value']:.4f} | {'✓ beats prompting' if delta_b['significant'] else '✗ prompting was sufficient'}")
    print(f"\nResults written to ablations/ablation_results.json")
    print(f"Traces written to ablations/held_out_traces.jsonl")


if __name__ == "__main__":
    main()
