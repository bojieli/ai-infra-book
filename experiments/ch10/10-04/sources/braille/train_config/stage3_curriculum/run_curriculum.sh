#!/usr/bin/env bash
# Stage 3 (S3) "Tone curriculum": 10 sequential sub-stages on passage-level data,
# tone retention decreasing r100 -> r10, one epoch each.
#
# Renders templates/curriculum.yaml once per tone level and chains each sub-stage
# from the previous sub-stage's checkpoint. The cosine LR schedule restarts at every
# sub-stage because each is a separate llamafactory-cli invocation.
#
# Run from the repository root:
#     bash train_config/stage3_curriculum/run_curriculum.sh <stage2_checkpoint_dir>
#
# <stage2_checkpoint_dir> is the Stage 2 output, either the run directory
# (the latest checkpoint-N inside it is picked) or a specific checkpoint-N.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${PWD}"
TEMPLATE_FILE="${SCRIPT_DIR}/templates/curriculum.yaml"

OUTPUT_BASE_DIR="${OUTPUT_BASE_DIR:-${ROOT_DIR}/saves/Qwen3-8B-Braille/stage3_curriculum}"
DATASET_PREFIX="stage4_passage_train_br2zh_mix"
TONE_LEVELS=(r100 r90 r80 r70 r60 r50 r40 r30 r20 r10)

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <stage2_checkpoint_dir>" >&2
    exit 1
fi
current_checkpoint="$1"

latest_checkpoint() {
    find "$1" -maxdepth 1 -type d -name "checkpoint-*" 2>/dev/null | sort -t'-' -k2 -n | tail -1
}

resolve() {
    local p="$1"
    [[ "$p" =~ checkpoint-[0-9]+$ ]] && { echo "$p"; return; }
    local found; found="$(latest_checkpoint "$p")"
    [[ -n "$found" ]] || { echo "no checkpoint-N found under $p" >&2; exit 1; }
    echo "$found"
}

current_checkpoint="$(resolve "${current_checkpoint}")"
echo "[S3] starting from ${current_checkpoint}"

GENERATED_DIR="$(mktemp -d)"
trap 'rm -rf "${GENERATED_DIR}"' EXIT

for tone in "${TONE_LEVELS[@]}"; do
    yaml="${GENERATED_DIR}/train_${tone}.yaml"
    sed -e "s|{{tone_pct}}|${tone}|g" \
        -e "s|{{dataset_prefix}}|${DATASET_PREFIX}|g" \
        -e "s|{{output_base_dir}}|${OUTPUT_BASE_DIR}|g" \
        -e "s|{{checkpoint_path}}|${current_checkpoint}|g" \
        "${TEMPLATE_FILE}" > "${yaml}"

    if grep -qE '\{\{[a-zA-Z_]+\}\}' "${yaml}"; then
        echo "unsubstituted placeholder in ${yaml}:" >&2
        grep -oE '\{\{[a-zA-Z_]+\}\}' "${yaml}" | sort -u >&2
        exit 1
    fi

    echo "[S3] ${tone}: training from ${current_checkpoint}"
    FORCE_TORCHRUN=1 llamafactory-cli train "${yaml}"

    out="${OUTPUT_BASE_DIR}/${DATASET_PREFIX}_${tone}_train"
    current_checkpoint="$(latest_checkpoint "${out}")"
    [[ -n "${current_checkpoint}" ]] || { echo "[S3] no checkpoint written to ${out}" >&2; exit 1; }
    echo "[S3] ${tone}: done -> ${current_checkpoint}"
done

echo "[S3] curriculum complete. Final checkpoint: ${current_checkpoint}"
echo "[S3] pass this to Stage 4 (train_config/stage4_consolidation/train_passage_10pc.yaml)"
