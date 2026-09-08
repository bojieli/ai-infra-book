#!/bin/bash

TASKS=${1:-"GSM8K"}
QUANT_METHOD="mxfp"

MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B

python -m mxq.evaluation.inference \
        --model "$MODEL" \
        --dataset "$TASKS" \
        --quant_method $QUANT_METHOD