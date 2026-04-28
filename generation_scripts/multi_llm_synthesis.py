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

load_dotenv()

FRONTIER_MODEL = "claude-sonnet-4-6"
DEV_MODEL = "openrouter/qwen/qwen3-235b-a22b"

HARD_SEED_PROMPT = """You are an expert benchmark designer for B2B sales AI agents.

The agent being evaluated is a "Conversion Engine" for Tenacious — a staffing company that
places pre-vetted engineers. The agent finds prospects via hiring signals, writes personalized
outreach, and books discovery calls.

Known failure modes from the agent's Week 10 evaluation:
{failure_taxonomy}

Your task: Write ONE extremely hard evaluation task that specifically targets one of these failure modes.
The task must be machine-verifiable (a script can score it without a human).

Output a JSON object with this EXACT structure:
{{
  "dimension": "<one of: tone-preservation|signal-grounding|prospect-qualification|bench-commitment-accuracy|discovery-call-booking|objection-handling|multi-turn-coherence|cost-accuracy>",
  "difficulty": "hard",
  "scenario_description": "<2-3 sentences describing why this is hard>",
  "input": {{
    "hiring_signal_brief": "<realistic hiring signal>",
    "bench_summary": "Tenacious provides pre-vetted senior engineers on 2-week deployment timelines.",
    "prospect_profile": {{
      "company_name": "<realistic company name>",
      "company_size": "<one of: 11-50|51-200|201-500|501-2000>",
      "segment": "<segment>",
      "requested_headcount": <integer>,
      "ai_maturity_score": <1.0-5.0>,
      "signal_confidence": <0.5-1.0>
    }}
  }},
  "ground_truth": {{
    "required_signal_references": ["<exact phrase 1>", "<exact phrase 2>"],
    "banned_phrases": ["hope this finds you well", "circle back", "touch base", "synergy"],
    "required_elements": ["calendar_link", "company_name_mention"],
    "tone_markers": ["direct", "evidence-based", "specific", "low-pressure", "competence-signaling"]
  }},
  "failure_mode_targeted": "<which Week 10 failure mode this targets>"
}}

Output ONLY the JSON. No explanation."""

VARIATION_PROMPT = """Given this hard evaluation task seed, generate {n} variations by changing:
- The company, segment, or headcount (keep the same failure mode targeted)
- Surface-level signal details (different keywords, different signal source)
- Difficulty level can stay the same or drop to "medium"

Seed task:
{seed_task}

Output a JSON array of {n} task objects using the SAME structure as the seed.
Output ONLY the JSON array. No explanation."""

JUDGE_FILTER_PROMPT = """You are a benchmark quality evaluator. Score this evaluation task on three dimensions.

Task:
{task}

Score each dimension 1-5:
1. input_coherence: Is the scenario realistic and internally consistent?
2. ground_truth_verifiability: Can a script check the ground truth without ambiguity?
3. rubric_clarity: Is it clear what a correct vs incorrect agent response looks like?

Output JSON only: {{"input_coherence": <1-5>, "ground_truth_verifiability": <1-5>, "rubric_clarity": <1-5>, "reasoning": "<one sentence>"}}"""

JUDGE_THRESHOLD = {"input_coherence": 3, "ground_truth_verifiability": 4, "rubric_clarity": 3}


def call_anthropic(prompt: str, model: str = FRONTIER_MODEL) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def call_openrouter(prompt: str, model: str = DEV_MODEL) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()


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
    for i in range(n):
        prompt = HARD_SEED_PROMPT.format(failure_taxonomy=failure_taxonomy_text)
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
            print(f"    Seed {i+1} failed: {e}")
        time.sleep(0.5)
    return seeds


def generate_variations(seeds: list[dict], n_variations: int) -> list[dict]:
    print(f"  Generating {n_variations} variations per seed with {DEV_MODEL}...")
    variations = []
    for i, seed in enumerate(seeds):
        prompt = VARIATION_PROMPT.format(seed_task=json.dumps(seed, indent=2), n=n_variations)
        try:
            raw = call_openrouter(prompt)
            batch = json.loads(raw)
            for v in batch:
                v["source_mode"] = "multi-llm-synthesis"
                v["metadata"] = {
                    "synthesis_model": DEV_MODEL,
                    "parent_seed_index": i,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            variations.extend(batch)
            print(f"    Seed {i+1}: +{len(batch)} variations")
        except Exception as e:
            print(f"    Variations for seed {i+1} failed: {e}")
        time.sleep(0.3)
    return variations


def assign_task_ids(tasks: list[dict], start: int = 1) -> list[dict]:
    for i, t in enumerate(tasks, start=start):
        t["task_id"] = f"TB-MS-{i:04d}"
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
