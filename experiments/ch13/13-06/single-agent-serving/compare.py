#!/usr/bin/env python3
"""Hardware and official API comparison at continuous 24x7 load."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import re
from pathlib import Path
import run

ROOT=Path(__file__).resolve().parent
GPUS={
 'H100-SXM':dict(memory_bytes=80e9,hbm_bytes_s=3.35e12,dense_fp8_flops_s=1.979e15,dense_bf16_flops_s=.9895e15,gpu_usd_hour=3.49,effective_nvlink_bytes_s=225e9,kimi_expert_dtype='bf16'),
 'H200-SXM':dict(memory_bytes=141e9,hbm_bytes_s=4.8e12,dense_fp8_flops_s=1.979e15,dense_bf16_flops_s=.9895e15,gpu_usd_hour=4.59,effective_nvlink_bytes_s=225e9,kimi_expert_dtype='bf16'),
 'B200':dict(memory_bytes=180e9,hbm_bytes_s=8e12,dense_fp8_flops_s=4.5e15,dense_bf16_flops_s=2.25e15,gpu_usd_hour=6.79,effective_nvlink_bytes_s=450e9,kimi_expert_dtype='fp8'),
 'B300':dict(memory_bytes=288e9,hbm_bytes_s=8e12,dense_fp8_flops_s=4.5e15,dense_bf16_flops_s=2.25e15,gpu_usd_hour=7.89,effective_nvlink_bytes_s=450e9,kimi_expert_dtype='fp8'),
}
for name,h in GPUS.items():
 h.update(gpu=name,usable_fraction=.8,effective_inter_node_bytes_s=25e9)
START=datetime(2026,9,9,tzinfo=timezone.utc)
PEAK_HOURS=sum((START+timedelta(hours=i)).weekday()<5 and (START+timedelta(hours=i)).hour in [1,2,3,6,7,8,9] for i in range(720))
PRICES={
 'DeepSeek-V4-Flash':dict(endpoint='deepseek-v4-flash',api_revision='DeepSeek-V4-Flash-0731',
    hit=.007*(1+PEAK_HOURS/720),miss=.22*(1+PEAK_HOURS/720),output=.66*(1+PEAK_HOURS/720)),
 'Kimi-K3':dict(endpoint='kimi-k3',hit=.30,miss=3.,output=15.),
}


def billing(model,history,output_per_turn=4096,tool_ratio=.25,hit_fraction=1.,rebuild=True):
    """Prompt length includes prior output and tool input; hit+miss conserves length."""
    tool=output_per_turn*tool_ratio
    # Conservative prompt-cache contract: previous generated output is new input next call.
    fresh=min(history,output_per_turn+tool)
    rebuild_frequency=min(1.,fresh/(.1*history)) if rebuild else 0.
    hit=(history-fresh)*hit_fraction*(1-rebuild_frequency)
    miss=history-hit
    price=PRICES[model]
    cost=price['output']+(hit*price['hit']+miss*price['miss'])/output_per_turn
    return dict(model=model,context_tokens=history,output_per_turn=output_per_turn,
                tool_input_per_turn=tool,prefix_hit_fraction=hit_fraction,rebuild=rebuild,
                rebuild_frequency=rebuild_frequency,hit_tokens_per_turn=hit,
                miss_tokens_per_turn=miss,effective_prompt_hit_fraction=hit/history,
                api_usd_per_million_output=cost,output_only_usd_per_million=price['output'])


def layouts(model,gpu):
    if model=='DeepSeek-V4-Flash':
        return [(t,1,1,2) for t in [1,2,4,8]]
    choices={'H100-SXM':[(32,1),(32,2)], 'H200-SXM':[(16,1),(32,1),(16,2)],
             'B200':[(8,2),(16,1)], 'B300':[(8,1),(8,2)]}[gpu]
    return [(tp,pp,dcp,kv) for tp,pp in choices for dcp in ([1] if gpu.startswith('H') else [1,tp]) for kv in [2,1]]


def versioned_models():
    models=[run.model(n) for n in PRICES]
    c=json.loads((ROOT/'comparison-sources/v4-0731-config.json').read_text())
    old=run.load('v4-config.json')
    for newer,older in [('num_hidden_layers','n_layers'),('hidden_size','dim'),('n_routed_experts','n_routed_experts'),('num_experts_per_tok','n_activated_experts'),('head_dim','head_dim'),('index_topk','index_topk')]:
        assert c[newer]==old[older]
    assert c['compress_ratios'][:43]==old['compress_ratios'][:43]
    # Reserve the entire current API-version checkpoint as an explicit conservative bound.
    # Extra MTP storage is NOT executed or used to claim a decode speedup.
    models[0]['weight_bytes']=json.loads((ROOT/'comparison-sources/v4-0731-index.json').read_text())['metadata']['total_size']
    return models


def workflow_adjust(x,m,hw,output_per_turn=4096,tool_ratio=.25,rebuild=True):
    b=x['batch'];n=x['context_tokens'];p=run.PROFILES[x['profile']]
    bill=billing(m['name'],n,output_per_turn,tool_ratio,rebuild=rebuild)
    f16=hw['dense_bf16_flops_s']*p['tensor_eff']
    expert=f16 if hw['kimi_expert_dtype']=='bf16' and m['name']=='Kimi-K3' else hw['dense_fp8_flops_s']*p['tensor_eff']
    st=m['state'](n)
    new_token=(m['routed_flops']/expert+(m['other_matrix_flops']+st['attention_flops'])/f16)/x['gpus']
    # Every worker pays their own new-input and full-history rebuild work.
    prefill_per_output=tool_ratio*new_token + bill['rebuild_frequency']*x['rebuild_compute_seconds']/output_per_turn
    r=1/(1/x['decode_tokens_s']+b*prefill_per_output)
    million=run.SECONDS*r/1e6
    unit=x['usd_month_per_worker']/million
    api= million*bill['api_usd_per_million_output']
    gpu_price_break_even=hw['gpu_usd_hour']*bill['api_usd_per_million_output']/unit
    # Critical cached fraction of the WHOLE prompt, not only reusable prefix.
    price=PRICES[m['name']]
    hit_threshold=(price['miss']-(unit-price['output'])*output_per_turn/n)/(price['miss']-price['hit'])
    return dict(**x,gpu=hw['gpu'],workflow_tokens_s=r,workflow_monthly_output_million=million,
                gpu_workflow_usd_per_million=unit,api_same_output_usd_month=api,
                api_usd_per_million_output=bill['api_usd_per_million_output'],
                cheaper='API' if api<x['usd_month_per_worker'] else 'GPU',
                gpu_price_break_even_usd_hour=gpu_price_break_even,
                api_total_prompt_hit_threshold=hit_threshold,
                workload=bill,expert_compute_dtype=hw['kimi_expert_dtype'] if m['name']=='Kimi-K3' else 'fp8')


def main():
    entries=json.loads((ROOT/'comparison-manifest.json').read_text())+json.loads((ROOT/'long-context-manifest.json').read_text())
    for entry in entries:
        assert hashlib.sha256((ROOT/entry['file']).read_bytes()).hexdigest()==entry['sha256']
    # Verify price data is present in frozen first-party HTML, including client-rendered Kimi table.
    ds=(ROOT/'comparison-sources/deepseek-pricing.html').read_text()
    for v in ['$0.007','$0.014','$0.22','$0.44','$0.66','$1.32','Monday through Friday']:assert v in ds
    kimi=(ROOT/'comparison-sources/kimi-pricing.html').read_text()
    for v in ['`0.30`','`3.00`','`15.00`']:assert v in kimi
    assert PEAK_HOURS==154
    rows=[]
    for m in versioned_models():
        for name,hw in GPUS.items():
            for tp,pp,dcp,kv in layouts(m['name'],name):
                for n in [200000,1000000]:
                    for b in [1,2,4,8,16,32,64,128]:
                        for profile in run.PROFILES:
                            mm=dict(m,tp=tp,pp=pp)
                            x=run.estimate(mm,n,b,dcp,profile,hardware=hw,kv_bytes=kv)
                            x['kv_bits']=kv*8
                            rows.append(workflow_adjust(x,mm,hw))
    best=[]
    for name in PRICES:
        for n in [200000,1000000]:
            for gpu in GPUS:
                for profile in run.PROFILES:
                    for target in [20,30]:
                        valid=[x for x in rows if x['model']==name and x['context_tokens']==n and x['gpu']==gpu
                               and x['profile']==profile and x['capacity_feasible'] and x['workflow_tokens_s']>=target]
                        winner=min(valid,key=lambda x:x['gpu_workflow_usd_per_million']) if valid else None
                        best.append(dict(model=name,context_tokens=n,gpu=gpu,profile=profile,target_tokens_s=target,best=winner))
    bill_sweep=[billing(m,n,q,hit_fraction=h,rebuild=rebuild) for m in PRICES for n in [200000,1000000]
                for q in [1024,4096,16384] for h in [0,.9,.99,1] for rebuild in [False,True]]
    result=dict(period_start=START.isoformat(),hours=720,peak_hours=PEAK_HOURS,offpeak_hours=720-PEAK_HOURS,
                prices=PRICES,hardware=GPUS,scenarios=rows,best=best,api_sensitivity=bill_sweep)
    (ROOT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    central=[b for b in best if b['profile']=='central' and b['target_tokens_s']==30]
    overall=[]
    for name in PRICES:
        for n in [200000,1000000]:
            candidates=[b['best'] for b in central if b['model']==name and b['context_tokens']==n and b['best']]
            overall.append(min(candidates,key=lambda x:x['gpu_workflow_usd_per_million']) if candidates else None)
    sections=['# 持续 Agent 负载：GPU 选型与官方 API 比较',
      '2026-09-09。以同一模型档、200K／1M 实际历史、每轮生成 4096 token + 1024 工具输入为主情景。GPU 持续有工作；所有员工自己的 prefill／重建都计入。未实测运行速度，API 持续额度亦作为待满足条件。方法与适用边界见 [COMPARISON.md](COMPARISON.md)。',
      '## 官方 API 单价（美元／百万 token）',
      run.table(['模型','缓存命中输入','未命中输入','输出'],[[m,f"{p['hit']:.6f}",f"{p['miss']:.6f}",f"{p['output']:.6f}"] for m,p in PRICES.items()]),
      f'DeepSeek 按 2026-09-09 00:00 UTC 起的 30 天平均：峰时 {PEAK_HOURS} 小时、谷时 {720-PEAK_HOURS} 小时。Kimi 为固定单价。上述不是仅输出费用；每轮输入历史仍按命中／未命中分别收费。',
      '## 卡型比较：同一工作负载、至少 30 token/s',
      run.table(['模型','历史','GPU','卡数/员工数','TP/PP/DCP','KV位宽','工作流 tok/s','GPU $/M输出'],
        [[b['model'],b['context_tokens'],b['gpu'],f"{x['gpus']}/{x['batch']}",f"{x['tp']}/{x['pp']}/{x['dcp']}",x['kv_bits'],f"{x['workflow_tokens_s']:.1f}",f"{x['gpu_workflow_usd_per_million']:.2f}"] if (x:=b['best']) else [b['model'],b['context_tokens'],b['gpu'],'无达标候选','—','—','—','—'] for b in central]),
      '以每百万输出费用选择候选；不同卡型输出速度不同，不能仅比每人月租。FP8 KV 是显式优化情景，仍需质量和运行时验证。无达标候选表示当前拓扑、效率和 30 token/s 条件不满足，不表示模型不能运行。',
      '## 最低估算单位成本的 GPU 候选 vs 官方 API',
      run.table(['模型','历史','选中 GPU','月输出 M/人','GPU $/人月','API 同输出量 $/月','GPU/API $/M','更便宜'],
        [[x['model'],x['context_tokens'],x['gpu'],f"{x['workflow_monthly_output_million']:.2f}",f"{x['usd_month_per_worker']:.2f}",f"{x['api_same_output_usd_month']:.2f}",f"{x['gpu_workflow_usd_per_million']:.2f} / {x['api_usd_per_million_output']:.2f}",x['cheaper']] for x in overall if x]),
      'API 账单按该 GPU 候选实际估算的月输出量核算，包含完整重复历史收费。API 自身速度不是从价格推出的。GPU 费用仅为预留卡组租金，不含另外采购的控制器、冗余和运维。',
      '## 交叉点',
      run.table(['模型','历史','该GPU租价降至多少 $/卡时可与API持平','API便宜所需整段输入命中比例'],
        [[x['model'],x['context_tokens'],f"{x['gpu_price_break_even_usd_hour']:.3f}",f"{x['api_total_prompt_hit_threshold']:.1%}"] for x in overall if x]),
      '命中阈值 >100% 表示即使全部输入命中，API 仍贵于该 GPU 情景；<0% 表示即使全未命中，API 仍便宜。交叉租价仅改变价格、固定性能及共享人数。',
      '## 调用粒度敏感性：完好前缀命中，周期重建保留',
      run.table(['模型','历史','每轮输出','平均整段输入命中率','API $/M输出'],
        [[x['model'],x['context_tokens'],x['output_per_turn'],f"{x['effective_prompt_hit_fraction']:.1%}",f"{x['api_usd_per_million_output']:.2f}"] for x in bill_sweep if x['prefix_hit_fraction']==1 and x['rebuild']]),
      '工具交互越频繁，同样的长历史越多次计费。完整 JSON 还列 0／90%／99% 前缀命中、无重建理想基线、20 token/s、三档执行效率；不以全池持续繁忙替代缓存命中条件。',
      '## 效率对选卡的影响（30 token/s）',
      run.table(['模型','历史','效率','最低单位成本卡型','GPU $/M'],
        [[m,n,p,x['gpu'],f"{x['gpu_workflow_usd_per_million']:.2f}"] if (x:=min([b['best'] for b in best if b['model']==m and b['context_tokens']==n and b['profile']==p and b['target_tokens_s']==30 and b['best']],key=lambda y:y['gpu_workflow_usd_per_million'],default=None)) else [m,n,p,'无候选','—'] for m in PRICES for n in [200000,1000000] for p in run.PROFILES]),
      f'共 {len(rows)} 个 GPU 情景、{len(bill_sweep)} 个 API 输入情景，见 [comparison.json](comparison.json)。这些是待校准的估算范围，不能证明某卡在所有供应商、后端和负载下最划算。']
    (ROOT/'COMPARISON-RESULTS.md').write_text('\n\n'.join(sections)+'\n')
    print('Wrote',len(rows),'GPU scenarios and',len(bill_sweep),'API scenarios; peak hours',PEAK_HOURS)


if __name__=='__main__':main()
