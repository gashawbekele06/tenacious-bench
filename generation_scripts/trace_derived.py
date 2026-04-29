"""
generation_scripts/trace_derived.py

Mode: Trace-Derived (~30% of dataset)

Converts Week 10 Tenacious agent outputs into benchmark tasks.
Data sources:
  - email_sink.jsonl  : 200 actual outreach emails the agent wrote
  - synthetic_prospects.json : 16 prospect profiles with hiring signals
  - probe_library.json : probe IDs to attach as metadata

Each (prospect profile + signals → email body) pair becomes one task.

Usage:
    python generation_scripts/trace_derived.py \
        --emails email_sink.jsonl \
        --prospects synthetic_prospects.json \
        --probes probe_library.json \
        --output tenacious_bench_v0.1/train/ \
        --seed 42 \
        --max_tasks 70
"""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path


BENCH_SUMMARY = (
    "Tenacious provides pre-vetted senior engineers on 2-week deployment timelines. "
    "Available bench: ML (5), Python/Backend (6), Fullstack (4), Data (3). "
    "NestJS stack committed through Q3 2026 on Modo Compass engagement."
)

BANNED_PHRASES = [
    "hope this finds you well", "circle back", "touch base",
    "synergy", "leverage", "best-in-class", "reach out",
    "loop you in", "end-to-end", "just wanted to",
]

# Map segment numbers to dimension focus
SEGMENT_DIMENSION = {
    1: "signal-grounding",       # post-raise, hiring surge
    2: "prospect-qualification", # post-layoff, cost discipline
    3: "signal-grounding",       # leadership change
    4: "signal-grounding",       # AI gap brief
}

# Probe IDs that apply by segment
SEGMENT_PROBES = {
    1: ["P-004", "P-005", "P-007"],
    2: ["P-001", "P-026"],
    3: ["P-006", "P-002"],
    4: ["P-028", "P-029", "P-030"],
}


def build_hiring_signal_brief(prospect: dict) -> str:
    """Construct a hiring_signal_brief string from a prospect's signals dict."""
    signals = prospect.get("signals", {})
    company = prospect.get("company_name", "Unknown Company")
    parts = []

    funding = signals.get("funding")
    if funding and funding.get("amount_usd"):
        amount = funding["amount_usd"]
        round_name = funding.get("round", "funding round")
        date = funding.get("announced_on", "recently")
        parts.append(
            f"{company} closed a ${amount:,} {round_name} on {date}."
        )

    roles = signals.get("open_engineering_roles")
    if roles:
        total = roles.get("total", 0)
        delta = roles.get("delta_60d", 0)
        parts.append(
            f"{total} open engineering roles posted"
            + (f" — up {delta} in the last 60 days." if delta else ".")
        )
        if roles.get("ml", 0):
            parts.append(f"ML-specific roles: {roles['ml']}.")
        if roles.get("python", 0):
            parts.append(f"Python roles: {roles['python']}.")

    leadership = signals.get("leadership_change_90d")
    if leadership:
        parts.append(f"Leadership change in the last 90 days: {leadership}.")

    layoffs = signals.get("layoffs_120d")
    if layoffs:
        parts.append(f"Layoff event in the last 120 days: {layoffs}.")

    ai = signals.get("ai_maturity_inputs", {})
    stack = ai.get("modern_data_stack", [])
    if stack:
        parts.append(f"Modern data stack detected: {', '.join(stack)}.")

    return " ".join(parts) if parts else f"{company} is actively hiring engineers."


def build_signal_references(prospect: dict) -> list[str]:
    """Extract key phrases from prospect signals for the rubric check_value."""
    signals = prospect.get("signals", {})
    refs = []

    funding = signals.get("funding")
    if funding and funding.get("round"):
        refs.append(funding["round"])

    roles = signals.get("open_engineering_roles", {})
    if roles.get("ml"):
        refs.append("ML")
    if roles.get("python"):
        refs.append("Python")
    if roles.get("total"):
        refs.append(str(roles["total"]))

    company = prospect.get("company_name", "")
    if company:
        refs.append(company.split()[0])  # first word of company name

    return refs[:4] if refs else ["hiring"]


def build_prospect_profile(prospect: dict) -> dict:
    """Build the prospect_profile sub-object from a synthetic prospect."""
    size_map = {
        range(1, 11): "1-10",
        range(11, 51): "11-50",
        range(51, 201): "51-200",
        range(201, 501): "201-500",
        range(501, 2001): "501-2000",
    }
    count = prospect.get("employee_count", 50)
    company_size = "51-200"
    for r, label in size_map.items():
        if count in r:
            company_size = label
            break

    segment_num = prospect.get("segment_hint", 1)
    segment_labels = {
        1: "Series B SaaS", 2: "Post-layoff / cost-discipline",
        3: "Leadership change", 4: "AI-gap prospect"
    }

    ai = prospect.get("signals", {}).get("ai_maturity_inputs", {})
    stack = ai.get("modern_data_stack", [])
    ai_score = 2.0
    if ai.get("named_ai_leadership"):
        ai_score += 1.0
    if ai.get("github_org_activity") == "high":
        ai_score += 0.5
    if len(stack) >= 3:
        ai_score += 0.5

    roles = prospect.get("signals", {}).get("open_engineering_roles", {})
    total_roles = roles.get("total", 2)
    delta = roles.get("delta_60d", 0)
    confidence = min(0.95, 0.55 + (delta / max(total_roles, 1)) * 0.3 + (0.1 if prospect.get("signals", {}).get("funding") else 0))

    return {
        "company_name": prospect.get("company_name", "Unknown"),
        "company_size": company_size,
        "segment": segment_labels.get(segment_num, "Series B SaaS"),
        "requested_headcount": min(total_roles, 5),
        "tech_stack": stack[:4] if stack else ["Python"],
        "ai_maturity_score": round(ai_score, 1),
        "signal_confidence": round(confidence, 2),
    }


def infer_dimension(email: dict, prospect: dict) -> str:
    segment = prospect.get("segment_hint", 1)
    body = email.get("body", "").lower()

    # Multi-turn if prior thread present
    if email.get("metadata", {}).get("turn", 1) > 1:
        return "objection-handling"

    # Layoff context → qualification task
    if prospect.get("signals", {}).get("layoffs_120d"):
        return "prospect-qualification"

    return SEGMENT_DIMENSION.get(segment, "signal-grounding")


def email_to_task(email: dict, prospect: dict, task_number: int, seed: int) -> dict:
    """Build one benchmark task from an email + its prospect."""
    segment = prospect.get("segment_hint", 1)
    dimension = infer_dimension(email, prospect)
    hiring_brief = build_hiring_signal_brief(prospect)
    signal_refs = build_signal_references(prospect)
    profile = build_prospect_profile(prospect)
    probe_ids = SEGMENT_PROBES.get(segment, ["P-010", "P-011"])

    return {
        "task_id": f"TB-TD-{task_number:04d}",
        "source_mode": "trace-derived",
        "difficulty": "medium",
        "dimension": dimension,
        "input": {
            "hiring_signal_brief": hiring_brief,
            "bench_summary": BENCH_SUMMARY,
            "prospect_profile": profile,
        },
        "candidate_output": "",
        "ground_truth": {
            "required_signal_references": signal_refs,
            "banned_phrases": BANNED_PHRASES,
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
                    "description": "No banned phrases from Tenacious style guide.",
                    "check_value": "|".join(BANNED_PHRASES),
                },
                {
                    "name": "signal_reference_check",
                    "weight": 0.3,
                    "check_type": "contains",
                    "description": "Must reference at least one hiring signal from the brief.",
                    "check_value": "|".join(signal_refs),
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
                    "description": "LLM judge scores on 5 Tenacious tone markers. Pass = avg >= 4/5.",
                    "check_value": "",
                },
            ],
        },
        "metadata": {
            "week10_trace_ids": [email.get("metadata", {}).get("prospect_id", "unknown")],
            "week10_probe_ids": probe_ids,
            "source_email_subject": email.get("subject", ""),
            "partition": "train",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seed": seed,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emails", default="email_sink.jsonl", help="Week 10 email_sink.jsonl")
    parser.add_argument("--prospects", default="synthetic_prospects.json", help="Week 10 synthetic_prospects.json")
    parser.add_argument("--probes", default="probe_library.json", help="Week 10 probe_library.json")
    parser.add_argument("--traces", default=None, help="Ignored — kept for CLI compatibility")
    parser.add_argument("--schema", default="schema.json")
    parser.add_argument("--output", default="tenacious_bench_v0.1/train/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max_tasks", type=int, default=70)
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load prospects indexed by id
    with open(args.prospects) as f:
        raw = json.load(f)
    prospects_list = raw.get("prospects", raw) if isinstance(raw, dict) else raw
    prospects = {p["id"]: p for p in prospects_list}
    print(f"Loaded {len(prospects)} prospect profiles")

    # Load emails
    emails = []
    with open(args.emails) as f:
        for line in f:
            line = line.strip()
            if line:
                emails.append(json.loads(line))
    print(f"Loaded {len(emails)} emails from {args.emails}")

    # Shuffle and cap
    random.shuffle(emails)
    emails = emails[: args.max_tasks]

    tasks_written = 0
    skipped = 0
    for i, email in enumerate(emails, start=2):  # start=2 to avoid collision with TB-TD-0001
        prospect_id = email.get("metadata", {}).get("prospect_id")
        if not prospect_id or prospect_id not in prospects:
            skipped += 1
            continue

        prospect = prospects[prospect_id]
        task = email_to_task(email, prospect, task_number=i, seed=args.seed)
        out_path = output_dir / f"{task['task_id']}.json"
        with open(out_path, "w") as f:
            json.dump(task, f, indent=2)
        tasks_written += 1

    print(f"Written {tasks_written} trace-derived tasks to {args.output}")
    if skipped:
        print(f"Skipped {skipped} emails (no matching prospect profile)")


if __name__ == "__main__":
    main()
