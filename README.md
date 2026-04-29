# Tenacious-Bench v0.1

**A sales agent evaluation benchmark for Tenacious-specific B2B outreach quality**

> Built as part of TRP1 Week 11 — Sales Agent Evaluation Bench challenge.  
> Author: Gashaw Bekele | gashaw@10academy.org

---

## What This Is

Tenacious-Bench evaluates AI sales agents on failure modes that public benchmarks (τ²-Bench, AgentBench) miss:
tone preservation, hiring-signal grounding, bench commitment accuracy, and discovery-call booking in the
B2B engineering staffing domain.

The benchmark provides:
- **200–300 evaluation tasks** across 8 Tenacious-specific dimensions
- **A machine-verifiable scoring evaluator** (`scoring_evaluator.py`)
- **A trained LoRA adapter** (Path A) that lifts the Week 10 agent on the primary failure mode
- **A contamination-clean held-out partition** with statistical ablation results

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/gashabekele/tenacious-bench.git
cd tenacious-bench

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Fill in your ANTHROPIC_API_KEY, OPENROUTER_API_KEY, HF_TOKEN

# 4. Validate the schema with a dummy task
python scripts/validate_schema.py --task schema.json --example 0

# 5. Run the scoring evaluator on the dev set (once you have agent outputs)
python scoring_evaluator.py \
    --batch tenacious_bench_v0.1/dev/ \
    --agent_outputs your_outputs.jsonl
```

---

## Project Structure

```
tenacious-bench/
├── README.md                        ← You are here
├── schema.json                      ← Task schema + 1 example task
├── scoring_evaluator.py             ← Machine-verifiable scorer
├── contamination_check.py           ← N-gram + embedding + time-shift checks
├── audit_memo.md                    ← Act I: gap audit (≤600 words)
├── methodology.md                   ← Path declaration, partitioning, judge rotation
├── datasheet.md                     ← Gebru+Pushkarna dataset documentation
├── inter_rater_agreement.md         ← 30-task re-labeling results
├── cost_log.csv                     ← Every API + compute charge logged
├── evidence_graph.json              ← Every numeric claim → its source
│
├── tenacious_bench_v0.1/
│   ├── train/                       ← 50% — fine-tuning only
│   ├── dev/                         ← 30% — public, iterative eval
│   └── held_out/                    ← 20% — SEALED (gitignored)
│
├── generation_scripts/
│   ├── trace_derived.py             ← Mode 1: Week 10 traces → tasks
│   ├── programmatic.py             ← Mode 2: template combinatorics
│   ├── multi_llm_synthesis.py       ← Mode 3: Claude + Qwen routing
│   ├── judge_filter.py              ← LLM-as-a-judge quality filter
│   └── dedup.py                     ← N-gram + embedding dedup
│
├── training_data/                   ← Formatted for chosen path (gitignored contents)
├── training/
│   ├── train_lora.py               ← Unsloth LoRA training (Path A/B/C)
│   └── hyperparams.yaml            ← Pinned hyperparameters
│
├── ablations/
│   ├── run_ablations.py            ← Delta A/B/C + bootstrap CI
│   ├── ablation_results.json       ← Results (filled after Day 5)
│   └── held_out_traces.jsonl       ← Per-task scores for all ablations
│
└── synthesis_memos/
    ├── memo_synthetic_data_best_practices.md
    ├── memo_datasheets_data_cards.md
    ├── memo_contamination_prevention.md
    └── memo_llm_as_judge.md
```

---

## Status

| Phase | Status | Target |
|-------|--------|--------|
| Day 0 — Pre-flight | Complete | Sunday |
| Act I — Audit + Schema | Complete | Monday (interim: Wed 21:00 UTC) |
| Act II — Dataset Authoring | Complete (250 tasks) | Tue–Wed |
| Act III — Training Data Prep | Pending | Thursday |
| Act IV — Train + Ablate | Pending | Fri–Sat |
| Act V — Publish + Engage | Pending | Saturday (final: Sat 21:00 UTC) |

---

## Reproduce the Headline Number

```bash
# Run the scoring evaluator on the dev partition with your agent outputs
python scoring_evaluator.py \
    --batch tenacious_bench_v0.1/dev/ \
    --agent_outputs outputs/your_agent_outputs.jsonl

# Run ablations (after training)
python ablations/run_ablations.py \
    --held_out tenacious_bench_v0.1/held_out/ \
    --baseline_outputs ablations/baseline_outputs.jsonl \
    --trained_outputs ablations/trained_outputs.jsonl \
    --prompted_outputs ablations/prompted_outputs.jsonl
```

Stable within ±2pp. All scripts run from seed=42 (set in `.env`).

---

## Public Artifacts

| Artifact | URL |
|----------|-----|
| HuggingFace Dataset | [Fill in after Day 7] |
| HuggingFace Model (LoRA adapter) | [Fill in after Day 7] |
| Technical Blog Post | [Fill in after Day 7] |
| Community Engagement | [Fill in after Day 7] |

---

## License

Dataset: CC-BY-4.0  
Code: MIT
