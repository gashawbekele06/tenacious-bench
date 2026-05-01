"""
training/train_lora.py

LoRA fine-tuning script using Unsloth + HuggingFace TRL.
Supports Path A (SFT), Path B (DPO/SimPO/ORPO), and Path C (reward modeling).

Run on Google Colab T4 (free) or RunPod 4090 (~$0.34/hr).
Expected wall time: 30-90 minutes for 1,000-3,000 pairs on Qwen 3.5 0.8B.

Usage:
    python training/train_lora.py --config training/hyperparams.yaml --path A

Environment:
    Set HF_TOKEN in .env to push adapter to HuggingFace Hub after training.
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_sft_dataset(data_dir: str):
    """Path A: Load chat-format input/output pairs."""
    from datasets import Dataset
    records = []
    for p in sorted(Path(data_dir).glob("*.jsonl")):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return Dataset.from_list(records)


def load_preference_dataset(data_dir: str):
    """Path B: Load (prompt, chosen, rejected) preference pairs."""
    from datasets import Dataset
    records = []
    for p in sorted(Path(data_dir).glob("*.jsonl")):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return Dataset.from_list(records)


def train_path_a(config: dict, dataset):
    """SFT a generation component with Unsloth + SFTTrainer."""
    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print("ERROR: unsloth not installed. Install with: pip install unsloth")
        sys.exit(1)

    from trl import SFTTrainer, SFTConfig
    from transformers import TrainingArguments

    print(f"\n[Path A — SFT] Loading backbone: {config['backbone']}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["backbone"],
        revision=config.get("backbone_revision", "main"),
        max_seq_length=config.get("max_seq_length", 2048),
        dtype=None,  # Auto-detect: fp16 on T4, bf16 on A100/4090
        load_in_4bit=False,  # Use 16-bit LoRA per Unsloth Qwen 3.5 guide
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=config.get("lora_r", 16),
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=config.get("lora_alpha", 16),
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=config.get("seed", 42),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=config.get("max_seq_length", 2048),
        args=SFTConfig(
            per_device_train_batch_size=config.get("batch_size", 2),
            gradient_accumulation_steps=config.get("grad_accum", 4),
            warmup_steps=config.get("warmup_steps", 5),
            num_train_epochs=config.get("epochs", 3),
            learning_rate=config.get("lr", 2e-4),
            fp16=not config.get("bf16", False),
            bf16=config.get("bf16", False),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=config.get("seed", 42),
            output_dir=config.get("output_dir", "training/output"),
        ),
    )

    print("\nStarting SFT training run...")
    trainer_stats = trainer.train()
    print(f"\nTraining complete. Loss: {trainer_stats.training_loss:.4f}")
    return model, tokenizer, trainer_stats


def train_path_b(config: dict, dataset):
    """DPO/SimPO/ORPO preference tuning."""
    try:
        from unsloth import FastLanguageModel, PatchDPOTrainer
        PatchDPOTrainer()
    except ImportError:
        print("ERROR: unsloth not installed.")
        sys.exit(1)

    algorithm = config.get("preference_algorithm", "orpo").lower()
    print(f"\n[Path B — {algorithm.upper()}] Loading backbone: {config['backbone']}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["backbone"],
        revision=config.get("backbone_revision", "main"),
        max_seq_length=config.get("max_seq_length", 2048),
        dtype=None,
        load_in_4bit=False,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=config.get("lora_r", 16),
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=config.get("lora_alpha", 16),
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=config.get("seed", 42),
    )

    training_args_kwargs = dict(
        per_device_train_batch_size=config.get("batch_size", 2),
        gradient_accumulation_steps=config.get("grad_accum", 4),
        num_train_epochs=config.get("epochs", 3),
        learning_rate=config.get("lr", 5e-5),
        fp16=not config.get("bf16", False),
        bf16=config.get("bf16", False),
        logging_steps=1,
        optim="adamw_8bit",
        seed=config.get("seed", 42),
        output_dir=config.get("output_dir", "training/output"),
    )

    if algorithm == "orpo":
        from trl import ORPOTrainer, ORPOConfig
        trainer = ORPOTrainer(
            model=model,
            args=ORPOConfig(**training_args_kwargs, max_length=config.get("max_seq_length", 2048)),
            train_dataset=dataset,
            tokenizer=tokenizer,
        )
    elif algorithm == "simpo":
        from trl import CPOTrainer, CPOConfig
        trainer = CPOTrainer(
            model=model,
            args=CPOConfig(**training_args_kwargs, loss_type="simpo"),
            train_dataset=dataset,
            tokenizer=tokenizer,
        )
    else:  # dpo
        from trl import DPOTrainer, DPOConfig
        trainer = DPOTrainer(
            model=model,
            args=DPOConfig(**training_args_kwargs),
            train_dataset=dataset,
            tokenizer=tokenizer,
        )

    print(f"\nStarting {algorithm.upper()} training run...")
    trainer_stats = trainer.train()
    print(f"\nTraining complete. Loss: {trainer_stats.training_loss:.4f}")
    return model, tokenizer, trainer_stats


def push_to_hub(model, tokenizer, config: dict):
    hf_token = os.environ.get("HF_TOKEN")
    hf_username = os.environ.get("HF_USERNAME", "your-handle")
    repo_name = config.get("adapter_repo_name", "tenacious-bench-lora")
    repo_id = f"{hf_username}/{repo_name}"

    print(f"\nPushing LoRA adapter to HuggingFace Hub: {repo_id}")
    model.push_to_hub(repo_id, token=hf_token)
    tokenizer.push_to_hub(repo_id, token=hf_token)
    print(f"Adapter pushed: https://huggingface.co/{repo_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="training/hyperparams.yaml")
    parser.add_argument("--path", choices=["A", "B", "C"], required=True, help="Training path")
    parser.add_argument("--data_dir", default="training_data/")
    parser.add_argument("--push_hub", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_seed{config.get('seed', 42)}"
    print(f"\n=== Tenacious-Bench Training Run: {run_id} ===")
    print(f"Path: {args.path} | Backbone: {config['backbone']}")

    if args.path == "A":
        dataset = load_sft_dataset(args.data_dir)
        print(f"SFT dataset size: {len(dataset)}")
        model, tokenizer, stats = train_path_a(config, dataset)
    elif args.path == "B":
        dataset = load_preference_dataset(args.data_dir)
        print(f"Preference dataset size: {len(dataset)}")
        model, tokenizer, stats = train_path_b(config, dataset)
    else:
        print("Path C (PRM) training: see training/train_prm.py")
        sys.exit(0)

    log = {
        "run_id": run_id,
        "path": args.path,
        "backbone": config["backbone"],
        "training_loss": stats.training_loss,
        "epochs": config.get("epochs", 3),
        "lr": config.get("lr"),
        "batch_size": config.get("batch_size"),
        "seed": config.get("seed", 42),
        "dataset_size": len(dataset),
    }
    log_path = Path("training") / f"training_run_{run_id}.log"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\nRun log written to {log_path}")

    if args.push_hub:
        push_to_hub(model, tokenizer, config)


if __name__ == "__main__":
    main()
