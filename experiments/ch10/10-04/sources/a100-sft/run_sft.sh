#!/bin/bash -l
#===============================================================================
# SFT 全量微调 Qwen3 — 50k apex 混合数据, 4 节点 × 4 卡 = 16 卡
#
# 支持模型: Qwen3-4B-Base (默认) / Qwen3-8B-Base (通过 SFT_MODEL_PATH 切换)
#
# 数据: 50k apex SFT (my_data/sft_50k_apex/)
#   - 数学/科学: Thinking 模式 (~60%), 逻辑/代码: Non-thinking 模式 (~40%)
#   - max_length=8192 覆盖大部分数据
#
# 用法:
#   # 测试（5 步验证不 OOM，看 step time）
#   sbatch -o logs/sft_test_%j.out -e logs/sft_test_%j.err run_sft.sh test
#
#   # 正式训练
#   sbatch -o logs/sft_run_%j.out -e logs/sft_run_%j.err run_sft.sh run
#
#   # 切换 8B 模型（Slurm 只传递已 export 的变量；未 export 时作业内仍是默认 4B，wandb 名也不会变）
#   export SFT_MODEL_PATH=Qwen3-8B-Base
#   sbatch -o logs/sft_8b_test_%j.out -e logs/sft_8b_test_%j.err run_sft.sh test
#   # 或一行前缀环境（无需 export）:
#   SFT_MODEL_PATH=Qwen3-8B-Base sbatch -o logs/sft_8b_run_%j.out -e logs/sft_8b_run_%j.err run_sft.sh run
#
# 不传参数默认 test（仅跑 5 steps 快速验证）。
#
# 环境变量覆盖（不改脚本即可换模型/数据/实验名）:
#   SFT_MODEL_PATH      模型路径，相对名如 Qwen3-8B-Base 或绝对路径，默认 Qwen3-4B-Base
#   SFT_DATA_DIR         数据目录，相对名如 sft_20k_qwen3 或绝对路径
#   SFT_EXPERIMENT_NAME  实验名，用于 outputs/ 与 wandb（自动按模型生成默认值）
#   SFT_LR               学习率覆盖（默认 2e-5）
#   SFT_ENABLE_THINKING  是否启用 thinking 模式（默认 true，无 <think> 数据应设为 false）
# 单节点时须同时覆盖 nodes 与 ntasks（脚本默认 ntasks=4），且单节点通常无 128 CPU，需改 cpus-per-task。
#
# ---------- 当前模式: 全量微调 (Full Fine-Tuning) -------------------------
# 全量微调显存估算:
#   8B + A100-40G, max_length=8192, micro_batch=1 → ~35-40 GiB/卡
#   已启用 gradient_checkpointing 以节省显存
#
# [切换 LoRA 微调方法]
#   1. 添加 model.lora_rank=64 和 model.lora_alpha=128
#   2. 可移除 model.enable_gradient_checkpointing=true
# -----------------------------------------------------------------------
#===============================================================================

#SBATCH --job-name=sft-qwen3-4b-full
#SBATCH --account=p201251
#SBATCH --partition=gpu
#SBATCH --qos=default
#SBATCH --time=30:00:00
#SBATCH --nodes=4
#SBATCH --ntasks=4
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=128
#SBATCH --gpus-per-task=4
#SBATCH --exclusive
#SBATCH --output=logs/sft_run_%j.out
#SBATCH --error=logs/sft_run_%j.err

set -euxo pipefail

# ============ 测试 vs 正式：第 1 个参数 = test / run ============
RUN_MODE=${1:-test}
if [[ "$RUN_MODE" == "run" ]]; then
  TOTAL_EPOCHS=1
  MODE="正式"
  TOTAL_TRAINING_STEPS=""
  SAVE_FREQ=800
  TEST_FREQ=100
else
  TOTAL_EPOCHS=1
  MODE="测试"
  TOTAL_TRAINING_STEPS=5
  SAVE_FREQ=5
  TEST_FREQ=5
fi

# ============ 路径（可被环境变量覆盖，不改原代码）============
WORK_DIR=/project/home/p201251/hyl_ppo

if [[ -n "${SFT_MODEL_PATH:-}" ]]; then
  if [[ "${SFT_MODEL_PATH}" = /* ]]; then MODEL_PATH="${SFT_MODEL_PATH}"; else MODEL_PATH="${WORK_DIR}/${SFT_MODEL_PATH}"; fi
else
  MODEL_PATH="${WORK_DIR}/Qwen3-4B-Base"
fi
MODEL_NAME=$(basename "${MODEL_PATH}")

if [[ -n "${SFT_DATA_DIR:-}" ]]; then
  if [[ "${SFT_DATA_DIR}" = /* ]]; then DATA_DIR="${SFT_DATA_DIR}"; else DATA_DIR="${WORK_DIR}/my_data/${SFT_DATA_DIR}"; fi
else
  DATA_DIR="${WORK_DIR}/my_data/sft_40k_v2"
fi
DATA_NAME=$(basename "${DATA_DIR}")

if [[ "${MODEL_NAME}" == *"8B"* ]]; then
  DEFAULT_EXPERIMENT="sft_qwen3_8b_${DATA_NAME}"
else
  DEFAULT_EXPERIMENT="sft_qwen3_4b_${DATA_NAME}"
fi
LR="${SFT_LR:-2e-5}"
ENABLE_THINKING="${SFT_ENABLE_THINKING:-true}"
EXPERIMENT_NAME="${SFT_EXPERIMENT_NAME:-${DEFAULT_EXPERIMENT}}"
# 不再使用 run1/run2 后缀，run 模式与 experiment_name 保持一致
RUN_DISPLAY_NAME="${EXPERIMENT_NAME}"
if [[ "${RUN_MODE}" == "run" ]]; then
  SAVE_DIR="${WORK_DIR}/outputs/${EXPERIMENT_NAME}"
else
  SAVE_DIR="${WORK_DIR}/outputs/${EXPERIMENT_NAME}-test"
fi

echo "Training from scratch for ${TOTAL_EPOCHS} epoch(s)"

mkdir -p "${WORK_DIR}/logs"
cd "${WORK_DIR}"
source activate_verl.sh

export WANDB_PROJECT="sft-base-model"
export WANDB_NAME="${EXPERIMENT_NAME}"
export HYDRA_FULL_ERROR=1
# 缓解 CUDA 显存碎片，避免 OOM 时分配大块失败（见 PyTorch 文档）
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# NCCL 多节点调优：防止跨节点通讯超时，关闭不必要的调试输出
export NCCL_IB_TIMEOUT=50
export NCCL_DEBUG=${NCCL_DEBUG:-WARN}

# ============ 多节点 / 单节点 ============
NNODES=${SLURM_NNODES:-${SLURM_JOB_NUM_NODES:-1}}
NGPU_PER_NODE=${SLURM_GPUS_ON_NODE:-${SLURM_GPUS_PER_NODE:-4}}
TOTAL_GPUS=$((NNODES * NGPU_PER_NODE))

if [ "$NNODES" -gt 1 ]; then
  export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
  export MASTER_PORT=${MASTER_PORT:-29500}
  LAUNCHER="srun --nodes=${NNODES} --ntasks=${NNODES} --ntasks-per-node=1 \
    torchrun --nnodes=${NNODES} --nproc_per_node=${NGPU_PER_NODE} \
    --rdzv_backend=c10d --rdzv_endpoint=${MASTER_ADDR}:${MASTER_PORT}"
else
  LAUNCHER="torchrun --standalone --nnodes=1 --nproc_per_node=${NGPU_PER_NODE}"
fi

# ============ 打印运行信息 ============
echo "=============================================="
echo "SFT ${MODEL_NAME} + ${DATA_NAME} [${MODE}]"
echo "=============================================="
echo "run_mode:         ${RUN_MODE}"
echo "experiment_name:  ${EXPERIMENT_NAME}"
echo "wandb run name:   ${RUN_DISPLAY_NAME}"
echo "model:            ${MODEL_PATH}"
echo "data:             ${DATA_DIR}"
echo "max_length:       8192"
echo "finetune_mode:    full (gradient_checkpointing=true)"
echo "lr:               ${LR}"
echo "enable_thinking:  ${ENABLE_THINKING}"
echo "total_epochs:     ${TOTAL_EPOCHS}"
echo "save_freq:        ${SAVE_FREQ}"
echo "test_freq:        ${TEST_FREQ}"
[[ -n "${TOTAL_TRAINING_STEPS}" ]] && echo "total_training_steps: ${TOTAL_TRAINING_STEPS}"
echo "nodes:            ${NNODES}  (${SLURM_NODELIST:-local})"
echo "total_gpus:       ${TOTAL_GPUS}"
echo "started_at:       $(date -Iseconds)"
echo "=============================================="

MICRO_BATCH=${SFT_MICRO_BATCH:-1}
EXTRA_TRAINER_OPTS=()
[[ -n "${TOTAL_TRAINING_STEPS}" ]] && EXTRA_TRAINER_OPTS+=(trainer.total_training_steps=${TOTAL_TRAINING_STEPS})

$LAUNCHER \
    -m verl.trainer.sft_trainer \
    data.train_files="${DATA_DIR}/train.parquet" \
    data.val_files="${DATA_DIR}/test.parquet" \
    data.micro_batch_size_per_gpu=${MICRO_BATCH} \
    data.train_batch_size=$((TOTAL_GPUS * MICRO_BATCH)) \
    data.num_workers=4 \
    data.pin_memory=false \
    data.max_length=8192 \
    data.max_token_len_per_gpu=24576 \
    data.truncation=left \
    data.enable_thinking_default=${ENABLE_THINKING} \
    data.ignore_input_ids_mismatch=true \
    model.path="${MODEL_PATH}" \
    model.trust_remote_code=true \
    model.enable_gradient_checkpointing=true \
    engine.model_dtype=bfloat16 \
    optim.lr=${LR} \
    optim.lr_scheduler_type=cosine \
    optim.min_lr_ratio=0.1 \
    optim.lr_warmup_steps_ratio=0.01 \
    optim.weight_decay=0.1 \
    trainer.default_local_dir="${SAVE_DIR}" \
    trainer.project_name=sft-base-model \
    trainer.experiment_name="${RUN_DISPLAY_NAME}" \
    trainer.nnodes=${NNODES} \
    trainer.n_gpus_per_node=${NGPU_PER_NODE} \
    trainer.total_epochs=${TOTAL_EPOCHS} \
    trainer.save_freq=${SAVE_FREQ} \
    trainer.test_freq=${TEST_FREQ} \
    trainer.max_ckpt_to_keep=null \
    trainer.resume_mode=auto \
    "${EXTRA_TRAINER_OPTS[@]}"

echo "=============================================="
echo "SFT training finished: $(date -Iseconds)"
echo "Checkpoints saved to: ${SAVE_DIR}"
echo "=============================================="


