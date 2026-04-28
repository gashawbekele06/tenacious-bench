"""
generation_scripts/trace_derived.py

Mode: Trace-Derived (~30% of dataset)
Takes Week 10 trace_log.jsonl, redacts sensitive fields, and restructures
each trace into a (input, candidate_output) task pair with a rubric.

Usage:
    python generation_scripts/trace_derived.py \
        --traces path/to/week10/trace_log.jsonl \
        --schema schema.json \
        --output tenacious_bench_v0.1/train/ \
        --seed 42
"""

import argparse
import json
import os
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone


REDACT_FIELDS = ["email", "phone", "personal_name", "linkedin_url"]


def redact(obj: dict) -> dict:
    """Recursively redact PII fields."""
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k in REDACT_FIELDS else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(i) for i in obj]
    return obj


def trace_to_task(trace: dict, task_number: int, seed: int) -> dict | None:
    """
    Convert a single Week 10 trace into a Tenacious-Bench task.
    Returns None if the trace lacks the required fields.
    """
    required = ["trace_id", "input", "output", "dimension"]
    if not all(k in trace for k in required):
        return None

    redacted_input = redact(trace["input"])

    return {
        "task_id": f"TB-TD-{task_number:04d}",
        "source_mode": "trace-derived",
        "difficulty": trace.get("difficulty", "medium"),
        "dimension": trace.get("dimension", "signal-grounding"),
        "input": {
            "hiring_signal_brief": redacted_input.get("hiring_signal_brief", ""),
            "bench_summary": redacted_input.get("bench_summary", ""),
            "prospect_profile": redacted_input.get("prospect_profile", {}),
            "prior_thread": redacted_input.get("prior_thread", ""),
        },
        "candidate_output": "",
        "ground_truth": trace.get("ground_truth", {
            "required_signal_references": [],
            "banned_phrases": [
                "hope this finds you well", "circle back", "touch base",
                "synergy", "leverage", "reach out", "loop you in"
            ],
            "required_elements": ["calendar_link", "company_name_mention"],
            "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"],
        }),
        "rubric": {
            "scoring_type": "hybrid",
            "threshold": 0.75,
            "dimensions": [
                {
                    "name": "banned_phrase_check",
                    "weight": 0.3,
                    "check_type": "not_contains",
                    "description": "No banned phrases from Tenacious style guide.",
                    "check_value": "hope this finds you well|circle back|touch base|synergy|leverage|reach out",
                },
                {
                    "name": "signal_reference_check",
                    "weight": 0.3,
                    "check_type": "contains",
                    "description": "Must reference at least one hiring signal.",
                    "check_value": "|".join(trace.get("ground_truth", {}).get("required_signal_references", ["hiring"])),
                },
                {
                    "name": "calendar_link_check",
                    "weight": 0.1,
                    "check_type": "regex",
                    "description": "Must contain a calendar booking link.",
                    "check_value": r"(calendly|cal\.com|savvycal|hubspot meetings)",
                },
                {
                    "name": "tone_judge",
                    "weight": 0.3,
                    "check_type": "llm_score",
                    "description": "LLM judge scores on 5 Tenacious tone markers.",
                    "check_value": "",
                },
            ],
        },
        "metadata": {
            "week10_trace_ids": [trace["trace_id"]],
            "week10_probe_ids": trace.get("probe_ids", []),
            "partition": "train",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seed": seed,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces", required=True, help="Path to trace_log.jsonl from Week 10")
    parser.add_argument("--schema", default="schema.json")
    parser.add_argument("--output", default="tenacious_bench_v0.1/train/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_tasks", type=int, default=100, help="Max trace-derived tasks to generate")
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    traces = []
    with open(args.traces) as f:
        for line in f:
            line = line.strip()
            if line:
                traces.append(json.loads(line))

    print(f"Loaded {len(traces)} traces from {args.traces}")
    random.shuffle(traces)
    traces = traces[: args.max_tasks]

    tasks_written = 0
    for i, trace in enumerate(traces, start=1):
        task = trace_to_task(trace, task_number=i, seed=args.seed)
        if task is None:
            print(f"  Skipping trace {i}: missing required fields")
            continue
        out_path = output_dir / f"{task['task_id']}.json"
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)
        tasks_written += 1

    print(f"Written {tasks_written} trace-derived tasks to {args.output}")


if __name__ == "__main__":
    main()
