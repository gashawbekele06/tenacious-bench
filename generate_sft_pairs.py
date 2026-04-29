"""
generate_sft_pairs.py

Phase 1 of Path A: Generate gold-standard email outputs for each train task,
verify they pass programmatic rubric checks, and write to training_data/sft_pairs.jsonl
in Qwen3 chat-template format for Unsloth SFTTrainer.

Usage:
    python generate_sft_pairs.py \
        --input tenacious_bench_v0.1/train/ \
        --output training_data/sft_pairs.jsonl \
        --model claude-haiku-4-5 \
        --max_tasks 233 \
        --seed 42

Expected output: 180-230 passing pairs (~80% pass rate).
Estimated cost: ~$1-3 at claude-haiku-4-5 rates.
"""

import argparse
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(override=True)

SYSTEM_PROMPT = """You are a senior B2B sales writer for Tenacious Intelligence Corporation.
Tenacious places pre-vetted ML/software engineers at growth-stage companies on 2-week deployment timelines.

Your job: write a cold outreach email from the Tenacious sales rep to the prospect.

STYLE RULES (Tenacious Style Guide v2 — mandatory):
1. Subject line states intent directly. No "Quick question" or "Just checking in".
2. Reference the specific hiring signal from the brief (company name, role, signal date/count).
3. Name Tenacious's relevant bench capacity (engineers available, timeline).
4. One clear CTA: book a 20-min call via cal.com/tenacious.
5. Word count: body <= 120 words (cold outreach).
6. Tone: direct, evidence-based, low-pressure, professional.

BANNED PHRASES (any of these = automatic fail):
hope this finds you well, just following up, circling back, circle back, touch base,
synergy, synergize, leverage, ecosystem, world-class, top talent, A-players,
rockstar, ninja, wizard, skyrocket, supercharge, game-changer, disruptor,
paradigm shift, best-in-class, reach out, Quick question, Quick chat,
Don't miss out, You'll regret, Per my last email, bench (when referring to Tenacious engineers)

Write only the email (subject line + body). No preamble, no explanation."""

USER_TEMPLATE = """Write a Tenacious cold outreach email for this prospect.

Hiring signal: {hiring_signal_brief}

Bench summary: {bench_summary}

Prospect:
- Company: {company_name} ({company_size}, {segment})
- Requested headcount: {requested_headcount}
- AI maturity score: {ai_maturity_score}
- Signal confidence: {signal_confidence}

REQUIRED — you MUST use at least one of these exact phrases verbatim in the email body: {required_signal_references_str}
Calendar link to use: cal.com/tenacious"""


def call_claude(system: str, user: str, model: str = "claude-haiku-4-5") -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    r = client.chat.completions.create(
        model=f"anthropic/{model}",
        max_tokens=512,
        messages=[
            {"role": "user", "content": system + "\n\n" + user},
        ],
    )
    return r.choices[0].message.content.strip()


def is_metadata_phrase(phrase: str) -> bool:
    """True if the phrase is a rubric annotation, not a natural email phrase.
    Heuristics: contains = < > () [], looks like code notation, or is clearly
    a constraint description rather than something an email would contain.
    """
    if any(c in phrase for c in ("=", "<", ">", "(", ")", "[")):
        return True
    # Long phrases with underscores are rubric keys, not natural language
    if "_" in phrase and len(phrase) > 20:
        return True
    return False


def natural_signal_phrases(check_value: str) -> list[str]:
    """Return only the non-metadata phrases from a pipe-separated check_value."""
    return [p.strip() for p in check_value.split("|")
            if p.strip() and not is_metadata_phrase(p.strip())]


def count_words(text: str) -> int:
    lines = text.split("\n")
    body_lines = [l for l in lines if not l.lower().startswith("subject:")]
    body = " ".join(body_lines)
    return len(body.split())


def check_rubric(output: str, task: dict) -> tuple[bool, list[str]]:
    """Run all programmatic rubric checks. Returns (passed, list_of_failures)."""
    failures = []
    rubric = task.get("rubric", {})
    dimensions = rubric.get("dimensions", [])

    for dim in dimensions:
        check_type = dim.get("check_type")
        check_value = dim.get("check_value", "")
        name = dim.get("name", "")
        text = output.lower()

        if check_type == "not_contains":
            patterns = [p.strip() for p in check_value.split("|") if p.strip()]
            hits = [p for p in patterns if p.lower() in text]
            if hits:
                failures.append(f"{name}: banned phrases found: {hits}")

        elif check_type == "contains":
            patterns = natural_signal_phrases(check_value)
            if not patterns:
                # All phrases were metadata annotations — auto-pass this check
                pass
            elif not any(p.lower() in text for p in patterns):
                failures.append(f"{name}: required phrase not found (need one of: {patterns[:3]}...)")

        elif check_type == "regex":
            if not re.search(check_value, output, re.IGNORECASE):
                failures.append(f"{name}: regex not matched: {check_value}")

        elif check_type == "word_count":
            max_words = int(check_value)
            wc = count_words(output)
            if wc > max_words:
                failures.append(f"{name}: {wc} words > {max_words} limit")

    return len(failures) == 0, failures


def build_user_msg(task: dict) -> str:
    inp = task.get("input", {})
    pp = inp.get("prospect_profile", {})
    raw_refs = task.get("ground_truth", {}).get("required_signal_references", [])
    # Only pass natural-language phrases into the prompt; skip rubric annotations
    natural_refs = [r for r in raw_refs if not is_metadata_phrase(r)]
    refs_str = ", ".join(f'"{r}"' for r in natural_refs) if natural_refs else "(ground in the hiring signal brief)"
    return USER_TEMPLATE.format(
        hiring_signal_brief=inp.get("hiring_signal_brief", ""),
        bench_summary=inp.get("bench_summary", ""),
        company_name=pp.get("company_name", ""),
        company_size=pp.get("company_size", ""),
        segment=pp.get("segment", ""),
        requested_headcount=pp.get("requested_headcount", ""),
        ai_maturity_score=pp.get("ai_maturity_score", ""),
        signal_confidence=pp.get("signal_confidence", ""),
        required_signal_references_str=refs_str,
    )


def format_sft_record(task: dict, gold_output: str) -> dict:
    """Format as Qwen3 chat-template text for SFTTrainer (dataset_text_field='text')."""
    user_msg = build_user_msg(task)

    text = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_msg}<|im_end|>\n"
        f"<|im_start|>assistant\n{gold_output}<|im_end|>"
    )
    return {
        "task_id": task.get("task_id"),
        "dimension": task.get("dimension"),
        "text": text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="tenacious_bench_v0.1/train/")
    parser.add_argument("--output", default="training_data/sft_pairs.jsonl")
    parser.add_argument("--model", default="claude-haiku-4-5")
    parser.add_argument("--max_tasks", type=int, default=233)
    parser.add_argument("--max_retries", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tasks = []
    for p in sorted(input_dir.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            tasks.append(json.load(f))
    tasks = tasks[:args.max_tasks]
    print(f"Loaded {len(tasks)} tasks from {args.input}")

    passed, failed, skipped = 0, 0, 0
    log_rows = []

    with open(output_path, "w", encoding="utf-8") as out_f:
        for i, task in enumerate(tasks):
            tid = task.get("task_id", f"task_{i}")

            # Only generate for tasks with a prompt-answerable dimension
            if task.get("dimension") not in {
                "tone-preservation", "signal-grounding", "prospect-qualification",
                "bench-commitment-accuracy", "discovery-call-booking",
                "objection-handling", "cost-accuracy",
            }:
                skipped += 1
                continue

            attempt_passed = False
            last_failures = []

            for attempt in range(args.max_retries + 1):
                try:
                    user_msg = build_user_msg(task)
                    gold = call_claude(SYSTEM_PROMPT, user_msg, model=args.model)
                    ok, failures = check_rubric(gold, task)

                    if ok:
                        record = format_sft_record(task, gold)
                        out_f.write(json.dumps(record) + "\n")
                        out_f.flush()
                        passed += 1
                        attempt_passed = True
                        print(f"  [{i+1}/{len(tasks)}] {tid} PASS ({count_words(gold)} words)")
                        break
                    else:
                        last_failures = failures
                        if attempt < args.max_retries:
                            time.sleep(0.5)

                except Exception as e:
                    print(f"  [{i+1}/{len(tasks)}] {tid} ERROR: {e}")
                    last_failures = [str(e)]
                    time.sleep(1)

            if not attempt_passed:
                failed += 1
                print(f"  [{i+1}/{len(tasks)}] {tid} FAIL after {args.max_retries+1} attempts: {last_failures[:2]}")

            log_rows.append({"task_id": tid, "passed": attempt_passed, "failures": last_failures})
            time.sleep(0.3)

    log_path = output_path.parent / "sft_generation_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now(timezone.utc).isoformat(),
            "model": args.model,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(tasks),
            "pass_rate": round(passed / max(passed + failed, 1), 3),
            "rows": log_rows,
        }, f, indent=2)

    print(f"\nDone: {passed} pairs written to {output_path}")
    print(f"Failed: {failed} | Skipped: {skipped} | Pass rate: {passed/(passed+failed)*100:.1f}%")
    print(f"Log: {log_path}")
    print(f"\nNext step: upload training_data/sft_pairs.jsonl to Google Colab and run train_lora.py")


if __name__ == "__main__":
    main()
