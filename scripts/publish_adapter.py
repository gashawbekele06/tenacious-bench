"""
scripts/publish_adapter.py

Uploads the trained LoRA adapter from training/output/ to HuggingFace Hub.

Run this from Colab (where the adapter was saved) or locally if you have
downloaded the adapter weights to training/output/.

Usage:
    python scripts/publish_adapter.py --adapter_dir training/output \
        --repo_id gashawbekele/tenacious-bench-lora-path-a

Colab usage (run in a cell after training):
    !python scripts/publish_adapter.py \
        --adapter_dir /content/tenacious-bench/training/output \
        --repo_id gashawbekele/tenacious-bench-lora-path-a
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter_dir", default="training/output",
                        help="Path to the saved LoRA adapter directory")
    parser.add_argument("--repo_id", default="gashawbekele/tenacious-bench-lora-path-a",
                        help="HuggingFace repo ID for the adapter")
    parser.add_argument("--dry_run", action="store_true",
                        help="Check files exist without uploading")
    args = parser.parse_args()

    adapter_path = Path(args.adapter_dir)
    if not adapter_path.exists():
        print(f"ERROR: adapter_dir '{adapter_path}' does not exist.")
        print("Train the adapter first with: python training/train_lora.py --config training/hyperparams.yaml --path A")
        return

    adapter_files = list(adapter_path.rglob("*"))
    print(f"Found {len(adapter_files)} files in {adapter_path}")
    for f in sorted(adapter_files)[:10]:
        print(f"  {f}")
    if len(adapter_files) > 10:
        print(f"  ... and {len(adapter_files) - 10} more")

    if args.dry_run:
        print(f"\nDRY RUN — would push to: https://huggingface.co/{args.repo_id}")
        return

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not set in .env")

    from huggingface_hub import HfApi
    api = HfApi()

    # Create repo if it doesn't exist
    try:
        api.create_repo(repo_id=args.repo_id, repo_type="model",
                        token=hf_token, exist_ok=True)
        print(f"Repo ready: https://huggingface.co/{args.repo_id}")
    except Exception as e:
        print(f"Repo create warning (may already exist): {e}")

    # Upload model card
    model_card_path = Path("model_card.md")
    if model_card_path.exists():
        api.upload_file(
            path_or_fileobj=str(model_card_path),
            path_in_repo="README.md",
            repo_id=args.repo_id,
            repo_type="model",
            token=hf_token,
        )
        print("Uploaded model_card.md → README.md")

    # Upload adapter files
    api.upload_folder(
        folder_path=str(adapter_path),
        repo_id=args.repo_id,
        repo_type="model",
        token=hf_token,
    )
    print(f"\nAdapter published: https://huggingface.co/{args.repo_id}")


if __name__ == "__main__":
    main()
