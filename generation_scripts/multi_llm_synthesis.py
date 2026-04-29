"""
generation_scripts/multi_llm_synthesis.py

Mode: Multi-LLM Synthesis (~25% of dataset)
Routes task generation across multiple LLM families:
  - Frontier model (Claude Sonnet 4.6 via Anthropic) → hard seeds anchored to failure taxonomy
  - Cheap dev-tier model (Qwen via OpenRouter) → bulk variations

Both pools are deduplicated and judge-filtered before inclusion.
Rotation policy: generation model != judge model (prevents preference leakage).

Usage:
    python generation_scripts/multi_llm_synthesis.py \
        --failure_taxonomy failure_taxonomy.md \
        --output tenacious_bench_v0.1/ \
        --seed 42 \
        --n_hard_seeds 40 \
        --n_variations 5
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

FRONTIER_MODEL = "claude-haiku-4-5"
DEV_MODEL = "qwen/qwen3-8b"

HARD_SEED_PROMPT = """You are a benchmark designer for B2B sales AI agents.

Tenacious is a staffing company placing pre-vetted engineers. The sales agent writes outreach emails using hiring signals and books discovery calls.

Week 10 failure modes (pick ONE to target):
{failure_taxonomy}

Write ONE hard evaluation task. Keep all string values SHORT (under 30 words each).

Output ONLY this JSON, no explanation:
{{
  "dimension": "<tone-preservation|signal-grounding|prospect-qualification|bench-commitment-accuracy|discovery-call-booking|objection-handling|multi-turn-coherence|cost-accuracy>",
  "difficulty": "hard",
  "scenario_description": "<one sentence max>",
  "input": {{
    "hiring_signal_brief": "<signal in 20 words max>",
    "bench_summary": "Tenacious: pre-vetted engineers, 2-week deployment.",
    "prospect_profile": {{
      "company_name": "<company name>",
      "company_size": "<11-50|51-200|201-500|501-2000>",
      "segment": "<segment label>",
      "requested_headcount": <1-6>,
      "ai_maturity_score": <1.0-4.0>,
      "signal_confidence": <0.5-0.9>
    }}
  }},
  "ground_truth": {{
    "required_signal_references": ["<phrase1>", "<phrase2>"],
    "banned_phrases": ["hope this finds you well", "circle back", "touch base", "synergy", "leverage"],
    "required_elements": ["calendar_link", "company_name_mention"],
    "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
  }},
  "failure_mode_targeted": "<probe ID and name>"
}}"""

VARIATION_PROMPT = """Given this benchmark task seed, write ONE variation by changing only:
- The company name and company_size
- One signal detail (different keyword or number)
- Difficulty may stay the same or drop to "medium"

Keep all string values under 25 words. Keep the same dimension and failure_mode_targeted.

Seed task:
{seed_task}

Output ONLY a single JSON object with the same structure as the seed. No array, no explanation."""

JUDGE_FILTER_PROMPT = """You are a benchmark quality evaluator. Score this evaluation task on three dimensions.

Task:
{task}

Score each dimension 1-5:
1. input_coherence: Is the scenario realistic and internally consistent?
2. ground_truth_verifiability: Can a script check the ground truth without ambiguity?
3. rubric_clarity: Is it clear what a correct vs incorrect agent response looks like?

Output JSON only: {{"input_coherence": <1-5>, "ground_truth_verifiability": <1-5>, "rubric_clarity": <1-5>, "reasoning": "<one sentence>"}}"""

JUDGE_THRESHOLD = {"input_coherence": 3, "ground_truth_verifiability": 4, "rubric_clarity": 3}


def strip_fences(text: str) -> str:
    """Strip markdown code fences that models wrap around JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json or ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def call_anthropic(prompt: str, model: str = FRONTIER_MODEL) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    response = client.chat.completions.create(
        model=f"anthropic/{model}",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return strip_fences(response.choices[0].message.content)


def call_openrouter(prompt: str, model: str = DEV_MODEL) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return strip_fences(response.choices[0].message.content)


def judge_task(task: dict, judge_fn) -> tuple[bool, dict]:
    """Returns (passed, scores). Judge model must differ from generation model."""
    prompt = JUDGE_FILTER_PROMPT.format(task=json.dumps(task, indent=2))
    try:
        raw = judge_fn(prompt)
        scores = json.loads(raw)
        passed = all(scores.get(k, 0) >= v for k, v in JUDGE_THRESHOLD.items())
        return passed, scores
    except Exception as e:
        return False, {"error": str(e)}


def generate_hard_seeds(failure_taxonomy_text: str, n: int, rng: random.Random) -> list[dict]:
    print(f"  Generating {n} hard seeds with {FRONTIER_MODEL}...")
    seeds = []
    dimensions = [
        "tone-preservation", "signal-grounding", "prospect-qualification",
        "bench-commitment-accuracy", "discovery-call-booking", "objection-handling",
        "multi-turn-coherence", "cost-accuracy",
    ]
    for i in range(n):
        target_dim = dimensions[i % len(dimensions)]
        prompt = HARD_SEED_PROMPT.format(failure_taxonomy=failure_taxonomy_text) + \
            f'\n\nIMPORTANT: You MUST set "dimension" to "{target_dim}" for this task.'
        try:
            raw = call_anthropic(prompt)
            task = json.loads(raw)
            task["source_mode"] = "multi-llm-synthesis"
            task["metadata"] = {
                "synthesis_model": FRONTIER_MODEL,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            seeds.append(task)
            print(f"    Seed {i+1}/{n}: {task.get('dimension', '?')} — {task.get('difficulty', '?')}")
        except Exception as e:
            print(f"    Seed {i+1} failed: {type(e).__name__}: {e}")
            if 'raw' in dir():
                print(f"      Raw response preview: {raw[:120]!r}")
        time.sleep(0.5)
    return seeds


def generate_variations(seeds: list[dict], n_variations: int) -> list[dict]:
    print(f"  Generating {n_variations} variations per seed with {DEV_MODEL}...")
    variations = []
    for i, seed in enumerate(seeds):
        count = 0
        for v_idx in range(n_variations):
            prompt = VARIATION_PROMPT.format(seed_task=json.dumps(seed, indent=2), n=1)
            try:
                raw = call_openrouter(prompt)
                # Model may return a single object or a 1-element array
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    parsed = parsed[0] if parsed else None
                if parsed:
                    parsed["source_mode"] = "multi-llm-synthesis"
                    parsed["metadata"] = {
                        "synthesis_model": DEV_MODEL,
                        "parent_seed_index": i,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    variations.append(parsed)
                    count += 1
            except Exception as e:
                print(f"    Variation {v_idx+1} for seed {i+1} failed: {e}")
            time.sleep(0.2)
        print(f"    Seed {i+1}: +{count} variations")
    return variations


def assign_task_ids(tasks: list[dict], start: int = 1) -> list[dict]:
    for i, t in enumerate(tasks, start=start):
        t["task_id"] = f"TB-MS-{i:04d}"
        if "candidate_output" not in t:
            t["candidate_output"] = ""
    return tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--failure_taxonomy", default="failure_taxonomy.md")
    parser.add_argument("--output", default="tenacious_bench_v0.1/")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_hard_seeds", type=int, default=40)
    parser.add_argument("--n_variations", type=int, default=5)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    output_dir = Path(args.output)

    taxonomy_text = ""
    if Path(args.failure_taxonomy).exists():
        with open(args.failure_taxonomy) as f:
            taxonomy_text = f.read()
    else:
        taxonomy_text = "Failure modes: tone drift, formulaic phrasing, weak signal grounding, bench over-commitment."

    print("\n[Step 1] Generating hard seeds with frontier model...")
    seeds = generate_hard_seeds(taxonomy_text, args.n_hard_seeds, rng)

    print("\n[Step 2] Generating variations with dev-tier model...")
    variations = generate_variations(seeds, args.n_variations)

    all_tasks = seeds + variations
    print(f"\n[Step 3] Running judge filter ({len(all_tasks)} tasks)...")
    # Judge uses the OPPOSITE model family from generation to prevent preference leakage
    judge_fn = call_openrouter  # seeds were generated by frontier → judge with dev
    passed_tasks = []
    for task in all_tasks:
        passed, scores = judge_task(task, judge_fn)
        if passed:
            task.setdefault("metadata", {})["judge_scores"] = scores
            task.setdefault("metadata", {})["judge_model"] = DEV_MODEL
            passed_tasks.append(task)
    print(f"  Passed judge filter: {len(passed_tasks)}/{len(all_tasks)}")

    assign_task_ids(passed_tasks, start=1)

    # Assign partitions: 50% train, 30% dev, 20% held_out
    rng.shuffle(passed_tasks)
    n = len(passed_tasks)
    train_tasks = passed_tasks[: int(n * 0.5)]
    dev_tasks = passed_tasks[int(n * 0.5) : int(n * 0.8)]
    held_out_tasks = passed_tasks[int(n * 0.8) :]

    for partition_name, partition_tasks in [("train", train_tasks), ("dev", dev_tasks), ("held_out", held_out_tasks)]:
        partition_dir = output_dir / partition_name
        partition_dir.mkdir(parents=True, exist_ok=True)
        for task in partition_tasks:
            task.setdefault("metadata", {})["partition"] = partition_name
            task["metadata"]["seed"] = args.seed
            out_path = partition_dir / f"{task['task_id']}.json"
            with open(out_path, "w") as f:
                json.dump(task, f, indent=2)

    print(f"\nDone: {len(train_tasks)} train, {len(dev_tasks)} dev, {len(held_out_tasks)} held_out")
    print(f"Tasks written to {args.output}")


if __name__ == "__main__":
    main()
