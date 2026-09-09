"""Repeated immutable KV snapshot reads versus one staged local copy."""
from fractions import Fraction
from ..units import positive_int
from .memory_concurrency import calculate as window_calculate
from .graph_execution import amortization


def calculate(model='qwen3-8b',length=1024,reuses=4,active_transactions=313,
              transaction_bytes=256,remote_latency_ns=2000,remote_bandwidth=40*10**9,
              bulk_bandwidth=25*10**9,local_bandwidth=10**12,
              remote_startup_ns=5000,bulk_startup_ns=10000,local_startup_ns=1000,
              available_local_bytes=256*1024**2):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='model':positive_int(value,name,allow_zero=name in ('remote_startup_ns','bulk_startup_ns','local_startup_ns','available_local_bytes'))
    window=window_calculate(model=model,length=length,transactions=active_transactions,
                            transaction_bytes=transaction_bytes,latency_ns=remote_latency_ns,
                            bandwidth_bytes_per_second=remote_bandwidth)
    payload=window['summary']['logical_kv_payload_bytes']
    rate=Fraction(window['summary']['effective_bandwidth_upper_exact_bytes_per_second'])
    remote=remote_startup_ns+max(Fraction(remote_latency_ns),payload*10**9/rate)
    local=local_startup_ns+Fraction(payload*10**9,local_bandwidth)
    # This explicit serialized model adds destination write time to bulk transfer.
    transfer=Fraction(payload*10**9,bulk_bandwidth)
    write=Fraction(payload*10**9,local_bandwidth)
    setup=bulk_startup_ns+transfer+write
    direct_total=reuses*remote
    staged_total=setup+reuses*local
    feasible=payload<=available_local_bytes
    threshold=amortization(setup,remote-local)
    return dict(schema_version=1,calculation='remote-state',scenario=inputs,sources=window['sources'],
                summary=dict(snapshot_payload_bytes=payload,
                             remote_effective_upper_exact_bytes_per_second=str(rate),
                             remote_required_transactions=window['summary']['required_transactions'],
                             remote_per_read_exact_ns=str(remote),local_per_read_exact_ns=str(local),
                             stage_network_exact_ns=str(transfer),stage_local_write_exact_ns=str(write),
                             stage_setup_exact_ns=str(setup),
                             direct_total_exact_ns=str(direct_total),staged_total_exact_ns=str(staged_total),
                             direct_network_bytes=reuses*payload,staged_network_bytes=payload,
                             staged_local_write_bytes=payload,staged_local_read_bytes=reuses*payload,
                             staged_fits_local_capacity=feasible,
                             strict_reuses_to_amortize=threshold['strictly_faster_calls'],
                             selected_policy=('stage' if staged_total<direct_total else 'direct') if feasible else 'direct',
                             selected_total_exact_ns=str(min(direct_total,staged_total) if feasible else direct_total)),
                assumptions=[
                    '官方Qwen BF16 GQA历史快照，完整层KV不切分；reuses次读取同一个不变快照，追加token、位置更新、权重和计算不在本例，不冒充完整自回归decode成本。',
                    '远程每次读取使用已有窗口上界min(B,Nm/T)，服务时间至少max(T,payload/rate)，每次再加显式启动。窗口参数是教学接口假设，延迟与带宽不代表特定硬件。',
                    '搬回路径明确串行计一次bulk启动、网络搬运、目的端写入，然后每次本地读取；真实DMA可能重叠网络与写入，需路径trace才能替换。数值是给定执行组织估计，不是硬件可达性能保证。',
                    'available_local_bytes是扣除其它占用后的可用预算；快照必须整体放得下才允许选择stage。部分缓存、驱逐、分配器对齐、压缩与缓存命中均未模拟。',
                    '网络按发送payload只计一次，不将两端收发相加。本地写和复用读取另列；提前搬回并未消除本地访存。严格回本按额外准备/每次节省计算，容量可行性独立检查。',
                    '只比较给定快照访问，不模拟发布通知、消费者同步、取消回收或源端状态更新。远端地址可用不等于数据已发布，这些依赖另由操作顺序与回收模块计量。',
                ])
