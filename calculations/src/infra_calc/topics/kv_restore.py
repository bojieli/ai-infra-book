"""Known next-use window: keep KV, host offload/prefetch, or backbone replay."""
from fractions import Fraction
from ..models import forward
from ..schema import Scenario
from ..units import positive_int


def calculate(model='qwen3-8b',tokens=1024,next_use_ns=20000000,
              offload_bandwidth=25*10**9,restore_bandwidth=25*10**9,
              transfer_startup_ns=10000,recompute_ns=50000000,
              host_capacity_bytes=256*1024**2):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='model':positive_int(value,name,allow_zero=name in ('next_use_ns','transfer_startup_ns','host_capacity_bytes'))
    work=forward(model,Scenario(tokens=tokens,output_head='none'))
    payload=work['summary']['kv_resident_after_bytes']
    offload=transfer_startup_ns+Fraction(payload*10**9,offload_bandwidth)
    restore=transfer_startup_ns+Fraction(payload*10**9,restore_bandwidth)
    # Offload begins now; destination allocation reserves the whole snapshot.
    restore_start=max(offload,Fraction(next_use_ns)-restore)
    restored=restore_start+restore
    rebuild_start=max(0,next_use_ns-recompute_ns)
    rebuilt=rebuild_start+recompute_ns
    host_fits=payload<=host_capacity_bytes
    rows=[dict(policy='keep',feasible=True,ready_exact_ns=str(next_use_ns),stall_exact_ns='0',
               kv_free_interval_exact_ns='0',released_byte_ns_exact='0',transfer_bytes=0,replayed_matrix_flops=0),
          dict(policy='offload_prefetch',feasible=host_fits,ready_exact_ns=str(restored),
               stall_exact_ns=str(max(Fraction(0),restored-next_use_ns)),
               kv_free_interval_exact_ns=str(restore_start-offload),
               released_byte_ns_exact=str(payload*(restore_start-offload)),
               transfer_bytes=2*payload,replayed_matrix_flops=0),
          dict(policy='drop_recompute',feasible=True,ready_exact_ns=str(rebuilt),
               stall_exact_ns=str(max(0,rebuilt-next_use_ns)),kv_free_interval_exact_ns=str(rebuild_start),
               released_byte_ns_exact=str(payload*rebuild_start),transfer_bytes=0,
               replayed_matrix_flops=work['summary']['matrix_flops'])]
    return dict(schema_version=1,calculation='kv-restore',scenario=inputs,sources=work['sources'],
                restore_policies=rows,
                summary=dict(kv_snapshot_bytes=payload,input_token_id_bytes=tokens*4,
                             replay_backbone_matrix_flops=work['summary']['matrix_flops'],
                             replay_backbone_scalar_flops=work['summary']['scalar_flops'],
                             replay_special_ops=work['summary']['special_ops'],
                             replay_new_kv_write_bytes=work['summary']['kv_new_write_bytes'],
                             offload_exact_ns=str(offload),restore_exact_ns=str(restore),
                             prefetch_start_exact_ns=str(restore_start),
                             offload_return_stall_exact_ns=rows[1]['stall_exact_ns'],
                             recompute_start_ns=rebuild_start,recompute_stall_ns=max(0,rebuilt-next_use_ns),
                             host_snapshot_fits=host_fits),
                assumptions=[
                    '原始token ID与固定权重可用，快照是官方模型BF16完整历史。重算使用标准backbone前向、无lm_head；矩阵、标量和特殊运算分列，不声称这是仅生成KV的最小裁剪图。',
                    'recompute_ns是独立给定的教学服务时长，不从峰值FLOPs推断。重算还读权重和中间状态，不能把KV写字节或token数当全部重算成本。',
                    'next_use_ns是已知的未来使用时刻；offload立即开始，完整复制结束后才释放本地KV，再尽可能晚地整块预取；预取启动时预留整个本地快照，两个方向串行且各有启动。',
                    '丢弃立即释放原KV，重算尽可能晚开始；重算一开始就预留完整KV容量。因此释放byte*ns只计释放到重新预留的间隔，不将重算期间当空闲显存。',
                    'offload需要host_capacity容纳完整快照，输入token ID按int32另列；keep与recompute假设执行时本地容量可用。未计其它工作对容量和带宽的争用、pinned分配、权重装载或发布同步。',
                    '三策略展示恢复等待与释放容量时间的权衡，不自动按最短延迟选keep；保留KV可能挤占别的请求，这需要服务队列与容量收益联合评估。next_use未知、预取预测错误和淘汰策略不在本例。',
                ])
