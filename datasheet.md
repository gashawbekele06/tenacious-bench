# Tenacious-Bench v0.1 — Dataset Datasheet

*Following Gebru et al. (2021) "Datasheets for Datasets" and Pushkarna et al. (2022) "Data Cards"*  
*Layered detail: telescopic (summary) → periscopic (overview) → microscopic (details)*

---

## 1. Motivation (Telescopic)

**Why was this dataset created?**  
Tenacious-Bench v0.1 was created to evaluate B2B sales AI agents on Tenacious-specific failure modes
that existing public benchmarks (τ²-Bench, AgentBench) do not capture: tone preservation, signal grounding,
bench commitment accuracy, and prospect qualification in the staffing domain.

**Who created it and for what purpose?**  
Created by Gashaw (gashaw@10academy.org) as part of the TRP1 cohort Week 11 project. Primary purpose: evaluation and
LoRA adapter training for the Tenacious Conversion Engine.

**Funding / support:**  
10 Academy TRP1 program.

---

## 2. Composition (Periscopic)

**What does the dataset represent?**  
Evaluation tasks for a B2B sales outreach agent. Each task provides a prospect's hiring signal brief,
bench summary, and company profile. The agent must produce a personalized outreach email that passes
programmatic and LLM-judge quality checks.

**How many instances?**  
Total: 250 tasks — 233 train, 14 dev, 3 held-out.

> **Note (v0.1 limitation):** The multi-LLM synthesis stage generated variation tasks from 20 seed scenarios.
> Most variations share nearly identical hiring signals, which caused 48/51 initial held-out candidates to fail
> the ≥0.90 cosine contamination check. The held-out partition (3 tasks) is intentionally small for v0.1.
> v0.2 will seed held-out tasks from entirely disjoint prospect profiles.

**Dimension breakdown (Microscopic):**

| Dimension | Train | Dev | Held-out | Total |
|-----------|-------|-----|----------|-------|
| tone-preservation | 23 | 2 | 0 | 25 |
| signal-grounding | 72 | 2 | 0 | 74 |
| prospect-qualification | 51 | 2 | 0 | 53 |
| bench-commitment-accuracy | 28 | 1 | 1 | 30 |
| discovery-call-booking | 14 | 1 | 1 | 16 |
| objection-handling | 27 | 3 | 0 | 30 |
| multi-turn-coherence | 8 | 2 | 1 | 11 |
| cost-accuracy | 10 | 1 | 0 | 11 |
| **Total** | **233** | **14** | **3** | **250** |

**Source mode breakdown:**

| Mode | Count | % |
|------|-------|---|
| Trace-derived | 71 | 28.4% |
| Programmatic | 70 | 28.0% |
| Multi-LLM synthesis | 99 | 39.6% |
| Hand-authored adversarial | 10 | 4.0% |

**Is any information missing?**  
Candidate outputs are left blank in the dev and held-out partitions. Ground truth for the held-out
partition is sealed and will be released after the public leaderboard is published.

**Are there recommended data splits?**  
Yes. train/ for fine-tuning, dev/ for iterative evaluation, held_out/ for final sealed-slice scoring only.

---

## 3. Collection Process (Periscopic)

**How was data collected?**  
Four authoring modes (see `methodology.md`): trace-derived from Week 10 agent traces, programmatic
combinatorial expansion of probe templates, multi-LLM synthesis via OpenRouter, and hand-authored
adversarial tasks written by the dataset author.

**Who collected the data?**  
[Your name], with LLM assistance from Claude Sonnet 4.6 (Anthropic) and Qwen models (OpenRouter).

**Timeframe:**  
2026-04-27 to 2026-04-28 (Week 11 sprint)

**Ethical considerations:**  
All prospect profiles are synthetic. Company names, contact details, and hiring signals are
fabricated or derived from public domain signals only. No personally identifiable information.

---

## 4. Preprocessing / Cleaning (Microscopic)

**Preprocessing steps:**
1. PII redaction in trace-derived tasks (`generation_scripts/trace_derived.py`)
2. LLM-as-a-judge quality filter: all tasks scored on 3 dimensions, threshold per dimension documented
3. Deduplication: 6-gram overlap and cosine similarity < 0.90 (`generation_scripts/dedup.py`)
4. Contamination check: 8-gram (≥3 overlaps), embedding (≥0.90 cosine), time-shift (`contamination_check.py`) — all passed
5. Inter-rater agreement check on 30-task subset

**Raw data availability:**  
Raw traces from Week 10 not published (may contain Tenacious proprietary information).
Synthetic seed data and generation scripts available in `generation_scripts/`.

---

## 5. Uses (Telescopic)

**What tasks has the dataset been used for?**  
- LoRA fine-tuning of Qwen 3.5 backbone
- Ablation study (Delta A, B, C as defined in `ablations/run_ablations.py`)
- Baseline scoring of Week 10 agent

**Is there anything the dataset should NOT be used for?**  
- Do not use for general-purpose outreach generation without Tenacious-specific grounding
- Held-out partition must not be used for training under any circumstances

---

## 6. Distribution

**How is the dataset distributed?**  
HuggingFace Hub: `[your-handle]/tenacious-bench-v0.1`

**License:**  
CC-BY-4.0 — free to use with attribution.

**Citation:**  
```bibtex
@dataset{tenacious_bench_v01,
  author    = {[Your name]},
  title     = {Tenacious-Bench v0.1: A Sales Agent Evaluation Benchmark},
  year      = {2026},
  publisher = {HuggingFace Hub},
  url       = {https://huggingface.co/datasets/[your-handle]/tenacious-bench-v0.1}
}
```

---

## 7. Maintenance (Periscopic)

**Who maintains the dataset?**  
[Your name] — [your contact/GitHub]

**Will the dataset be updated?**  
v0.2 planned to address failure modes identified in the skeptic's appendix. Held-out tasks
will be released after leaderboard publication.

**What mechanisms exist for error reporting?**  
Open a GitHub Issue at [repo URL].
