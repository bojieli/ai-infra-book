"""Sealed inter-request prefix reuse, with explicitly conditional retention."""
from fractions import Fraction
import json
from . import trace_resource_bridge as bridge
from .state import calculate as state
from ..units import positive_int


def calculate(host_bytes_per_second=25_000_000_000,remote_bytes_per_second=5_000_000_000,lookup_ns=10000):
    for name,value in locals().copy().items():
        positive_int(value,name,allow_zero=name=='lookup_ns')
    sources=bridge.evidence()
    prompts=json.loads((bridge.SOURCE_ROOT/'sources/chat/prompts.json').read_text(),parse_float=Fraction)
    original=bridge.calculate('returned_ids_serial_policy')
    unit=state('qwen3-8b',1)['summary']['kv_bytes_per_token_per_request']
    rows=[]
    for previous,current in zip(prompts,prompts[1:]):
        prior_state=previous['input_ids']+previous['response']['output_ids'][:-1]
        inputs=current['input_ids']
        common=0
        while common<min(len(prior_state),len(inputs)) and prior_state[common]==inputs[common]:
            common+=1
        meta=current['response']['meta_info']
        hit=meta['cached_tokens']
        if common!=hit or meta['cached_tokens_details']!={'device':hit,'host':0}:
            raise ValueError('Changed sealed prefix/tier evidence')
        gap=current['start_s']-previous['end_s']
        if gap<0:
            raise ValueError('This contract requires serial application intervals')
        payload=hit*unit
        h2d=Fraction(payload,host_bytes_per_second)
        remote=Fraction(lookup_ns,10**9)+Fraction(payload,remote_bytes_per_second)+h2d
        cold=bridge.logical_call(0,len(inputs))['prefill']['totals']
        warm=original['calls'][current['id']]['resources']['prefill']['totals']
        rows.append(dict(previous_request=previous['id'],request=current['id'],
            longest_common_token_prefix=common,reported_cached_tokens=hit,
            reported_cached_tiers=meta['cached_tokens_details'],
            recorded_application_gap_seconds_exact=str(gap),
            conditional_bf16_prefix_payload_bytes=payload,
            conditional_retain_through_gap_byte_seconds_exact=str(payload*gap),
            conditional_hbm_restore_payload_bytes=0,
            counterfactual_host_restore_seconds_exact=str(h2d),
            counterfactual_remote_via_host_seconds_exact=str(remote),
            minimum_host_bytes_per_second_exact=str(Fraction(payload)/gap) if gap else None,
            remote_gap_after_lookup_and_h2d_seconds_exact=str(gap-Fraction(lookup_ns,10**9)-h2d),
            minimum_remote_bytes_per_second_exact=(
                str(Fraction(payload)/(gap-Fraction(lookup_ns,10**9)-h2d))
                if gap-Fraction(lookup_ns,10**9)-h2d>0 else None),
            host_copy_fits_recorded_gap=h2d<=gap,
            remote_copy_fits_recorded_gap=remote<=gap,
            cold_prefill_totals=cold,warm_prefill_totals=warm,
            observed_page_identity=None,observed_page_lifetime=None,
            observed_restore_bytes=None,actual_restore_seconds=None))
    return dict(calculation='sealed-trace-cache-lifecycle',
        scenario=dict(host_bytes_per_second=host_bytes_per_second,remote_bytes_per_second=remote_bytes_per_second,lookup_ns=lookup_ns),
        trace_sources=sources,kv_bytes_per_token=unit,transitions=rows,
        conditional_prefix_gap_byte_seconds_exact=str(sum(Fraction(r['conditional_retain_through_gap_byte_seconds_exact']) for r in rows)),
        scope=[
            'Three transitions from four original captures. Device/host counters are reported observations; they do not prove physical allocation identity.',
            'Prior candidate state assumes one serial sampled step per returned ID: the final returned EOS has no extra KV append. Matching token prefixes is checked against raw IDs.',
            'Retaining only the reused prefix for the entire completion-to-next-send gap is a declared policy; byte-seconds is not an observed page lifetime or complete request residency.',
            'BF16 full GQA logical state uses official Qwen8 config. No allocator page rounding, metadata, copies or shared ancestor residency inferred.',
            'Host and remote restore are counterfactual alternatives to the reported device hits. Effective rates are caller assumptions. Remote lookup, network and H2D are serial.',
            'Copy fitting within the recorded application gap assumes proactive transfer can start at prior completion; it is not observed overlap or a prediction of TTFT.',
            'Gap fractions preserve the decimal JSON timestamps from one monotonic application clock, not a claim of exact physical clock resolution. Proactive transfer also assumes the next reused prefix is known at prior completion.',
            'Cold and warm logical prefill accounts are retained separately. No full timing, GPU peak or complete HBM claim.'
        ])

def markdown(result):
    lines=["# 同一 Chat 轨迹的缓存保留与取回条件", "",
        "后三次请求报告 device 命中，且原 token IDs 的公共前缀与命中数相符。下面 host/remote 是替代场景，不能当作已发生的迁移。", "",
        "| 转移 | 命中 token | BF16 KV bytes | 应用间隔 ms | host 取回 ms | remote 经 host ms | host 能否放入间隔 |",
        "|---|---:|---:|---:|---:|---:|---|"]
    for r in result["transitions"]:
        gap=float(Fraction(r["recorded_application_gap_seconds_exact"]))*1000
        host=float(Fraction(r["counterfactual_host_restore_seconds_exact"]))*1000
        remote=float(Fraction(r["counterfactual_remote_via_host_seconds_exact"]))*1000
        lines.append(f"| {r['previous_request']} → {r['request']} | {r['reported_cached_tokens']} | {r['conditional_bf16_prefix_payload_bytes']:,} | {gap:.6f} | {host:.6f} | {remote:.6f} | {'是' if r['host_copy_fits_recorded_gap'] else '否'} |")
    lines += ["", "保留策略只覆盖上次应用完成到下次发送之间的复用前缀。其 byte-seconds 不代表完整请求峰值或观测页寿命。取回要求预先知道下一次复用前缀；判断使用精确分数，表格小数仅用于展示。", "",
        "host 门槛为 KV bytes / gap；remote 门槛还需先扣 lookup 和 H2D。剩余时间不为正时，即使远端带宽无限也不能在此串行模型下完成。", "",
        "## 完整明细", "", "```json",json.dumps(result,indent=2),"```",""]
    return "\n".join(lines)

