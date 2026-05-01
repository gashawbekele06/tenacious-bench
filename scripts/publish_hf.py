"""
scripts/publish_hf.py

Publishes the Tenacious-Bench dataset to HuggingFace Hub.
Run only after passing the publication checklist in README.md.

Usage:
    python scripts/publish_hf.py --repo_id your-handle/tenacious-bench-v0.1 --dry_run
    python scripts/publish_hf.py --repo_id your-handle/tenacious-bench-v0.1
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


def normalize(task: dict) -> dict:
    """Flatten nested fields to JSON strings for a consistent schema across partitions."""
    return {
        "task_id": task.get("task_id", ""),
        "source_mode": task.get("source_mode", ""),
        "difficulty": task.get("difficulty", ""),
        "dimension": task.get("dimension", ""),
        "input": json.dumps(task.get("input", {})),
        "candidate_output": task.get("candidate_output", ""),
        "ground_truth": json.dumps(task.get("ground_truth", {})),
        "rubric": json.dumps(task.get("rubric", {})),
        "metadata": json.dumps(task.get("metadata", {})),
    }


def load_partition(directory: str) -> list[dict]:
    tasks = []
    for p in sorted(Path(directory).glob("*.json")):
        with open(p, encoding="utf-8") as f:
            tasks.append(normalize(json.load(f)))
    return tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_id", required=True, help="HuggingFace repo ID, e.g. your-handle/tenacious-bench-v0.1")
    parser.add_argument("--dry_run", action="store_true", help="Print what would be uploaded without actually uploading")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token and not args.dry_run:
        raise ValueError("HF_TOKEN not set in .env")

    from datasets import Dataset, DatasetDict
    from huggingface_hub import HfApi

    print(f"Loading dataset partitions...")
    train = load_partition("tenacious_bench_v0.1/train/")
    dev = load_partition("tenacious_bench_v0.1/dev/")
    # Held-out is not published — only released after leaderboard
    print(f"  Train: {len(train)}, Dev: {len(dev)}")

    ds = DatasetDict({
        "train": Dataset.from_list(train),
        "dev": Dataset.from_list(dev),
    })

    if args.dry_run:
        print(f"\nDRY RUN — would push to: https://huggingface.co/datasets/{args.repo_id}")
        print(f"Dataset: {ds}")
        return

    print(f"\nPushing to HuggingFace Hub: {args.repo_id}")
    ds.push_to_hub(args.repo_id, token=hf_token)

    # Upload datasheet and README
    api = HfApi()
    api.upload_file(
        path_or_fileobj="datasheet.md",
        path_in_repo="datasheet.md",
        repo_id=args.repo_id,
        repo_type="dataset",
        token=hf_token,
    )
    print(f"\nDataset published: https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
