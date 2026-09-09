"""Qwen3.6-35B-A3B identity bound to the shared Qwen3.5-MoE implementation.

The model release keeps the qwen3_5_moe architecture name. The calculation
shares formulas, while configurations, checkpoint headers and provenance are
bound to the separate Qwen3.6 release.
"""
from . import qwen35_forward

MODEL = 'qwen3.6-35b-a3b'
EVIDENCE_ROOT = 'sources/qwen3.6-35b-a3b'
MASK_SOURCE = EVIDENCE_ROOT + '/transformers/src/transformers/masking_utils.py'


def calculate(batch=1, tokens=8192, history=0, output_head='all',
              routing_counts=None, chunk_size=64, record_past=False):
    result = qwen35_forward.calculate(
        batch=batch, tokens=tokens, history=history, output_head=output_head,
        routing_counts=routing_counts, chunk_size=chunk_size, record_past=record_past,
        model=MODEL, evidence_root=EVIDENCE_ROOT, mask_source=MASK_SOURCE)
    result['calculation'] = 'qwen36-base-text-ledger'
    return result


def markdown(result):
    return qwen35_forward.markdown(result).replace('Qwen3.5', 'Qwen3.6-35B-A3B')
