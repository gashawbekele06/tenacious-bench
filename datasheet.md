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
Four authoring modes (see `methodology.md`):

| Mode | Script | Count | Description |
|------|--------|------:|-------------|
| Trace-derived | `generation_scripts/trace_derived.py` | 71 | Week 10 agent (email_sink.jsonl) → tasks via prospect profile matching |
| Programmatic | `generation_scripts/programmatic.py` | 70 | Combinatorial expansion of 6 probe templates × 4 company sizes × 5 segments × 5 AI-maturity scores × 5 headcounts |
| Multi-LLM synthesis | `generation_scripts/multi_llm_synthesis.py` | 99 | 40 hard seeds (Claude Haiku 4.5) × up to 5 variations (Qwen3-8B), judge-filtered |
| Hand-authored adversarial | manual | 10 | Written by dataset author to probe failure modes not reachable by the other three modes |

**Generation pipeline steps (Microscopic):**

1. **Seed generation** — frontier model (Claude Haiku 4.5) generates hard seed tasks anchored to each of the 8 failure dimensions
2. **Variation expansion** — dev-tier model (Qwen3-8B via OpenRouter) generates up to 5 variations per seed, changing company name, company size, and one signal detail
3. **Judge filter** — pointwise LLM judge scores each task on `input_coherence`, `ground_truth_verifiability`, and `rubric_clarity` (1–5 scale); tasks below threshold discarded. Rotation policy: generation model ≠ judge model
4. **Deduplication** — 6-gram and cosine similarity dedup (`generation_scripts/dedup.py`) removes near-duplicate tasks before partition assignment
5. **Contamination check** — 8-gram overlap and cosine similarity (threshold < 0.80) between held-out and all other partitions; time-shift verification for date-referenced signals
6. **Partition assignment** — stratified random split (seed=42): 50% train, 30% dev, 20% held-out

**Who collected the data?**  
Gashaw Bekele (gashaw@10academy.org), with LLM assistance from Claude Haiku 4.5 (Anthropic) and Qwen3-8B (OpenRouter via OpenRouter API).

**Timeframe:**  
2026-04-27 to 2026-04-28 (Week 11 sprint, ~36 hours total authoring time)

**Ethical considerations:**  
All prospect profiles are synthetic. Company names, contact details, and hiring signals are
fabricated or derived from public domain signals only. No personally identifiable information
is present in any task. The dataset does not represent any real person, company, or transaction.

---

## 4. Preprocessing / Cleaning / Labeling (Microscopic)

**Preprocessing steps (applied in order):**

1. **PII redaction** — trace-derived tasks: `prospect_id` fields replaced with synthetic IDs; real company names from Week 10 traces replaced with fictional names from a fixed list (`generation_scripts/trace_derived.py`)
2. **Schema normalisation** — all tasks serialised to a flat schema: nested `input`, `ground_truth`, `rubric`, `metadata` fields stored as JSON strings. This ensures consistent column types across train/dev splits on HuggingFace Hub
3. **LLM-as-a-judge quality filter** — every multi-LLM synthesis task scored on three dimensions:
   - `input_coherence` ≥ 3/5
   - `ground_truth_verifiability` ≥ 4/5
   - `rubric_clarity` ≥ 3/5
   - Threshold documented in `generation_scripts/judge_filter.py`; per-task pass/fail logged to `judge_filter_log.json`
4. **Deduplication** — 6-gram overlap and cosine similarity (all-MiniLM-L6-v2, threshold < 0.90) applied with AND logic: a pair must violate both conditions to be removed (`generation_scripts/dedup.py`)
5. **Contamination check** — separate from dedup, applied only to the held-out partition:
   - 8-gram overlap with ≥3 shared n-grams flagged
   - Cosine similarity ≥ 0.80 flagged (threshold intentionally stricter than dedup)
   - Time-shift: tasks referencing public date signals must have `created_at` metadata
   - Both held-out vs. train AND held-out vs. dev checked
6. **Inter-rater agreement** — 30-task subset double-labeled with 24h gap; rubric revised where dimension agreement fell below 80% (see `inter_rater_agreement.md`)
7. **SFT pair generation** — gold-standard email responses generated by Claude Haiku 4.5 for all 233 train tasks; 221/233 passed programmatic rubric (94.8% pass rate); 12 discarded after 3 failed retries

**Labeling methodology:**  
Ground truth labels (`required_signal_references`, `banned_phrases`, `required_elements`, `tone_markers`) are authored at task-creation time, not post-hoc. For trace-derived tasks, labels are derived from the Week 10 probe library and style guide. For programmatic tasks, labels are deterministically set from template parameters. For multi-LLM synthesis tasks, labels are generated by the frontier model and verified by the judge filter.

**Raw data availability:**  
Raw traces from Week 10 not published (may contain Tenacious proprietary information).
Synthetic seed data and all generation scripts are available in `generation_scripts/`.
SFT pairs are available in `training_data/sft_pairs.jsonl` (CC-BY-4.0).

---

## 5. Uses (Telescopic → Periscopic)

**What tasks has the dataset been used for?**

| Use | Details |
|-----|---------|
| LoRA fine-tuning (Path A SFT) | 221 SFT pairs from train partition; Qwen2.5-0.5B-Instruct backbone; 3 epochs; adapter published at `gashawbekele/tenacious-bench-lora-path-a` |
| Ablation study | Delta A (trained vs baseline), Delta B (trained vs prompted), Delta C (vs τ²-Bench reference); see `ablations/run_ablations.py` |
| Baseline scoring of Week 10 agent | `scoring_evaluator.py --batch tenacious_bench_v0.1/dev/` with Week 10 agent outputs |
| Inter-rater calibration | 30-task dev subset used to calibrate rubric and measure scorer reliability |

**Recommended use cases:**
- Evaluating B2B outreach AI agents on style compliance and signal grounding
- Training data for domain-specific SFT (train partition only)
- Rubric calibration and scorer development (dev partition)
- Leaderboard evaluation (held-out partition — do not use for training)

**Is there anything the dataset should NOT be used for?**
- Do not use for general-purpose outreach generation without Tenacious-specific grounding
- Held-out partition must not be used for training under any circumstances
- Do not use as a proxy for general sales effectiveness — the benchmark measures style compliance, not conversion rates
- Do not deploy outputs from models fine-tuned only on this dataset in production without independent evaluation on a larger held-out set

**Impact on downstream models:**  
Models fine-tuned on this dataset will learn Tenacious-specific tone constraints (28-phrase banned list, 5-marker profile). These constraints are domain-specific and should not be expected to transfer to other sales domains without modification.

---

## 6. Distribution

**How is the dataset distributed?**  
HuggingFace Hub: `gashabekele/tenacious-bench-v0.1` (to be published post-Week 11)

**License:**  
CC-BY-4.0 — free to use with attribution.

**Citation:**  
```bibtex
@dataset{tenacious_bench_v01,
  author    = {Gashaw Bekele},
  title     = {Tenacious-Bench v0.1: A Sales Agent Evaluation Benchmark},
  year      = {2026},
  publisher = {HuggingFace Hub},
  url       = {https://huggingface.co/datasets/gashabekele/tenacious-bench-v0.1}
}
```

---

## 6. Distribution (Periscopic)

**How is the dataset distributed?**  
HuggingFace Hub: [`gashawbekele/tenacious-bench-v0.1`](https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1)

The held-out partition (3 tasks) is sealed in the GitHub repo (`tenacious_bench_v0.1/held_out/`, gitignored from public release) and will be released after leaderboard publication.

**What form does the dataset take?**  
JSONL files (one task per line) in `tenacious_bench_v0.1/{train,dev,held_out}/`. Each file is also available as individual `.json` files per task in the GitHub repository. On HuggingFace Hub, nested fields (`input`, `ground_truth`, `rubric`, `metadata`) are serialised as JSON strings in a flat Parquet schema.

**License:**  
CC-BY-4.0 — free to use, share, and adapt with attribution.

**Rationale for CC-BY-4.0:**  
The dataset contains no personally identifiable information, no proprietary data, and no copyrighted third-party content. CC-BY-4.0 maximises research accessibility while requiring attribution, consistent with the Gebru et al. (2021) recommendation to clearly state re-use rights.

**Has the dataset been made available to others before this release?**  
No. The dataset was authored and released as part of the TRP1 Week 11 project sprint. No prior distribution.

**Citation:**
```bibtex
@dataset{tenacious_bench_v01,
  author    = {Gashaw Bekele},
  title     = {Tenacious-Bench v0.1: A Sales Agent Evaluation Benchmark},
  year      = {2026},
  publisher = {HuggingFace Hub},
  url       = {https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1},
  license   = {CC-BY-4.0}
}
```

---

## 7. Maintenance (Periscopic)

**Who maintains the dataset?**  
Gashaw Bekele — gashaw@10academy.org

**Will the dataset be updated?**  
v0.2 is planned to address the following known limitations:

| Limitation | v0.2 Fix |
|------------|----------|
| Held-out partition too small (n=3) | Seed held-out from entirely disjoint prospect profiles; target n=20 |
| Multi-LLM synthesis over-represented (39.6% vs 25% target) | Cap synthesis mode at 25%; expand hand-authored to 15% |
| Backbone capacity (0.5B cannot suppress context-copied banned words) | Retrain on Qwen2.5-1.5B with same 221 pairs |
| Metadata phrases in `required_signal_references` auto-pass | Add validation step to filter metadata-style check values at authoring time |

Held-out tasks will be released after leaderboard publication.

**What mechanisms exist for error reporting?**  
Open a GitHub Issue at https://github.com/gashawbekele06/tenacious-bench.

**Known limitations and biases (Microscopic):**

1. **Domain specificity** — all tasks model Tenacious's B2B engineering staffing domain. The signal structures (`hiring_signal_brief`, `bench_summary`) and tone constraints (28-phrase banned list) are specific to this company. Results do not generalise to other sales domains.

2. **Synthetic prospect profiles** — no real companies or contacts appear in the dataset. The synthetic profiles may not capture the full distribution of real prospect behavior, particularly edge cases in the objection-handling and multi-turn-coherence dimensions.

3. **LLM judge variance** — the `tone_judge` dimension relies on an LLM judge with κ=0.66 inter-rater agreement. Stochasticity in the judge introduces non-zero variance in all LLM-scored tasks. This is documented and within the acceptable range for published judge-based evaluations (Zheng et al., 2023).

4. **Author-as-sole-labeler** — all ground truth labels were authored by one person (Gashaw Bekele). While inter-rater agreement was measured with a 24h gap protocol, a true second labeler from outside the project would provide stronger calibration evidence.

5. **Held-out size** — with n=3 held-out tasks, the benchmark has insufficient statistical power to detect small effects. The bootstrap confidence interval collapses to [0, 0] at this sample size. v0.2 targets n=20.
