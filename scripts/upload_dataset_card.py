"""
scripts/upload_dataset_card.py

Uploads a README.md (dataset card) to the HuggingFace dataset repo.
Run after publish_hf.py to populate the "Dataset card" tab on HF.

Usage:
    python scripts/upload_dataset_card.py --repo_id gashawbekele/tenacious-bench-v0.1
"""

import argparse
import os
from dotenv import load_dotenv

load_dotenv(override=True)

CARD_CONTENT = """\
---
language:
- en
license: cc-by-4.0
task_categories:
- text-generation
task_ids:
- language-modeling
tags:
- evaluation
- benchmark
- sales-agent
- b2b
- style-compliance
- lora
- sft
pretty_name: Tenacious-Bench v0.1
size_categories:
- n<1K
---

# Tenacious-Bench v0.1

**A style-compliance evaluation benchmark for B2B sales AI agents**

> Author: Gashaw Bekele | gashaw@10academy.org
> Built for TRP1 Week 11 — Sales Agent Evaluation Bench challenge
> Code: https://github.com/gashawbekele06/tenacious-bench

---

## What This Is

Tenacious-Bench evaluates AI sales agents on failure modes that public benchmarks
(τ²-Bench, AgentBench) miss: tone preservation, hiring-signal grounding, bench
commitment accuracy, and discovery-call booking in the B2B engineering staffing domain.

**250 tasks** across 8 failure dimensions, 4 authoring modes, and 3 partitions.

This dataset release contains the `train` (233 tasks) and `dev` (14 tasks) splits.
The `held_out` split (3 tasks) is sealed for leaderboard evaluation.

---

## Dataset Structure

Each row contains:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique task identifier (e.g. `TB-MS-0001`) |
| `source_mode` | string | `trace-derived`, `programmatic`, `multi-llm-synthesis`, or `hand-authored` |
| `difficulty` | string | `easy`, `medium`, `hard`, or `adversarial` |
| `dimension` | string | One of 8 failure dimensions (see below) |
| `input` | string (JSON) | `hiring_signal_brief`, `bench_summary`, `prospect_profile` |
| `candidate_output` | string | Candidate email to be scored |
| `ground_truth` | string (JSON) | Banned phrases, required elements, tone markers |
| `rubric` | string (JSON) | Scoring dimensions with weights and check types |
| `metadata` | string (JSON) | Source info, judge scores, generation params |

### 8 Failure Dimensions

| Dimension | Tasks | Description |
|-----------|------:|-------------|
| signal-grounding | 74 | Evidence-based hiring signal citation with numeric anchor |
| prospect-qualification | 53 | Segment assignment + disqualifier logic |
| objection-handling | 30 | Offshore-perception, pricing, and escalation responses |
| bench-commitment-accuracy | 30 | Capacity claims vs. actual availability |
| tone-preservation | 25 | 5-marker style guide compliance (banned phrases) |
| discovery-call-booking | 16 | Calendar link + CTA validity |
| cost-accuracy | 11 | Deploy window and engagement pricing |
| multi-turn-coherence | 11 | Tone drift across conversation turns |

---

## Scoring

Use [`scoring_evaluator.py`](https://github.com/gashawbekele06/tenacious-bench/blob/main/scoring_evaluator.py)
to score agent outputs. Five check types:

- `not_contains` — banned phrase check (28-phrase Tenacious Style Guide v2 list)
- `contains` — required evidence citation check
- `regex` — structural requirements (calendar links, date formats)
- `word_count` — concision enforcement
- `llm_score` — LLM judge scoring against 5 tone markers (1–5 scale, avg ≥ 4.0 to pass)

Run the demo:
```bash
python scoring_evaluator.py --demo
```

---

## Baseline Results (Path A SFT)

LoRA adapter: [`gashawbekele/tenacious-bench-lora-path-a`](https://huggingface.co/gashawbekele/tenacious-bench-lora-path-a)

| Comparison | Delta | p-value |
|-----------|:-----:|:-------:|
| Trained vs Baseline (n=3) | 0.0 | 1.0 |
| Trained vs Prompted (n=3) | 0.0 | 1.0 |
| Output length reduction | −18% | — |

Delta = 0.0 is a measurement artefact (n=3 held-out, metadata auto-pass).
The adapter learned concision (−18% length reduction); v0.2 on Qwen2.5-1.5B is planned.

---

## Citation

```bibtex
@misc{bekele2026tenaciousbench,
  title={Tenacious-Bench v0.1: A Style-Compliance Evaluation Benchmark for B2B Sales Agents},
  author={Bekele, Gashaw},
  year={2026},
  note={TRP1 Week 11, 10 Academy. https://huggingface.co/datasets/gashawbekele/tenacious-bench-v0.1}
}
```

## License

CC-BY-4.0
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_id", default="gashawbekele/tenacious-bench-v0.1")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not set in .env")

    from huggingface_hub import HfApi
    api = HfApi()

    import tempfile, os as _os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                     delete=False, encoding="utf-8") as f:
        f.write(CARD_CONTENT)
        tmp_path = f.name

    try:
        api.upload_file(
            path_or_fileobj=tmp_path,
            path_in_repo="README.md",
            repo_id=args.repo_id,
            repo_type="dataset",
            token=hf_token,
        )
        print(f"Dataset card uploaded to: https://huggingface.co/datasets/{args.repo_id}")
    finally:
        _os.unlink(tmp_path)


if __name__ == "__main__":
    main()
