#!/bin/bash

TASKS=${1:-"wikitext"}
WBIT=4
WMODE="mxes"
ABIT=4
AMODE="mxem"
GROUP_SIZE=32

MODEL=meta-llama/Meta-Llama-3-8B

python -m mxq.entry \
    --model_path "$MODEL" \
    --tasks "$TASKS" \
    --w_bit "$WBIT" \
    --w_mode "$WMODE" \
    --a_bit "$ABIT" \
    --a_mode "$AMODE" \
    --group_size "$GROUP_SIZE"