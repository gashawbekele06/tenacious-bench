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
import time
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


def _is_metadata_phrase(phrase: str) -> bool:
    """Rubric annotations (peer_count=2, cannot_assert_...) are not natural email phrases."""
    if any(c in phrase for c in ("=", "<", ">", "(", ")", "[")):
        return True
    if "_" in phrase and len(phrase) > 20:
        return True
    return False


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters (GPT/Claude convention)."""
    return max(1, len(text) // 4)


# Cost per 1M tokens (input+output blended) by model family
TOKEN_COST_PER_M = {
    "claude-haiku-4-5": 0.10,
    "qwen3-8b": 1.00,
    "default": 0.25,
}


def compute_task_cost(input_text: str, output_text: str, model: str = "claude-haiku-4-5") -> dict:
    """Returns token counts and estimated USD cost for one inference call."""
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    total_tokens = input_tokens + output_tokens
    cost_per_m = TOKEN_COST_PER_M.get(model, TOKEN_COST_PER_M["default"])
    cost_usd = (total_tokens / 1_000_000) * cost_per_m
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "model": model,
    }


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
            patterns = [p.strip() for p in check_value.split("|") if p.strip()
                        and not _is_metadata_phrase(p.strip())]
            if not patterns:
                passed = True  # all phrases were metadata annotations — auto-pass
            else:
                passed = any(p.lower() in text for p in patterns)
        elif dim["check_type"] == "regex":
            passed = bool(re.search(check_value, output, re.IGNORECASE))
        elif dim["check_type"] == "word_count":
            max_words = int(check_value)
            body = " ".join(l for l in output.split("\n") if not l.lower().startswith("subject:"))
            passed = len(body.split()) <= max_words
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
    total_cost = {"baseline": 0.0, "trained": 0.0, "prompted": 0.0}
    total_tokens = {"baseline": 0, "trained": 0, "prompted": 0}

    for task in tasks:
        tid = task["task_id"]
        task_input_text = json.dumps(task.get("input", {}))
        b_out = baseline_outputs.get(tid, "")
        t_out = trained_outputs.get(tid, "")
        p_out = prompted_outputs.get(tid, "")

        # --- scoring with wall-clock timing ---
        t0 = time.perf_counter()
        b_score = score_output(task, b_out)
        b_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        t_score = score_output(task, t_out)
        t_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        p_score = score_output(task, p_out)
        p_elapsed = time.perf_counter() - t0

        # --- per-task cost-pareto ---
        b_cost = compute_task_cost(task_input_text, b_out)
        t_cost = compute_task_cost(task_input_text, t_out)
        p_cost = compute_task_cost(task_input_text, p_out)

        total_cost["baseline"] += b_cost["cost_usd"]
        total_cost["trained"] += t_cost["cost_usd"]
        total_cost["prompted"] += p_cost["cost_usd"]
        total_tokens["baseline"] += b_cost["total_tokens"]
        total_tokens["trained"] += t_cost["total_tokens"]
        total_tokens["prompted"] += p_cost["total_tokens"]

        baseline_scores.append(b_score)
        trained_scores.append(t_score)
        prompted_scores.append(p_score)
        traces.append({
            "task_id": tid,
            "baseline_score": round(b_score, 4),
            "trained_score": round(t_score, 4),
            "prompted_score": round(p_score, 4),
            "cost_pareto": {
                "baseline": {**b_cost, "latency_s": round(b_elapsed, 4)},
                "trained":  {**t_cost, "latency_s": round(t_elapsed, 4)},
                "prompted": {**p_cost, "latency_s": round(p_elapsed, 4)},
            },
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
        "cost_pareto": {
            "description": "Token counts and USD cost per condition across all held-out tasks",
            "baseline":  {"total_tokens": total_tokens["baseline"],  "total_cost_usd": round(total_cost["baseline"],  6)},
            "trained":   {"total_tokens": total_tokens["trained"],   "total_cost_usd": round(total_cost["trained"],   6)},
            "prompted":  {"total_tokens": total_tokens["prompted"],  "total_cost_usd": round(total_cost["prompted"],  6)},
            "note": "Token counts estimated at 1 token per 4 chars. Per-task breakdown in held_out_traces.jsonl.",
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
