"""
generation_scripts/programmatic.py

Mode: Programmatic with parameter sweeps (~30% of dataset)
Generates tasks by combinatorially expanding template slots.
A single probe becomes many tasks by varying company_size, segment,
ai_maturity_score, requested_headcount, signal_confidence, etc.

Usage:
    python generation_scripts/programmatic.py \
        --probes probe_library.md \
        --output tenacious_bench_v0.1/train/ \
        --seed 42
"""

import argparse
import json
import random
from datetime import datetime, timezone
from itertools import product
from pathlib import Path


COMPANY_SIZES = ["11-50", "51-200", "201-500", "501-2000"]
SEGMENTS = ["Series A SaaS", "Series B SaaS", "Growth-stage FinTech", "Enterprise Healthcare", "SMB eCommerce"]
AI_MATURITY_SCORES = [1.5, 2.5, 3.0, 3.5, 4.5]
SIGNAL_CONFIDENCES = [0.55, 0.70, 0.82, 0.91]
HEADCOUNTS = [1, 2, 3, 5, 8]
DIMENSIONS = [
    "tone-preservation",
    "signal-grounding",
    "prospect-qualification",
    "bench-commitment-accuracy",
    "discovery-call-booking",
    "objection-handling",
]

# Templates: each is a (dimension, hiring_signal_template, difficulty) tuple
PROBE_TEMPLATES = [
    (
        "signal-grounding",
        "easy",
        "{company} posted {headcount} {role} roles on LinkedIn in the past 10 days.",
        ["hiring", "roles", "LinkedIn"],
    ),
    (
        "bench-commitment-accuracy",
        "medium",
        "{company} is scaling its {segment} team rapidly. CTO mentioned needing to 'move fast on hiring' in a recent interview.",
        ["scaling", "hiring"],
    ),
    (
        "tone-preservation",
        "medium",
        "{company} has an active Greenhouse listing for {headcount} engineers. Previous outreach received no reply.",
        ["Greenhouse", "engineers"],
    ),
    (
        "prospect-qualification",
        "hard",
        "{company} laid off 12% of staff 3 months ago but is now rehiring. Signal confidence is low.",
        ["laid off", "rehiring"],
    ),
    (
        "objection-handling",
        "hard",
        "{company} responded to previous outreach: 'We use a preferred vendor list and are not considering new staffing vendors.'",
        ["vendor", "staffing"],
    ),
    (
        "discovery-call-booking",
        "medium",
        "{company} opened your last email 4 times but did not reply. They have {headcount} open ML roles.",
        ["open", "ML"],
    ),
]

COMPANY_NAMES = [
    "Meridian Analytics", "Veltro Systems", "CrestPath AI", "NovaBridge",
    "Luminary Data", "Syncora Tech", "Axial Software", "Pinnacle Labs",
    "Stratum Cloud", "Helios Robotics",
]

ROLES = ["ML engineer", "data scientist", "backend engineer", "DevOps engineer", "AI researcher"]


def make_task(
    task_number: int,
    dimension: str,
    difficulty: str,
    signal_template: str,
    required_signals: list[str],
    company_size: str,
    segment: str,
    ai_maturity: float,
    signal_confidence: float,
    headcount: int,
    seed: int,
    rng: random.Random,
) -> dict:
    company = rng.choice(COMPANY_NAMES)
    role = rng.choice(ROLES)
    hiring_signal = signal_template.format(
        company=company, headcount=headcount, role=role, segment=segment
    )
    return {
        "task_id": f"TB-PG-{task_number:04d}",
        "source_mode": "programmatic",
        "difficulty": difficulty,
        "dimension": dimension,
        "input": {
            "hiring_signal_brief": hiring_signal,
            "bench_summary": (
                "Tenacious provides pre-vetted senior engineers on 2-week deployment timelines. "
                "Typical engagement: 3-6 months, option to convert. No placement fees."
            ),
            "prospect_profile": {
                "company_name": company,
                "company_size": company_size,
                "segment": segment,
                "requested_headcount": headcount,
                "tech_stack": rng.sample(["Python", "Go", "TypeScript", "Kubernetes", "React", "PyTorch"], 3),
                "ai_maturity_score": ai_maturity,
                "signal_confidence": signal_confidence,
            },
        },
        "candidate_output": "",
        "ground_truth": {
            "required_signal_references": required_signals,
            "banned_phrases": [
                "hope this finds you well", "circle back", "touch base",
                "synergy", "leverage", "reach out", "loop you in",
            ],
            "required_elements": ["calendar_link", "company_name_mention"],
            "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"],
        },
        "rubric": {
            "scoring_type": "hybrid",
            "threshold": 0.75,
            "dimensions": [
                {
                    "name": "banned_phrase_check",
                    "weight": 0.3,
                    "check_type": "not_contains",
                    "description": "No banned phrases.",
                    "check_value": "hope this finds you well|circle back|touch base|synergy|leverage|reach out",
                },
                {
                    "name": "signal_reference_check",
                    "weight": 0.3,
                    "check_type": "contains",
                    "description": "Must reference signal.",
                    "check_value": "|".join(required_signals),
                },
                {
                    "name": "calendar_link_check",
                    "weight": 0.1,
                    "check_type": "regex",
                    "description": "Must contain calendar link.",
                    "check_value": r"(calendly|cal\.com|savvycal|hubspot meetings)",
                },
                {
                    "name": "tone_judge",
                    "weight": 0.3,
                    "check_type": "llm_score",
                    "description": "LLM judge on 5 tone markers.",
                    "check_value": "",
                },
            ],
        },
        "metadata": {
            "week10_trace_ids": [],
            "week10_probe_ids": [],
            "partition": "train",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seed": seed,
            "generation_params": {
                "company_size": company_size,
                "segment": segment,
                "ai_maturity_score": ai_maturity,
                "signal_confidence": signal_confidence,
                "headcount": headcount,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="tenacious_bench_v0.1/train/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_tasks", type=int, default=90)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_number = 1
    tasks_written = 0
    combos = list(product(PROBE_TEMPLATES, COMPANY_SIZES, SEGMENTS[:3], AI_MATURITY_SCORES[:3], HEADCOUNTS[:3]))
    rng.shuffle(combos)

    for (dim, diff, template, signals), size, seg, ai_mat, headcount in combos:
        if tasks_written >= args.max_tasks:
            break
        task = make_task(
            task_number=task_number,
            dimension=dim,
            difficulty=diff,
            signal_template=template,
            required_signals=signals,
            company_size=size,
            segment=seg,
            ai_maturity=ai_mat,
            signal_confidence=rng.choice(SIGNAL_CONFIDENCES),
            headcount=headcount,
            seed=args.seed,
            rng=rng,
        )
        out_path = output_dir / f"{task['task_id']}.json"
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)
        task_number += 1
        tasks_written += 1

    print(f"Written {tasks_written} programmatic tasks to {args.output}")


if __name__ == "__main__":
    main()
