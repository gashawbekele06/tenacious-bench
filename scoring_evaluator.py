"""
scoring_evaluator.py

Machine-verifiable scorer for Tenacious-Bench tasks.
Usage:
    python scoring_evaluator.py --task schema.json --output "Your agent output here"
    python scoring_evaluator.py --batch tenacious_bench_v0.1/dev/ --agent_outputs outputs.jsonl

The evaluator runs programmatic checks first (banned phrases, required elements, regex),
then calls the LLM judge only for tasks with scoring_type = "hybrid" or "llm-judge".
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Programmatic checks
# ---------------------------------------------------------------------------

def check_not_contains(text: str, pattern: str) -> tuple[bool, str]:
    """Returns (passed, reason). Passed = text contains NONE of the pipe-separated patterns."""
    patterns = [p.strip() for p in pattern.split("|") if p.strip()]
    found = [p for p in patterns if p.lower() in text.lower()]
    if found:
        return False, f"Banned phrase(s) found: {found}"
    return True, "No banned phrases detected"


def check_contains(text: str, pattern: str) -> tuple[bool, str]:
    """Returns (passed, reason). Passed = text contains AT LEAST ONE pipe-separated pattern."""
    patterns = [p.strip() for p in pattern.split("|") if p.strip()]
    found = [p for p in patterns if p.lower() in text.lower()]
    if not found:
        return False, f"Required signal not found. Expected one of: {patterns}"
    return True, f"Signal reference found: {found}"


def check_regex(text: str, pattern: str) -> tuple[bool, str]:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return False, f"Regex not matched: {pattern}"
    return True, f"Regex matched: {match.group()}"


def check_exact_match(text: str, value: str) -> tuple[bool, str]:
    if text.strip() != value.strip():
        return False, "Exact match failed"
    return True, "Exact match"


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

TONE_JUDGE_PROMPT = """You are an expert evaluator for B2B sales outreach quality.

You will score the following email/outreach draft on the 5 Tenacious tone markers.
Score each marker 1-5 (5 = excellent).

Tone markers:
1. direct — Gets to the point without filler phrases
2. evidence-based — Grounds claims in specific signals or data
3. specific — Names specific details from the prospect's context
4. low-pressure — Does not push or use urgency tactics
5. competence-signaling — Demonstrates domain expertise without bragging

Output a JSON object with this exact structure (no other text):
{{"direct": <1-5>, "evidence_based": <1-5>, "specific": <1-5>, "low_pressure": <1-5>, "competence_signaling": <1-5>, "reasoning": "<one sentence>"}}

---
OUTREACH DRAFT:
{output}
---
"""


def llm_judge_score(candidate_output: str, model: str | None = None) -> dict[str, Any]:
    """Call the LLM judge. Returns dict with scores and pass/fail."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        used_model = model or "claude-sonnet-4-6"
        response = client.messages.create(
            model=used_model,
            max_tokens=256,
            messages=[{"role": "user", "content": TONE_JUDGE_PROMPT.format(output=candidate_output)}],
        )
        raw = response.content[0].text.strip()
        scores = json.loads(raw)
        avg = sum(v for k, v in scores.items() if k != "reasoning") / 5
        scores["average"] = round(avg, 2)
        scores["passed"] = avg >= 4.0
        return scores
    except Exception as e:
        return {"error": str(e), "passed": False, "average": 0.0}


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_task(task: dict, candidate_output: str, judge_model: str | None = None) -> dict:
    """
    Score a single task against candidate_output.
    Returns a result dict with per-dimension scores and an overall score.
    """
    rubric = task["rubric"]
    dimension_results = []
    total_weight = 0.0
    weighted_score = 0.0

    for dim in rubric["dimensions"]:
        check_type = dim["check_type"]
        weight = dim["weight"]
        check_value = dim.get("check_value", "")
        total_weight += weight

        if check_type == "not_contains":
            passed, reason = check_not_contains(candidate_output, check_value)
        elif check_type == "contains":
            passed, reason = check_contains(candidate_output, check_value)
        elif check_type == "regex":
            passed, reason = check_regex(candidate_output, check_value)
        elif check_type == "exact_match":
            passed, reason = check_exact_match(candidate_output, check_value)
        elif check_type == "llm_score":
            if rubric["scoring_type"] in ("hybrid", "llm-judge"):
                judge_result = llm_judge_score(candidate_output, judge_model)
                passed = judge_result.get("passed", False)
                reason = f"LLM judge avg={judge_result.get('average', 0):.2f}: {judge_result.get('reasoning', '')}"
            else:
                passed, reason = True, "LLM check skipped (programmatic mode)"
        else:
            passed, reason = False, f"Unknown check_type: {check_type}"

        dimension_results.append({
            "name": dim["name"],
            "weight": weight,
            "passed": passed,
            "score": 1.0 if passed else 0.0,
            "reason": reason,
        })
        weighted_score += weight * (1.0 if passed else 0.0)

    overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
    threshold = rubric.get("threshold", 0.75)

    return {
        "task_id": task["task_id"],
        "overall_score": round(overall_score, 4),
        "passed": overall_score >= threshold,
        "threshold": threshold,
        "dimension_results": dimension_results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench scoring evaluator")
    parser.add_argument("--task", type=str, help="Path to a single task JSON file")
    parser.add_argument("--output", type=str, help="Candidate output string (for single task mode)")
    parser.add_argument("--batch", type=str, help="Directory of task JSON files")
    parser.add_argument("--agent_outputs", type=str, help="JSONL file mapping task_id -> output")
    parser.add_argument("--judge_model", type=str, default=None, help="LLM judge model override")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.task and args.output:
        with open(args.task) as f:
            task = json.load(f)
        result = score_task(task, args.output, args.judge_model)
        print(json.dumps(result, indent=2))

    elif args.batch and args.agent_outputs:
        with open(args.agent_outputs) as f:
            outputs = {json.loads(line)["task_id"]: json.loads(line)["output"] for line in f}

        results = []
        task_dir = Path(args.batch)
        for task_file in sorted(task_dir.glob("*.json")):
            with open(task_file) as f:
                task = json.load(f)
            tid = task["task_id"]
            candidate = outputs.get(tid, "")
            result = score_task(task, candidate, args.judge_model)
            results.append(result)

        passed = sum(1 for r in results if r["passed"])
        print(f"\n=== Tenacious-Bench Results ===")
        print(f"Tasks scored : {len(results)}")
        print(f"Pass rate    : {passed}/{len(results)} = {passed/len(results)*100:.1f}%")
        print(f"Mean score   : {sum(r['overall_score'] for r in results)/len(results):.4f}")
        print("\nFull results written to scoring_results.json")
        with open("scoring_results.json", "w") as f:
            json.dump(results, f, indent=2)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
