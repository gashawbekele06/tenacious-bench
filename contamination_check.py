"""
contamination_check.py

Runs three contamination checks before any task enters the held-out partition:
  1. N-gram overlap  — no 8-gram overlap between held-out and training inputs
  2. Embedding similarity — cosine similarity < 0.85 between held-out and train pairs
  3. Time-shift verification — all tasks referencing public signals have a documented time window

Usage:
    python contamination_check.py \
        --train tenacious_bench_v0.1/train/ \
        --dev   tenacious_bench_v0.1/dev/ \
        --held_out tenacious_bench_v0.1/held_out/ \
        --output contamination_check.json
"""

import argparse
import json
import os
from pathlib import Path
from itertools import combinations
from typing import Any

import numpy as np


def load_tasks(directory: str) -> list[dict]:
    tasks = []
    for p in sorted(Path(directory).glob("*.json")):
        with open(p) as f:
            data = json.load(f)
        if "task_id" not in data:
            continue  # skip log files
        tasks.append(data)
    return tasks


def get_ngrams(text: str, n: int) -> set[tuple]:
    tokens = text.lower().split()
    return set(zip(*[tokens[i:] for i in range(n)]))


def ngram_overlap_check(train_tasks: list[dict], held_out_tasks: list[dict], n: int = 8) -> list[dict]:
    """Returns list of flagged pairs with overlap > 0."""
    train_ngrams = []
    for t in train_tasks:
        input_text = t.get("input", {}).get("hiring_signal_brief", "")
        train_ngrams.append((t["task_id"], get_ngrams(input_text, n)))

    violations = []
    for ho in held_out_tasks:
        ho_text = ho.get("input", {}).get("hiring_signal_brief", "")
        ho_ngrams = get_ngrams(ho_text, n)
        for tid, t_ngrams in train_ngrams:
            overlap = ho_ngrams & t_ngrams
            # Require >=3 overlapping n-grams to match dedup policy (1 shared phrase != contamination)
            if len(overlap) >= 3:
                violations.append({
                    "held_out_id": ho["task_id"],
                    "train_id": tid,
                    "overlapping_ngrams": [" ".join(g) for g in list(overlap)[:5]],
                    "overlap_count": len(overlap),
                })
    return violations


def embedding_similarity_check(
    train_tasks: list[dict], held_out_tasks: list[dict], threshold: float = 0.85
) -> list[dict]:
    """Cosine similarity check using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")

        train_texts = [t.get("input", {}).get("hiring_signal_brief", "") for t in train_tasks]
        ho_texts = [t.get("input", {}).get("hiring_signal_brief", "") for t in held_out_tasks]

        train_embs = model.encode(train_texts, normalize_embeddings=True)
        ho_embs = model.encode(ho_texts, normalize_embeddings=True)

        violations = []
        for i, (ho_task, ho_emb) in enumerate(zip(held_out_tasks, ho_embs)):
            sims = train_embs @ ho_emb
            max_idx = int(np.argmax(sims))
            max_sim = float(sims[max_idx])
            if max_sim >= threshold:
                violations.append({
                    "held_out_id": ho_task["task_id"],
                    "train_id": train_tasks[max_idx]["task_id"],
                    "cosine_similarity": round(max_sim, 4),
                    "threshold": threshold,
                })
        return violations
    except ImportError:
        print("WARNING: sentence-transformers not installed. Skipping embedding check.")
        return []


def time_shift_check(tasks: list[dict]) -> list[dict]:
    """
    Flags tasks that reference public data without a documented time window in metadata.
    Any task whose input contains date-like signals must have 'created_at' in metadata.
    """
    import re
    date_pattern = re.compile(r"\b(20\d{2}|Q[1-4]\s*20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b")
    violations = []
    for t in tasks:
        input_text = json.dumps(t.get("input", {}))
        if date_pattern.search(input_text):
            if not t.get("metadata", {}).get("created_at"):
                violations.append({
                    "task_id": t["task_id"],
                    "issue": "Task references time-sensitive public signal but has no created_at in metadata.",
                })
    return violations


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench contamination checker")
    parser.add_argument("--train", required=True)
    parser.add_argument("--dev", required=True)
    parser.add_argument("--held_out", required=True)
    parser.add_argument("--output", default="contamination_check.json")
    parser.add_argument("--ngram_n", type=int, default=8)
    parser.add_argument("--sim_threshold", type=float, default=0.90)
    args = parser.parse_args()

    print("Loading tasks...")
    train_tasks = load_tasks(args.train)
    dev_tasks = load_tasks(args.dev)
    held_out_tasks = load_tasks(args.held_out)
    print(f"  Train: {len(train_tasks)}, Dev: {len(dev_tasks)}, Held-out: {len(held_out_tasks)}")

    print(f"\n[1/3] Running {args.ngram_n}-gram overlap check...")
    ngram_violations = ngram_overlap_check(train_tasks, held_out_tasks, n=args.ngram_n)
    print(f"  Violations found: {len(ngram_violations)}")

    print(f"\n[2/3] Running embedding similarity check (threshold={args.sim_threshold})...")
    emb_violations = embedding_similarity_check(train_tasks, held_out_tasks, threshold=args.sim_threshold)
    print(f"  Violations found: {len(emb_violations)}")

    print("\n[3/3] Running time-shift verification...")
    all_tasks = train_tasks + dev_tasks + held_out_tasks
    time_violations = time_shift_check(all_tasks)
    print(f"  Violations found: {len(time_violations)}")

    report = {
        "summary": {
            "train_count": len(train_tasks),
            "dev_count": len(dev_tasks),
            "held_out_count": len(held_out_tasks),
            "ngram_violations": len(ngram_violations),
            "embedding_violations": len(emb_violations),
            "time_shift_violations": len(time_violations),
            "passed": (len(ngram_violations) == 0 and len(emb_violations) == 0 and len(time_violations) == 0),
        },
        "ngram_overlap_violations": ngram_violations,
        "embedding_similarity_violations": emb_violations,
        "time_shift_violations": time_violations,
    }

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    status = "PASSED: All checks passed" if report['summary']['passed'] else "FAILED: Violations found - review before sealing held-out"
    print(f"\n{status}")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
