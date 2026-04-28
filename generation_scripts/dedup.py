"""
generation_scripts/dedup.py

Deduplicates tasks across all generation modes before partitioning.
Uses both n-gram overlap and embedding similarity.
Keeps the task with higher judge_scores when two are near-duplicates.

Usage:
    python generation_scripts/dedup.py \
        --input_dirs tenacious_bench_v0.1/train/ tenacious_bench_v0.1/dev/ \
        --output tenacious_bench_v0.1/deduped/ \
        --ngram_n 6 \
        --sim_threshold 0.90 \
        --seed 42
"""

import argparse
import json
from pathlib import Path


def load_all_tasks(dirs: list[str]) -> list[dict]:
    tasks = []
    for d in dirs:
        for p in sorted(Path(d).glob("*.json")):
            with open(p) as f:
                tasks.append(json.load(f))
    return tasks


def get_ngrams(text: str, n: int) -> set[tuple]:
    tokens = text.lower().split()
    if len(tokens) < n:
        return set()
    return set(zip(*[tokens[i:] for i in range(n)]))


def avg_judge_score(task: dict) -> float:
    scores = task.get("metadata", {}).get("judge_scores", {})
    vals = [v for k, v in scores.items() if k not in ("error", "reasoning", "judge_type") and isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else 3.0


def deduplicate(tasks: list[dict], ngram_n: int, sim_threshold: float) -> list[dict]:
    """
    Greedy dedup: for each task, check against already-kept tasks.
    If near-duplicate found, keep the one with higher judge score.
    """
    from sentence_transformers import SentenceTransformer
    import numpy as np

    print(f"  Loading sentence-transformers for embedding dedup...")
    emb_model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [json.dumps(t.get("input", {})) for t in tasks]
    embeddings = emb_model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    kept_indices = []
    removed = []

    for i, task in enumerate(tasks):
        i_text = json.dumps(task.get("input", {}))
        i_ngrams = get_ngrams(i_text, ngram_n)
        i_emb = embeddings[i]
        is_dup = False

        for j in kept_indices:
            j_text = json.dumps(tasks[j].get("input", {}))
            j_ngrams = get_ngrams(j_text, ngram_n)
            ngram_overlap = bool(i_ngrams & j_ngrams)
            cos_sim = float(embeddings[j] @ i_emb)

            if ngram_overlap or cos_sim >= sim_threshold:
                # Keep the one with higher judge score
                if avg_judge_score(task) > avg_judge_score(tasks[j]):
                    kept_indices.remove(j)
                    kept_indices.append(i)
                is_dup = True
                removed.append(task["task_id"])
                break

        if not is_dup:
            kept_indices.append(i)

    print(f"  Kept {len(kept_indices)} / {len(tasks)} tasks after dedup (removed {len(removed)})")
    return [tasks[i] for i in kept_indices], removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dirs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ngram_n", type=int, default=6)
    parser.add_argument("--sim_threshold", type=float, default=0.90)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading tasks from: {args.input_dirs}")
    tasks = load_all_tasks(args.input_dirs)
    print(f"Total tasks loaded: {len(tasks)}")

    kept_tasks, removed_ids = deduplicate(tasks, args.ngram_n, args.sim_threshold)

    for task in kept_tasks:
        out_path = output_dir / f"{task['task_id']}.json"
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)

    log = {"kept": len(kept_tasks), "removed": len(removed_ids), "removed_ids": removed_ids}
    with open(output_dir / "dedup_log.json", "w") as f:
        json.dump(log, f, indent=2)

    print(f"Deduped tasks written to {args.output}")


if __name__ == "__main__":
    main()
