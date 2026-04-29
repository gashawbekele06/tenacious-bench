"""
scoring_evaluator.py

Machine-verifiable scorer for Tenacious-Bench tasks.

Usage:
    # Single task
    python scoring_evaluator.py --task examples/ex01_tone_preservation.json --output "..."

    # Batch (dev or held-out partition)
    python scoring_evaluator.py --batch tenacious_bench_v0.1/dev/ --agent_outputs outputs.jsonl

    # Demo mode — runs all three wired examples with passing mock outputs
    python scoring_evaluator.py --demo

Check-type to example mapping:
    not_contains    → ex01 (banned_phrase_check, w=0.45) — banned phrase avoidance
                      ex02 (confidence_gate_check, w=0.30) — low-confidence hedging
                      ex03 (banned_phrase_check, w=0.20) — defensive appeasement phrases
    contains        → ex01 (signal_reference_check, w=0.30) — Node.js / Vantage Pay
                      ex02 (signal_reference_check, w=0.40) — 12 ML roles / 60 days / NeuralCart
                      ex03 (case_study_reference_check, w=0.25) — Clearbit / 11 days
    regex           → ex01/02/03 (calendar_link_check) — calendly|cal.com|savvycal|hubspot
    word_count      → ex01 (w=0.05), ex02 (w=0.10) — cold outreach body ≤ 120 words
    llm_score       → ex03 (tone_judge, w=0.45) — all 5 Style Guide v2 markers:
                       direct, grounded, honest, professional, non_condescending

The evaluator runs programmatic checks first (not_contains, contains, regex, word_count),
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

load_dotenv(override=True)


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

# Exact 5-marker framework from Tenacious Style Guide v2.
# Each marker scored 1-5. Pass = every marker >= 4. Fail on any = regenerate.
TONE_JUDGE_PROMPT = """You are a tone evaluator for Tenacious Intelligence Corporation B2B sales outreach.

Score the draft below on the five Tenacious tone markers (1-5 each).
Pass threshold per marker: 4. A draft below 4 on any marker fails.

MARKER DEFINITIONS:

1. direct (1-5)
   5 = subject states intent ("Request:", "Context:", "Question:"); body has one clear ask; no filler.
   3 = one minor filler or vague ask.
   1 = "Quick/Just/Hey" subject; multi-paragraph self-intro; 2+ asks stacked; exceeds word limit.

2. grounded (1-5)
   5 = at least one specific signal named (funding amount+date, exact role count+trend, named layoff, named leadership change+date); phrasing matches signal confidence.
   3 = vague signal reference ("I see you are hiring") without specifics.
   1 = no signal referenced, OR "aggressive hiring" asserted on a signal with <3 open roles.

3. honest (1-5)
   5 = names what is unknown; uses interrogative phrasing for low-confidence signals; refuses to commit bench capacity or pricing not supported by brief.
   3 = minor overstatement of certainty.
   1 = asserts unsupported claims; commits capacity beyond brief; invents pricing or discount; fabricates peer data.

4. professional (1-5)
   5 = no banned phrases; "bench" does not appear externally; language calibrated to CTO/founder reader.
   3 = borderline jargon but no banned phrase.
   1 = any banned phrase present ("world-class", "top talent", "synergy", "leverage", "skyrocket", etc.); OR "bench" used in prospect-facing text; OR offshore clichés.

5. non_condescending (1-5)
   5 = any competitor or capability gap framed as a research finding or question; explicit acknowledgment that prospect may have already considered it.
   3 = neutral framing but no acknowledgment.
   1 = "falling behind," "behind the curve," "catch up," "you need to," "you should"; gap framed as prospect's leadership failure.

Output ONLY this JSON (no other text):
{{"direct": <1-5>, "grounded": <1-5>, "honest": <1-5>, "professional": <1-5>, "non_condescending": <1-5>, "reasoning": "<one sentence identifying the strongest and weakest marker>"}}

---
OUTREACH DRAFT TO SCORE:
{output}
---
"""


def llm_judge_score(candidate_output: str, model: str | None = None) -> dict[str, Any]:
    """Call the LLM judge via OpenRouter. Returns dict with scores and pass/fail."""
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )
        used_model = model or "anthropic/claude-haiku-4-5"
        response = client.chat.completions.create(
            model=used_model,
            max_tokens=300,
            messages=[{"role": "user", "content": TONE_JUDGE_PROMPT.format(output=candidate_output)}],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        scores = json.loads(raw)
        marker_keys = ["direct", "grounded", "honest", "professional", "non_condescending"]
        marker_scores = [scores[k] for k in marker_keys if k in scores]
        avg = sum(marker_scores) / len(marker_scores) if marker_scores else 0.0
        # Pass = average >= 4.0 across all five markers (Style Guide threshold)
        scores["average"] = round(avg, 2)
        scores["passed"] = avg >= 4.0
        return scores
    except Exception as e:
        return {"error": str(e), "passed": False, "average": 0.0}


# ---------------------------------------------------------------------------
# Word count check
# ---------------------------------------------------------------------------

def check_word_count(text: str, max_words: int) -> tuple[bool, str]:
    """Returns (passed, reason). Passed = word count <= max_words."""
    count = len(text.split())
    if count > max_words:
        return False, f"Word count {count} exceeds limit of {max_words}"
    return True, f"Word count {count} within limit of {max_words}"


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_task(task: dict, candidate_output: str, judge_model: str | None = None) -> dict:
    """
    Score a single task against candidate_output.

    Dimension → check_type mapping (see examples/ for wired demonstrations):
      ex01_tone_preservation.json
        banned_phrase_check      not_contains  w=0.45  28-phrase Style Guide v2 list
        signal_reference_check   contains      w=0.30  "Node.js|Vantage Pay"
        calendar_link_check      regex         w=0.20  calendly|cal.com|savvycal|hubspot
        word_count_check         word_count    w=0.05  body ≤ 120 words

      ex02_signal_grounding.json
        signal_reference_check   contains      w=0.40  "12 ML|60 days|NeuralCart"
        confidence_gate_check    not_contains  w=0.30  assertive phrases banned at confidence <0.55
        calendar_link_check      regex         w=0.20  calendly|cal.com|savvycal|hubspot
        word_count_check         word_count    w=0.10  body ≤ 120 words

      ex03_llm_judge.json   (hybrid scoring — programmatic + LLM)
        banned_phrase_check          not_contains  w=0.20  defensive appeasement phrases
        case_study_reference_check   contains      w=0.25  "Clearbit|11 days|11-day"
        calendar_link_check          regex         w=0.10  calendly|cal.com|savvycal|hubspot
        tone_judge                   llm_score     w=0.45  all 5 markers avg ≥ 4.0
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
        elif check_type == "word_count":
            # check_value is the max word count as a string (e.g. "120" for cold outreach)
            try:
                passed, reason = check_word_count(candidate_output, int(check_value))
            except ValueError:
                passed, reason = False, f"Invalid word_count check_value: {check_value!r}"
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

DEMO_EXAMPLES = [
    {
        "task_file": "examples/ex01_tone_preservation.json",
        "output": (
            "Subject: Node.js engineers for Vantage Pay\n\n"
            "Hi — noticed Vantage Pay posted five senior Node.js roles this week. "
            "We have four vetted Node.js engineers deployable in two weeks. "
            "Worth a 20-min call? cal.com/tenacious"
        ),
    },
    {
        "task_file": "examples/ex02_signal_grounding.json",
        "output": (
            "Subject: ML hiring at NeuralCart\n\n"
            "Hi — based on NeuralCart's 12 ML engineer postings over the last 60 days, "
            "it looks like you may be scaling your ML team. "
            "We have three vetted ML engineers available in two weeks. "
            "Worth comparing notes? cal.com/tenacious"
        ),
    },
    {
        "task_file": "examples/ex03_llm_judge.json",
        "output": (
            "Subject: Re: offshore concern\n\n"
            "That is a fair concern — communication gaps are the most common failure mode we see. "
            "The Clearbit team integrated one of our ML engineers in 11 days; "
            "their lead said the main difference was daily 9am standups in US-East timezone. "
            "Happy to share the specifics: cal.com/tenacious"
        ),
    },
]


def run_demo(judge_model: str | None = None) -> None:
    """Run the scorer against all three wired example tasks and print per-dimension results."""
    print("=== Tenacious-Bench Demo Mode ===\n")
    for entry in DEMO_EXAMPLES:
        task_path = Path(entry["task_file"])
        if not task_path.exists():
            print(f"[SKIP] {task_path} not found — run from repo root.\n")
            continue
        with open(task_path) as f:
            task = json.load(f)
        result = score_task(task, entry["output"], judge_model)
        print(f"Task: {result['task_id']}  ({task['dimension']})")
        print(f"  Overall: {result['overall_score']:.4f}  {'PASS' if result['passed'] else 'FAIL'}  (threshold={result['threshold']})")
        for dim in result["dimension_results"]:
            status = "PASS" if dim["passed"] else "FAIL"
            print(f"  [{status}] {dim['name']} (w={dim['weight']}) — {dim['reason']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Tenacious-Bench scoring evaluator")
    parser.add_argument("--task", type=str, help="Path to a single task JSON file")
    parser.add_argument("--output", type=str, help="Candidate output string (for single task mode)")
    parser.add_argument("--batch", type=str, help="Directory of task JSON files")
    parser.add_argument("--agent_outputs", type=str, help="JSONL file mapping task_id -> output")
    parser.add_argument("--judge_model", type=str, default=None, help="LLM judge model override")
    parser.add_argument("--demo", action="store_true",
                        help="Run scorer on all three wired examples (examples/ex01-03) and print per-dimension results")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.demo:
        run_demo(args.judge_model)

    elif args.task and args.output:
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
