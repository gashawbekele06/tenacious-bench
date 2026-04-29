# Synthesis Memo — Contamination Prevention in Benchmarks

**Paper:** Oren et al. (2023) "Proving Test Set Contamination in Black-Box Language Models" (ICLR 2024);
supplemented by Yang et al. (2023) "Rethinking Benchmark and Contamination for Language Models with Rephrasing Samples"
**Author:** Gashaw Bekele
**Date:** 2026-04-28
**Status:** Final

---

## Core Argument

Oren et al. address the problem of detecting when benchmark test items have leaked into a language model's pretraining corpus. They propose a statistical test based on canonical ordering: if a model assigns higher likelihood to the canonical ordering of benchmark answer choices than to shuffled orderings, this is evidence of memorisation. Yang et al. complement this by showing that n-gram overlap alone is an unreliable contamination signal — paraphrase-level similarity routinely escapes n-gram filters while embedding-level similarity catches it. Together, the papers argue for a two-layer contamination check: lexical (n-gram) to catch exact or near-exact copies, and semantic (embedding cosine) to catch paraphrase-level duplicates.

---

## Three Design Choices Relevant to Tenacious-Bench

1. **Dual-layer contamination check.** `contamination_check.py` implements both 8-gram overlap (minimum 3 shared n-grams) and cosine similarity (threshold 0.90) between held-out and train partitions — a direct application of Yang et al.'s finding that n-gram alone is insufficient.

2. **Time-shift verification as a third layer.** Oren et al. show that temporal proximity between data collection and model cutoff is a contamination risk. The time-shift check in `contamination_check.py` flags any task referencing a public signal without a `created_at` metadata timestamp, ensuring every task has a documented provenance date.

3. **Dedup before partitioning, contamination check after.** Running deduplication first (removing within-pool near-duplicates via `dedup.py`) and then partitioning, followed by a cross-partition contamination check, is the sequence both papers implicitly recommend and the one our pipeline follows.

---

## Where I Disagree With the Paper

**Paper's recommendation:** Yang et al. recommend treating any n-gram overlap above a low threshold (5-gram, overlap >= 1) as a contamination signal requiring removal of the held-out item. Their argument is that erring toward removal is safer than risking contaminated evaluation.

**My choice:** Tenacious-Bench requires *both* 8-gram overlap >= 3 *and* cosine similarity >= 0.90 before flagging contamination. Neither condition alone triggers removal.

**Justification:** The conservative single-condition rule is appropriate for benchmarks where every test item has an independent provenance. Tenacious-Bench's variation generation deliberately creates tasks from the same seed scenario — different rubric dimensions applied to the same prospect signal. These tasks share surface phrases by design (a "Series B fintech, 40 engineers" scenario appears in multiple variations testing bench-commitment accuracy, signal-grounding, and cost-accuracy). Applying Yang et al.'s 5-gram >= 1 rule flagged 2,996 violations in our first contamination run — nearly the entire dataset — because the shared `bench_summary` text ("Tenacious provides pre-vetted ML engineers on 2-week deployment timelines") appears in every task. The AND criterion with n=8 and cosine >= 0.90 reduced this to 38 true positives: pairs where the hiring signal brief was semantically identical (cosine 1.0) despite surface variation. The three-run progression in our contamination_check.json output (2,996 violations with OR logic at n=8 / 111 with AND at n=8 / 38 with AND at cosine 0.90 / 0 after repartitioning) shows that the Yang et al. threshold would have eliminated structurally distinct evaluation items while the tighter criterion correctly identified only genuine duplicates.

---

## One Insight I Am Directly Applying

Yang et al.'s finding that embedding-level similarity catches paraphrase-level contamination that n-gram filters miss led directly to the `sentence-transformers` cosine check in `contamination_check.py`. Without it, variation tasks that change company names and signal details but keep the same rubric structure would appear clean under a pure n-gram filter while being semantically near-identical to train items. The embedding check is what correctly identified that TB-MS-0029 and TB-MS-0031 had cosine similarity 1.0 despite different surface text — the only reliable signal that they were true duplicates requiring partition correction.
