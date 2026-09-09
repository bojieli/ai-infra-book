#!/bin/bash
#SBATCH --exclude=nid007542
#SBATCH --nodes=32
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=40
#SBATCH --mem=256G
#SBATCH -p standard-g
#SBATCH -t 48:00:00
#SBATCH --gpus-per-node=mi250:8
#SBATCH --exclusive=user
#SBATCH --hint=nomultithread
#SBATCH --account=project_462000119
#SBATCH -o logs/%j.out
#SBATCH -e logs/%j.err

VARIANT=1b191b91bval
VARIANT_CKPT=1b191b91b

# if run without sbatch, invoke here
if [ -z $SLURM_JOB_ID ]; then
    mkdir -p logs
    sbatch "$0"
    exit
fi

set -euo pipefail

# symlink logs/latest.out and logs/latest.err
ln -f -s $SLURM_JOB_ID.out logs/latest.out
ln -f -s $SLURM_JOB_ID.err logs/latest.err

KILL_SWITCH_PATH=kill-switch-$VARIANT
CHECKPOINT_PATH=checkpoints_$VARIANT_CKPT
TENSORBOARD_PATH=tensorboard_$VARIANT

# Data
VOCAB_FILE="gpt2/vocab.json"
MERGE_FILE="gpt2/merges.txt"
#DATA_PATH="/scratch/project_462000119/data/pile/megatron_data/meg-gpt2_pile_text_document"
TRAIN_DATA_PATH=train12b.txt
# "train: 1.0 0:1 /scratch/project_462000119/data/c4_subsampled/gpt2tok_c4_en_12B_text_document"
VALID_DATA_PATH=val.txt
# "validation: 1.0 0:1 /scratch/project_462000119/data/c4_validation/gpt2tok_c4validation_rerun_text_document"

PP_SIZE=1
TP_SIZE=1

MICRO_BATCH_SIZE=1
GRADIENT_ACCUMULATION_STEPS=1
WORLD_SIZE=$((SLURM_GPUS_ON_NODE*SLURM_JOB_NUM_NODES))
GLOBAL_BATCH_SIZE=$((MICRO_BATCH_SIZE*WORLD_SIZE*GRADIENT_ACCUMULATION_STEPS))

# Model parameters
source model_params.sh
MODEL_PARAM=("${PARAM_1143M[@]}")
NHIDDEN=${MODEL_PARAM[0]}
FFN_HIDDEN_SIZE=${MODEL_PARAM[1]}
KV_SIZE=${MODEL_PARAM[2]}
NHEADS=${MODEL_PARAM[3]}
NLAYERS=${MODEL_PARAM[4]}
SEQ_LEN=2048

echo "Model parameters: d_model $NHIDDEN ffw_size $FFN_HIDDEN_SIZE kv_size $KV_SIZE n_heads $NHEADS n_layers $NLAYERS"

SAVE_INTERVAL=1000

# Tokens: 90964260000
# -> Samples: 44416143
TRAIN_SAMPLES=1

OPTIMIZER_ARGS=" \
    --optimizer adam \
    --adam-beta1 0.9 \
    --adam-beta2 0.999 \
    --adam-eps 1e-8 \
    --lr 2e-4 \
    --min-lr 2e-5 \
    --lr-decay-style cosine \
    --lr-decay-samples $TRAIN_SAMPLES \
    --lr-warmup-samples 0 \
    --clip-grad 1.0 \
    --weight-decay 1e-1 \
    --override-lr-scheduler \
    --reset-progress \
    --no-load-optim \
    "

GPT_ARGS=" \
    --num-layers $NLAYERS \
    --hidden-size $NHIDDEN \
    --num-attention-heads $NHEADS \
    --kv-channels $KV_SIZE \
    --ffn-hidden-size $FFN_HIDDEN_SIZE \
    --seq-length $SEQ_LEN \
    --max-position-embeddings $SEQ_LEN \
    --micro-batch-size $MICRO_BATCH_SIZE \
    --global-batch-size $GLOBAL_BATCH_SIZE \
    --train-samples $TRAIN_SAMPLES \
    --vocab-file $VOCAB_FILE \
    --merge-file $MERGE_FILE \
    --clip-grad 1.0 \
    --kill-switch-path $KILL_SWITCH_PATH \
    --bf16 \
    $OPTIMIZER_ARGS \
    "

OUTPUT_ARGS=" \
    --log-interval 10 \
    --save-interval $SAVE_INTERVAL \
    --eval-interval 1 \
    --eval-iters 100 \
    --eval-only true \
    --tensorboard-dir $TENSORBOARD_PATH \
    --tensorboard-queue-size 5 \
    --log-timers-to-tensorboard \
    --log-batch-size-to-tensorboard \
    --log-validation-ppl-to-tensorboard \
    "

ZERO_STAGE=0

mkdir -p ds_configs
DS_CONFIG_PATH="ds_configs/$SLURM_JOB_ID.json"

cat <<EOF > $DS_CONFIG_PATH
{
    "train_micro_batch_size_per_gpu": $MICRO_BATCH_SIZE,
    "train_batch_size": $GLOBAL_BATCH_SIZE,
    "gradient_clipping": 1.0,
    "zero_optimization": {
        "stage": $ZERO_STAGE
    },
    "bf16": {
        "enabled": true
    },
    "steps_per_print": 2000,
    "wall_clock_breakdown": false
}
EOF

DEEPSPEED_ARGS=" \
    --deepspeed \
    --deepspeed_config $DS_CONFIG_PATH \
    --zero-stage $ZERO_STAGE \
    "

CMD=" \
    Megatron-DeepSpeed/pretrain_gpt.py \
    --tensor-model-parallel-size $TP_SIZE \
    --pipeline-model-parallel-size $PP_SIZE \
    $GPT_ARGS \
    $OUTPUT_ARGS \
    --save $CHECKPOINT_PATH \
    --load $CHECKPOINT_PATH \
    --train-weighted-split-paths-path $TRAIN_DATA_PATH \
    --valid-weighted-split-paths-path $VALID_DATA_PATH \
    --data-impl mmap \
     $DEEPSPEED_ARGS \
    "

echo $CMD

echo "START $SLURM_JOBID: $(date)"

# bash launch_srun_32.sh $CMD
srun --label launch.sh $CMD

echo "END $SLURM_JOBID: $(date)"
