"""Recount archived FFN timings and Nsight events; never rerun GPU kernels."""
import hashlib
import json
import math
from fractions import Fraction
from statistics import median
from ..paths import PROJECT
from ..sources import model_config, provenance
from ..models import qwen3
from ..units import positive_int


def read_records():
    lock=json.loads((PROJECT/'configs/runtime-traces.lock.json').read_text())
    records={};sources=[]
    for entry in lock['files']:
        path=PROJECT/entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Runtime trace hash mismatch: '+entry['file'])
        if path.suffix=='.json':records[path.name]=json.loads(path.read_text())
        sources.append(dict(file=entry['file'],url='../'+entry['origin'],sha256=entry['sha256']))
    return records,sources


def union_ns(intervals):
    """Measure the union, so concurrent activities are not counted twice."""
    total=0;covered_end=None
    for start,end in sorted(intervals):
        if not isinstance(start,int) or not isinstance(end,int) or end<start:
            raise ValueError('Invalid integer interval')
        total+=max(0,end-max(start,covered_end if covered_end is not None else start))
        covered_end=max(end,covered_end) if covered_end is not None else end
    return total


def calculate(tokens=32):
    positive_int(tokens,'tokens')
    records,local_sources=read_records()
    config=model_config('qwen3-8b');qwen3.validate(config)
    h,f=config['hidden_size'],config['intermediate_size']
    measurements=records['results.json'];method=measurements['method']
    expected=[[h,f],[h,f],[f,h]]
    if method['weight_shapes']!=expected or method['dtype']!='BF16':
        raise ValueError('Experiment dimensions or format differ from pinned Qwen FFN')
    selected=[r for r in measurements['rows'] if r['tokens']==tokens]
    if not selected:raise ValueError('No recorded timing for these tokens')
    timing=[]
    for row in selected:
        if row['correctness']!='passed':raise ValueError('Unvalidated timing row')
        for field in ('samples_us','host_submit_samples_us'):
            values=row[field]
            if len(values)!=method['trials'] or any(not math.isfinite(x) or x<=0 for x in values):
                raise ValueError('Invalid timing samples')
        gpu=median(row['samples_us']);host=median(row['host_submit_samples_us'])
        if gpu!=row['median_us'] or host!=row['host_submit_median_us']:
            raise ValueError('Recorded median disagrees with samples')
        m=row['executed_tokens'];chunks=row['chunks']
        if m<tokens or m%chunks:raise ValueError('Invalid execution partition')
        # Source allocates x/y, g/u/a and optional unfused SiLU output in every chunk.
        live=2*m*(2*h+(3 if row['fused'] else 4)*f)
        if live!=row['live_io_intermediate_bytes']:raise ValueError('Tensor ledger differs from source record')
        payload=2*tokens*h if row['copy_input'] else 0
        if payload!=row['input_copy_payload_bytes']:raise ValueError('Copy payload mismatch')
        timing.append(dict(label=row['label'],executed_tokens=m,chunks=chunks,
                           chunk_tokens=m//chunks,logical_chain_operations=chunks*(4 if row['fused'] else 5),
                           matrix_flops=6*m*h*f,padding_matrix_flops=6*(m-tokens)*h*f,
                           live_io_intermediate_bytes=live,input_copy_payload_bytes=payload,
                           extra_copy_read_write_bytes=2*payload,
                           measured_median_us=gpu,measured_min_us=min(row['samples_us']),measured_max_us=max(row['samples_us']),
                           host_submit_median_us=host,
                           capture_instantiate_first_replay_ms=row['capture_instantiate_first_replay_ms'],
                           pytorch_allocated_graph_delta_bytes=row['pytorch_allocated_graph_delta_bytes']))
    traces=[]
    raw_trace=records['trace-analysis.json']
    if tokens==32:
        for span in raw_trace['ranges']:
            activities=span['kernels']+span['copies']
            for event in activities+span['apis']:
                if not span['start_ns']<=event['start_ns']<=event['end_ns']<=span['end_ns']:
                    raise ValueError('Event outside recorded range')
            intervals=[(x['start_ns'],x['end_ns']) for x in activities]
            active=union_ns(intervals)
            width=max(b for a,b in intervals)-min(a for a,b in intervals)
            launches=[a for a in span['apis'] if 'Launch' in a['name']]
            graph=sum('GraphLaunch' in a['name'] for a in launches)
            if (len(span['kernels']),len(launches),graph)!=(span['kernel_count'],span['launch_api_count'],span['graph_launch_count']):
                raise ValueError('Trace event count mismatch')
            traces.append(dict(label=span['label'],recorded_calls=raw_trace['calls_per_range'],
                               launch_api_count=len(launches),graph_launch_count=graph,kernel_count=len(span['kernels']),
                               copy_payload_bytes=sum(a['bytes'] for a in span['copies']),
                               kernel_duration_sum_ns=sum(a['end_ns']-a['start_ns'] for a in span['kernels']),
                               captured_activity_union_ns=active,device_span_ns=width,
                               uncovered_device_interval_ns=width-active,
                               launch_api_union_ns=union_ns([(a['start_ns'],a['end_ns']) for a in launches])))
    paper=records['paper-case.json']
    ratio=Fraction(str(paper['baseline_vllm_sglang_ms']))/Fraction(str(paper['mpk_ms']))
    return dict(schema_version=1,calculation='recorded-qwen-ffn-runtime',model='qwen3-8b',
                scenario=dict(tokens=tokens),sources=provenance('qwen3-8b')+local_sources,
                runtime_timings=timing,runtime_ranges=traces,environment=measurements['environment'],
                paper_comparison=dict(**paper,reported_latency_ratio_exact=str(ratio),reported_latency_ratio=float(ratio)),
                summary=dict(timing_cases=len(timing),trace_ranges=len(traces),weight_bytes=6*h*f,
                             real_matrix_flops_per_chain=6*tokens*h*f,
                             measured_full_model_seconds=None),
                assumptions=[
                    '记录为RTX PRO 6000 Blackwell上的随机BF16权重单层FFN，形状与官方Qwen配置逐项匹配；不是下载完整权重后的全模型执行。',
                    '无分析器计时从全部11个样本重算中位数和范围，不丢弃长尾；共享GPU、未清L2，CPU提交不含最终同步，CUDA event包含暴露提交间隙，二者不能相加。',
                    'Nsight仅有32-token各三次调用的独立采集，按事件重新计Launch API、GraphLaunch、kernel和copy。设备活动取区间并集，未覆盖区间不证明整卡空闲；分析器时间不替代无分析器计时。',
                    '逻辑链操作数是三个矩阵加独立SiLU/Mul或融合激活；库可能拆成更多kernel。微批在同一卡顺序执行，全部块缓冲同时保留，未增加跨设备流水，不把变慢全部归因于启动。',
                    '张量账含输入／输出和源码显式中间量，不含权重、外部原始输入、验证张量或库工作区。图allocator增量不是完整图内存；准备包含捕获、实例化、首次重放和同步，排除预热JIT。',
                    'MPK仅列作者Qwen3-8B/A100 BF16全模型decode14.5/12.5ms及29/25比值；其输入与环境保留，未在本机运行，也不与RTX局部比值相乘。',
                ])
