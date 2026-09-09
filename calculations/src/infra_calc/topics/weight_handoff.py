"""Exact Qwen parameter distribution and declared phase-switch live allocations."""
from fractions import Fraction

from ..models import qwen3, qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int


def calculate(model='qwen3-235b-a22b', expert_parallel=16, replicas=1,
              producer_bytes_per_second=50*10**9, receiver_bytes_per_second=50*10**9,
              training_live_bytes=40*1024**3, kv_bytes=24*1024**3,
              common_bytes=4*1024**3, capacity_bytes=64*1024**3):
    for name, value in (('expert_parallel', expert_parallel), ('replicas', replicas),
                        ('producer_bytes_per_second', producer_bytes_per_second),
                        ('receiver_bytes_per_second', receiver_bytes_per_second)):
        positive_int(value, name)
    for name, value in (('training_live_bytes', training_live_bytes), ('kv_bytes', kv_bytes),
                        ('common_bytes', common_bytes), ('capacity_bytes', capacity_bytes)):
        positive_int(value, name, allow_zero=True)
    config = model_config(model)
    if config['model_type'] not in ('qwen3', 'qwen3_moe'):
        raise ValueError('Full Qwen weight geometry required; no nominal active-parameter substitution')
    adapter = qwen3_moe if config['model_type'] == 'qwen3_moe' else qwen3
    weights = adapter.weights(config)
    expert_weights = [w for w in weights if '.experts.' in w.name]
    total_bytes = 2 * sum(w.parameters for w in weights)
    expert_bytes = 2 * sum(w.parameters for w in expert_weights)
    common_weight_bytes = total_bytes - expert_bytes
    experts = config.get('num_experts', 0)
    if (experts and expert_parallel > experts) or (not experts and expert_parallel != 1):
        raise ValueError('EP ranks must each own at least one expert; Dense requires EP=1')
    # Contiguous quotient/remainder ownership, repeated identically in each MoE layer.
    rank_rows = []
    cursor = 0
    for rank in range(expert_parallel):
        count = experts // expert_parallel + (rank < experts % expert_parallel)
        owned_bytes = expert_bytes // experts * count if experts else 0
        rank_rows.append(dict(rank=rank, expert_start=cursor, expert_stop=cursor + count,
                              expert_count=count, expert_bytes=owned_bytes,
                              required_weight_bytes=owned_bytes + common_weight_bytes))
        cursor += count
    selective_bytes = replicas * sum(r['required_weight_bytes'] for r in rank_rows)
    recipients = replicas * expert_parallel
    full_bytes = recipients * total_bytes
    largest_rank = max(r['required_weight_bytes'] for r in rank_rows)
    transfer_rows = []
    for strategy, sent, received in (
        ('full_to_every_rank', full_bytes, total_bytes),
        ('only_owned_experts_plus_common', selective_bytes, largest_rank),
    ):
        producer_time = Fraction(sent, producer_bytes_per_second)
        receiver_time = Fraction(received, receiver_bytes_per_second)
        transfer_rows.append(dict(strategy=strategy, producer_egress_bytes=sent,
                                  largest_receiver_bytes=received,
                                  producer_bound_exact_seconds=str(producer_time),
                                  receiver_bound_exact_seconds=str(receiver_time),
                                  transfer_bound_exact_seconds=str(max(producer_time, receiver_time))))
    # Selective rollout weights on the largest EP rank; training input includes its own weights.
    phases = [
        ('training', training_live_bytes + common_bytes),
        ('rollout', largest_rank + kv_bytes + common_bytes),
        ('restore_all_before_release', training_live_bytes + largest_rank + kv_bytes + common_bytes),
        ('sync_weights_before_release', training_live_bytes + largest_rank + common_bytes),
    ]
    staged_peak = max(value for name, value in phases if name != 'restore_all_before_release')
    return dict(
        schema_version=1, calculation='weight-handoff', model=model,
        scenario=dict(model=model, expert_parallel=expert_parallel, replicas=replicas,
                      producer_bytes_per_second=producer_bytes_per_second,
                      receiver_bytes_per_second=receiver_bytes_per_second,
                      training_live_bytes=training_live_bytes, kv_bytes=kv_bytes,
                      common_bytes=common_bytes, capacity_bytes=capacity_bytes),
        sources=provenance(model), weight_handoff_ranks=rank_rows,
        weight_handoff_transfers=transfer_rows,
        summary=dict(total_bf16_weight_bytes=total_bytes, expert_bf16_weight_bytes=expert_bytes,
                     nonexpert_bf16_weight_bytes=common_weight_bytes, recipients=recipients,
                     largest_rank_weight_bytes=largest_rank,
                     full_unicast_egress_bytes=full_bytes, selective_unicast_egress_bytes=selective_bytes,
                     egress_ratio_exact=str(Fraction(full_bytes, selective_bytes)),
                     phase_live_bytes=dict(phases), staged_peak_bytes=staged_peak,
                     staged_allocations_fit=staged_peak <= capacity_bytes,
                     restore_all_allocations_fit=dict(phases)['restore_all_before_release'] <= capacity_bytes),
        assumptions=[
            '官方Qwen完整参数BF16载荷；所有routed专家权重计入，不按top-k缩小。EP仅切专家、其余权重每rank完整复制，不含TP/PP；整数专家以连续区间均衡分配，非框架自动布局。',
            '每个replica是独立完整EP组。full基线明确为生产端向每rank发送完整模型的单播，再丢弃不归属专家；selective仅发送所需专家和全部非专家。不是树广播、multicast或共享网络缓存，不能把这个生产端字节比称为所有广播算法的加速比。',
            '生产端有效聚合出口和各接收端有效带宽为教学输入，时间max两界仅必要下界；训练侧重组、源分片all-gather、启动、拥塞、量化、验证和同步屏障未计。',
            'phase按最大权重rank独立核算。training_live_bytes已包括训练自身权重/状态，common_bytes为另外共用分配，rollout权重另占空间；无别名共享。先同步权重、释放全部训练分配、再恢复KV，生产端训练分配在同步完成之前保留。',
            '阶段容量表只对应selective目标布局，不推断full基线接收缓冲峰值；whole模型是否流式接收/丢弃需另给时间线。默认训练40GiB、KV24GiB、common4GiB为显式教学输入，不能从235B配置推断其真实训练容量。',
            '旧KV在权重更新后失效；恢复KV预算指分配空池，未表示旧KV内容可沿用。就绪/版本原子切换、LoRA/MTP与真实引擎交接仍未实现。',
        ],
    )
