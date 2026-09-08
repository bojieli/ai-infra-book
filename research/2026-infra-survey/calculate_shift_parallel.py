#!/usr/bin/env python3
"""Qwen3-8B teaching arithmetic; no framework import or hardware prediction."""
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'references/outline-checks/2026-09-07/scaling-history/qwen3-8b-config.json'


def calculate():
    c = json.loads(CONFIG.read_text())
    d, f, q, kv, h, layers = [c[k] for k in ('hidden_size', 'intermediate_size',
        'num_attention_heads', 'num_key_value_heads', 'head_dim', 'num_hidden_layers')]
    byte = 2; sp = tp = 2; devices = sp * tp
    matrices = {'qkv': d*(q+2*kv)*h*byte, 'o': q*h*d*byte, 'ffn': 3*d*f*byte}
    weight = sum(matrices.values())
    # Base SP x TP layout: TP groups [0,1], [2,3], SP groups [0,2], [1,3].
    # The full TP communicator follows SP-major head ordering.
    shift_order = [s*tp+t for t in range(tp) for s in range(sp)]
    ownership = []
    for rank in range(devices):
        s, t = divmod(rank, tp)
        head_begin = t*(kv//tp)+s*(kv//devices)
        base_heads = list(range(head_begin, head_begin+kv//devices))
        shift_slot = shift_order.index(rank)
        shift_heads = list(range(shift_slot*(kv//devices), (shift_slot+1)*(kv//devices)))
        assert base_heads == shift_heads
        ownership.append(dict(rank=rank,base_kv_heads=base_heads,shift_kv_heads=shift_heads,
                              naive_sorted_tp_heads=list(range(rank*(kv//devices),(rank+1)*(kv//devices)))))
    # Communication: per-rank SENT bytes, excluding self, no receive double-counting.
    # One ring all-reduce sends 2*(p-1)/p times its complete input buffer.
    full_tp_tx = Q(2)*Q(2*(devices-1),devices)*d*byte
    base_ar_tx = Q(2)*Q(2*(tp-1),tp)*Q(d*byte,sp)
    base_qkv_tx = Q((q+2*kv)*h*byte,sp*tp)*Q(sp-1,sp)
    base_o_tx = Q(q*h*byte,devices)*Q(sp-1,sp)
    base_tx = base_ar_tx+base_qkv_tx+base_o_tx
    assert all(x.denominator == 1 for x in (full_tp_tx,base_ar_tx,base_qkv_tx,base_o_tx))
    capacity = dict(layer_matrix_bytes=matrices,layer_total_matrix_bytes=weight,
        base_weight_per_gpu_per_layer_bytes=weight//tp,
        shift_weight_per_gpu_per_layer_bytes=weight//devices,
        dual_weight_per_gpu_per_layer_bytes=weight//tp+weight//devices,
        extra_weight_per_gpu_all_layers_bytes=layers*weight//devices,
        base_weight_per_gpu_all_layers_bytes=layers*weight//tp,
        dual_weight_per_gpu_all_layers_bytes=layers*(weight//tp+weight//devices),
        kv_per_gpu_per_cached_token_all_layers_bytes=layers*2*(kv//devices)*h*byte)
    capacity['kv_per_gpu_one_8192_token_sequence_bytes'] = capacity['kv_per_gpu_per_cached_token_all_layers_bytes']*8192
    capacity['extra_weights_in_8192_token_sequence_kv_equivalents'] = float(Q(capacity['extra_weight_per_gpu_all_layers_bytes'],capacity['kv_per_gpu_one_8192_token_sequence_bytes']))
    # This is an intentionally coarse, SERIAL local-matrix + communication budget.
    # The local matrix term uses an ideal max(compute, weights/B). Equal attention
    # work is a separate term, not estimated by this script. Real sharing can differ.
    assumptions = dict(effective_matrix_flops_per_second=500*10**12,
        effective_weight_bytes_per_second=2*10**12,
        effective_collective_sent_bytes_per_second=100*10**9,
        effective_startup_seconds_per_collective=0.000002,
        scope='Teaching assumptions, not card specifications or measurements. No communication/computation overlap; local matrix work uses optimistic Roofline. Attention, KV reads, norms, packing, output gathering, graphs and host work remain separate.')
    def budget(n, mixed):
        padded = ((n+sp-1)//sp)*sp if mixed else n
        flops = Q(2*padded*(weight//byte),devices)
        read = Q(weight,tp if mixed else devices)
        local = max(flops/assumptions['effective_matrix_flops_per_second'],
                    read/assumptions['effective_weight_bytes_per_second'])
        tx = (base_tx if mixed else full_tp_tx)*padded
        communication = Q(4 if mixed else 2)*Q(2,10**6)+tx/assumptions['effective_collective_sent_bytes_per_second']
        final_gather = (Q(2,10**6)+Q(d*byte*padded,sp)/assumptions['effective_collective_sent_bytes_per_second']) if mixed else Q(0)
        return dict(scheduled_tokens=n,padded_tokens=padded,matrix_flops_per_gpu=int(flops),
            matrix_read_bytes_per_gpu=int(read),sent_bytes_per_gpu=int(tx),
            matrix_budget_us=float(local*10**6),communication_budget_us=float(communication*10**6),
            subchain_budget_us=float((local+communication)*10**6),
            all_layers_matrix_communication_budget_us=float((layers*(local+communication)+final_gather)*10**6))
    rows = [dict(n=n,full_tp=budget(n,False),mixed=budget(n,True)) for n in [1,2,8,64,256,303,304,512,2048,8192]]
    first = next(n for n in range(1,8193) if budget(n,True)['subchain_budget_us'] < budget(n,False)['subchain_budget_us'])
    first_model = next(n for n in range(1,8193) if budget(n,True)['all_layers_matrix_communication_budget_us'] < budget(n,False)['all_layers_matrix_communication_budget_us'])
    return dict(scope='Derived teaching case, not Shift Parallelism measurement or verified Qwen3 deployment.',
        config_file=str(CONFIG.relative_to(ROOT)),config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        devices=devices,base_sp=sp,base_tp=tp,shift_tp=devices,bf16_bytes=byte,
        tp_groups=[[0,1],[2,3]],sp_groups=[[0,2],[1,3]],shift_rank_order=shift_order,
        kv_ownership=ownership,capacity=capacity,
        communication=dict(unit='sent bytes per GPU per real token for even N; mixed uses padded N when odd',
            full_tp_two_allreduces=int(full_tp_tx),mixed_two_allreduces=int(base_ar_tx),
            mixed_qkv_alltoall=int(base_qkv_tx),mixed_output_alltoall=int(base_o_tx),mixed_total=int(base_tx),
            final_sp_allgather_sent_bytes_per_gpu_per_token=int(Q(d*byte,sp)),
            exclusions='Per-layer counts omit the once-per-forward SP output all-gather, packing/workspaces, norms and input/output layers. Ring is a teaching choice, not a claim about selected NCCL algorithms.'),
        assumptions=assumptions,rows=rows,first_mixed_win_scheduled_tokens=first,
        first_all_layers_matrix_communication_win_scheduled_tokens=first_model,
        hardware_experiments_run=False)


if __name__ == '__main__':
    result = calculate()
    (Path(__file__).parent/'shift-parallel-arithmetic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'capacity':result['capacity'],'communication':result['communication'],
        'first_mixed_win_scheduled_tokens':result['first_mixed_win_scheduled_tokens'],
        'rows':[{ 'n':r['n'],'full_tp_us':r['full_tp']['subchain_budget_us'],'mixed_us':r['mixed']['subchain_budget_us']} for r in result['rows']]},indent=2))
