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

# 4. Run the demo — scores 3 wired example tasks to verify the scorer works
python scoring_evaluator.py --demo

# 5. Run the scoring evaluator on the dev set (once you have agent outputs)
python scoring_evaluator.py \
    --batch tenacious_bench_v0.1/dev/ \
    --agent_outputs your_outputs.jsonl
```

---

## Project Structure

```
tenacious-bench/
├── README.md                          ← You are here
├── schema.json                        ← Task schema + 1 example task
├── scoring_evaluator.py               ← Machine-verifiable scorer (--demo flag)
├── contamination_check.py             ← N-gram + embedding + time-shift checks
├── audit_memo.md                      ← Act I: gap audit (≤600 words)
├── methodology.md                     ← Path declaration, partitioning, training results
├── methodology_rationale.md           ← Why Path A; Tülu 3 / LIMA / Magpie foundations
├── model_card.md                      ← Backbone, hyperparams, eval results, limitations
├── datasheet.md                       ← Gebru+Pushkarna dataset documentation
├── inter_rater_agreement.md           ← 30-task re-labeling, κ=0.95 overall
├── interimreport.md                   ← Days 1–3 interim report (bench + IRA + examples)
├── failure_taxonomy.md                ← 8-dimension failure taxonomy
├── tenacious_style_guide.md           ← 5 tone markers, 28 banned phrases
├── cost_log.csv                       ← Every API + compute charge (~$2.12 total)
├── evidence_graph.json                ← Every numeric claim → source file + field
├── memo.pdf                           ← 2-page exec memo (decision / skeptic's appendix)
├── blog_post.md                       ← ~1,400-word community blog post
├── community_issue_draft.md           ← GitHub issue text for τ²-Bench repo
│
├── tenacious_bench_v0.1/
│   ├── train/                         ← 233 tasks — fine-tuning only
│   ├── dev/                           ← 14 tasks — public, rubric calibration
│   └── held_out/                      ← 3 tasks — SEALED (gitignored)
│
├── examples/
│   ├── ex01_tone_preservation.json    ← Programmatic, easy, score=1.0000
│   ├── ex02_signal_grounding.json     ← Programmatic, medium, score=1.0000
│   └── ex03_llm_judge.json            ← Hybrid adversarial, hard, score=0.5500
│
├── generation_scripts/
│   ├── trace_derived.py               ← Mode 1: Week 10 traces → tasks
│   ├── programmatic.py                ← Mode 2: template combinatorics
│   ├── multi_llm_synthesis.py         ← Mode 3: Claude + Qwen routing
│   ├── judge_filter.py                ← LLM-as-a-judge quality filter
│   └── dedup.py                       ← N-gram + embedding dedup
│
├── training_data/                     ← 221 SFT pairs (gitignored contents)
├── training/
│   ├── train_lora.py                  ← Unsloth LoRA training (Path A)
│   ├── hyperparams.yaml               ← Pinned hyperparameters
│   └── training_run.log               ← Step loss curve 3.08→0.42, epoch summary
│
├── ablations/
│   ├── run_ablations.py               ← Delta A/B/C + bootstrap CI
│   ├── ablation_results.json          ← Delta A=0.0, Delta B=0.0, p=1.0
│   └── held_out_traces.jsonl          ← Per-task scores for all conditions
│
├── scripts/
│   ├── publish_hf.py                  ← Upload dataset to HuggingFace Hub
│   ├── generate_memo_pdf.py           ← Regenerate memo.pdf (reportlab)
│   └── generate_memo.js               ← Regenerate memo.docx (docx-js)
│
└── synthesis_memos/
    ├── memo_tulu3_sft_recipe.md        ← Lambert et al. (2024) — Path A SFT strategy
    ├── memo_lima_alignment.md          ← Zhou et al. (2023) — dataset size rationale
    ├── memo_magpie_synthesis.md        ← Xu et al. (2024) — SFT pair generation
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
| Act III — Training Data Prep | Complete (221/233 SFT pairs) | Thursday |
| Act IV — Train + Ablate | Complete (LoRA on T4, delta documented) | Fri–Sat |
| Act V — Publish + Engage | Complete | Saturday (final: Sat 21:00 UTC) |

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
| HuggingFace Dataset | [gashawbekele/tenacious-bench-v0.1](https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1) |
| HuggingFace Model (LoRA adapter) | [gashawbekele/tenacious-bench-lora-path-a](https://huggingface.co/gashawbekele/tenacious-bench-lora-path-a) |
| Blog Post | [HuggingFace Community Post](https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1/discussions/1) |
| Executive Memo | [memo.pdf](memo.pdf) |
| Community Engagement | [τ²-Bench Issue #81](https://github.com/sierra-research/tau-bench/issues/81) |

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [methodology.md](methodology.md) | Path declaration, partitioning protocol, training results, ablation findings |
| [methodology_rationale.md](methodology_rationale.md) | Why Path A; Tülu 3 / LIMA / Magpie design choices and departures |
| [model_card.md](model_card.md) | Backbone, hyperparams, eval results (Delta A/B/C), limitations |
| [interimreport.md](interimreport.md) | Days 1–3 bench composition, IRA, worked examples, forward plan |
| [datasheet.md](datasheet.md) | Gebru + Pushkarna dataset documentation |
| [audit_memo.md](audit_memo.md) | Act I gap audit (Week 10 failure mode analysis) |
| [inter_rater_agreement.md](inter_rater_agreement.md) | 30-task re-labeling Cohen's kappa results (κ=0.95 overall) |
| [synthesis_memos/](synthesis_memos/) | 7 paper synthesis memos (incl. Tülu 3, LIMA, Magpie for Path A) |
| [examples/](examples/) | Three wired example tasks (ex01–ex03) for scorer validation |
| [training/training_run.log](training/training_run.log) | Step-by-step loss curve and convergence assessment |

---

## License

Dataset: CC-BY-4.0  
Code: MIT
