#!/bin/bash

# NOTE: 
# 1. memory fraction is set to 0.6, 0.9 will cause OOM because of the large amount of meta data through requests
ROLLOUT_MANAGER_ADDR="http://$1:$2"
HOST_ADDR="$(hostname -i)"

python -m rlboost.sglang.launch_server \
    --model-path Qwen/Qwen3-1.7B \
    --host $HOST_ADDR \
    --port 40000 \
    --grammar-backend outlines \
    --tp-size 1 \
    --mem-fraction-static 0.6 \
    --max-running-requests 256 \
    --stream-interval 10 \
    --enable-mixed-chunk \
    --enable-weight-transfer-agent \
    --transfer-agent-handshake-port 20000 \
    --rollout-manager-address "${ROLLOUT_MANAGER_ADDR}"
