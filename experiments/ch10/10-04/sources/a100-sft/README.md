# Base-Model SFT with verl

Code repository for supervised fine-tuning (SFT) before Reinforcement Learning, built on [verl](https://github.com/volcengine/verl).

This project provides a practical and reproducible pipeline for training Qwen base models on a reasoning-focused instruction dataset, then evaluating checkpoints with a benchmark script.

## Project Links

- GitHub code repository: https://github.com/96kevinli29/base-model-sft-verl
- Hugging Face model card: https://huggingface.co/96kevinli29/Qwen3-4B-SFT
- Hugging Face dataset card: https://huggingface.co/datasets/96kevinli29/SFT-Dataset

## What This Repository Contains

- SFT training launcher: `run_sft.sh`
- Evaluation launcher: `run_benchmark.sh`
- Utility scripts and configs for distributed training
- Documentation for setup and workflow

## Why This Project

Many open RL pipelines skip or simplify the SFT stage. This repository focuses on that missing step:

- Start from a base model (for example `Qwen3-4B-Base` or `Qwen3-8B-Base`)
- Run full-parameter SFT on a high-quality mixed dataset
- Produce a stronger aligned checkpoint for later PPO/GRPO-style RL

## Quick Start

```bash
git clone https://github.com/96kevinli29/base-model-sft-verl.git
cd base-model-sft-verl
```

1. Prepare environment and dependencies.
   - Use `activate_verl.sh` as the environment entrypoint.
2. Prepare base model and dataset locally.
   - Base model path can be set with `SFT_MODEL_PATH`.
   - Dataset directory can be set with `SFT_DATA_DIR`.
3. Run a short sanity job first.
   - `sbatch -o logs/sft_test_%j.out -e logs/sft_test_%j.err run_sft.sh test`
4. Run full training.
   - `sbatch -o logs/sft_run_%j.out -e logs/sft_run_%j.err run_sft.sh run`
5. Run evaluation.
   - `sbatch -o logs/bench_full_%j.out -e logs/bench_full_%j.err run_benchmark.sh full`

## Environment Variables

- `SFT_MODEL_PATH`: base model directory (relative name or absolute path)
- `SFT_DATA_DIR`: dataset directory (relative under `my_data/` or absolute path)
- `SFT_EXPERIMENT_NAME`: output and W&B run name
- `SFT_LR`: override learning rate (default in script is `2e-5`)
- `SFT_ENABLE_THINKING`: enable thinking-style supervision (`true` by default)

## Outputs

- Training checkpoints: `outputs/<experiment_name>/`
- Training and benchmark logs: `logs/`

## Documentation

- English SFT flow: `sft_en.md`
- Chinese SFT flow: `sft_zh.md`
