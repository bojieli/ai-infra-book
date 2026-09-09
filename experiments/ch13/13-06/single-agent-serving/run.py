#!/usr/bin/env python3
"""Offline resource-based estimates: V4 Flash / Kimi K3, full long contexts.
No API prices, small-model timings, or measured production-speed claims.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = ROOT / 'long-context-sources'
HOURS, SECONDS = 720, 2592000


def load(name):
    return json.loads((S / name).read_text())


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


# All editable performance assumptions are explicit; GPU specification != achieved rate.
PROFILES = {
    'slow': dict(hbm_eff=.35, tensor_eff=.10, layer_overhead_us=250, communication_us=10),
    'central': dict(hbm_eff=.50, tensor_eff=.20, layer_overhead_us=150, communication_us=5),
    'fast': dict(hbm_eff=.65, tensor_eff=.30, layer_overhead_us=75, communication_us=3),
}
HW = dict(gpu='B200', memory_bytes=180_000_000_000, hbm_bytes_s=8e12,
          dense_fp8_flops_s=4.5e15, dense_bf16_flops_s=2.25e15,
          gpu_usd_hour=6.79, usable_fraction=.8, effective_nvlink_bytes_s=450e9,
          effective_inter_node_bytes_s=25e9)


def v4_state(n):
    c = load('v4-config.json')
    resident = read = flops = 0
    prefill_attn = prefill_index = 0
    for r in c['compress_ratios'][:c['n_layers']]:
        z = n//r if r else 0
        chosen = min(z, c['index_topk']) if r == 4 else z
        coff = 2 if r == 4 else 1
        buf = 2*(coff*r)*(coff*c['head_dim'])*4
        if r == 4:
            buf += 2*(coff*r)*(coff*c['index_head_dim'])*4
        resident += (min(n,128)+z)*512*2 + buf
        read += (min(n,128)+chosen)*512*2
        flops += 4*64*512*(min(n,128)+chosen)
        # Conservative full-window / selected-record upper work for the whole prefill.
        prefill_attn += 4*64*512*(n*128 + (n*512 if r==4 else n*n/(2*r) if r else 0))
        if r == 4:
            resident += z*128*2
            read += z*128*2
            flops += 2*64*128*z
            # Reference rectangular index scores; not a sparsity discount on the scan.
            prefill_index += 2*64*128*n*(n//4)
    return dict(resident_bytes=resident, history_read_bytes=read, attention_flops=flops,
                prefill_attention_flops=prefill_attn+prefill_index)


def k3_state(n):
    c = load('k3-config.json')['text_config']; linear = c['linear_attn_config']
    mla, kda = len(linear['full_attn_layers']), len(linear['kda_layers'])
    recurrent = kda*96*128*128*4
    conv = kda*3*96*128*4*2
    history = mla*n*(512+64)*2
    return dict(resident_bytes=history+recurrent+conv, history_read_bytes=history,
                recurrent_bytes=recurrent, convolution_bytes=conv,
                attention_flops=2*mla*96*n*(512+64+512),
                prefill_attention_flops=mla*96*n*(n+1)*(512+64+512))


def model(name):
    d = load('v4-forward.json' if name=='DeepSeek-V4-Flash' else 'k3-forward.json')
    v4 = name=='DeepSeek-V4-Flash'; base_batch=d['scenario']['batch']
    e=d['components']['experts']; g=e['geometry']
    routed_params=sum(m['parameters'] for m in e['matrices'] if m['category']=='routed')
    routed_bytes=routed_params*17//32  # FP4 payload + one-byte group-32 scales.
    weight=d['checkpoint']['byte_groups']['base_total_bytes' if v4 else 'text_total_bytes']
    assert (routed_bytes == e['routed_expert_format']['summary']['resident_weight_and_scale_bytes']) if v4 else (routed_bytes == d['checkpoint']['byte_groups']['text_U8_bytes'])
    attn0=(d['components']['attention']['summary']['effective_qk_pv_matrix_flops']+
           d['components']['attention']['summary']['reference_index_matrix_flops']) if v4 else d['components']['mla']['summary']['valid_attention_matrix_flops']
    total_flops=d['summary']['matrix_flops_effective_attention' if v4 else 'matrix_flops']/base_batch
    routed_flops=e['summary']['routed_matrix_flops']/base_batch
    return dict(name=name, weight_bytes=weight, routed_bytes=routed_bytes,
                nonrouted_bytes=weight-routed_bytes, experts=g['experts'], k=g['top_k'],
                layers=43 if v4 else 93, hidden=g['hidden'], routed_flops=routed_flops,
                other_matrix_flops=total_flops-attn0/base_batch-routed_flops,
                tp=4 if v4 else 8, pp=1 if v4 else 2,
                state=v4_state if v4 else k3_state)


def expected_tiles(b, k, experts, tile=32):
    # Per expert X~Binomial(B,k/E), since each sequence selects k distinct experts.
    p=k/experts
    probs=[math.comb(b,x)*p**x*(1-p)**(b-x) for x in range(b+1)]
    union=experts*(1-probs[0])
    padded=experts*sum(math.ceil(x/tile)*tile*probs[x] for x in range(1,b+1))
    return union,padded


def estimate(m, n, b, dcp, profile):
    st=m['state'](n); tp,pp=m['tp'],m['pp']; cards=tp*pp; p=PROFILES[profile]
    v4=m['name']=='DeepSeek-V4-Flash'
    # TP replicates shared latent KV unless explicitly context-sharded.
    # Five KDA slots/request budget ongoing state plus prefix/reuse bookkeeping.
    if v4:
        state_rank=st['resident_bytes']*b
    else:
        c=load('k3-config.json')['text_config']['linear_attn_config']
        stages=[list(range(1,48)),list(range(48,94))]
        state_rank=max(b*(len(set(ids)&set(c['full_attn_layers']))*n*576*2/dcp +
                          len(set(ids)&set(c['kda_layers']))*(5*96*128*128*4+3*96*128*4*2)/tp)
                       for ids in stages)
    # 5% allowance for layer/embedding imbalance; another 20% card reserve is unavailable.
    weight_rank=m['weight_bytes']/cards*(1.05 if pp>1 else 1)
    peak=weight_rank+state_rank
    union,padded=expected_tiles(b,m['k'],m['experts'])
    routed_read=m['routed_bytes']*union/m['experts']
    padded_flops=m['routed_flops']/m['k']*padded
    bw=HW['hbm_bytes_s']*p['hbm_eff']
    fp8=HW['dense_fp8_flops_s']*p['tensor_eff']
    bf16=HW['dense_bf16_flops_s']*p['tensor_eff']
    # Sum sequential stages: divide latency by TP only, never by TP*PP.
    routed_s=max(routed_read/(tp*bw),padded_flops/(tp*fp8))*1.2
    other_s=max(m['nonrouted_bytes']/(tp*bw),b*m['other_matrix_flops']/(tp*bf16))
    traffic=b*(st['history_read_bytes']/dcp + (0 if v4 else 2*st['recurrent_bytes']/tp))
    attention_s=max(traffic/bw,b*st['attention_flops']/(tp*bf16))
    # Communication startup and payload; no tensor-product multiplication of bandwidth.
    collectives=2*m['layers']+(48 if dcp>1 else 0)
    comm=collectives*(p['communication_us']*1e-6+2*(tp-1)/tp*b*m['hidden']*2/HW['effective_nvlink_bytes_s'])
    if pp>1:
        comm+=20e-6+b*m['hidden']*2/HW['effective_inter_node_bytes_s']
    overhead=m['layers']*p['layer_overhead_us']*1e-6
    step=routed_s+other_s+attention_s+comm+overhead
    # Rebuild retained history after every 10% of the context worth of new output.
    # Full-length rebuild is conservative versus actually rebuilding 90%; compute-only model.
    # Aggregate hardware used for chunked prefill, unlike the serial decode trajectory.
    prefill=(n*m['routed_flops']/(cards*fp8)+
             (n*m['other_matrix_flops']+st['prefill_attention_flops'])/(cards*bf16))
    cycle_output=.1*n
    decode_fraction=cycle_output*step/(cycle_output*step+b*prefill)
    r=1/step; sustained=r*decode_fraction
    cost=HOURS*cards*HW['gpu_usd_hour']/b
    feasible=peak<=HW['memory_bytes']*HW['usable_fraction']
    return dict(model=m['name'],context_tokens=n,batch=b,tp=tp,pp=pp,dcp=dcp,gpus=cards,
                profile=profile,capacity_feasible=feasible,rank_peak_gib=peak/2**30,
                rank_weight_gib=weight_rank/2**30,rank_state_gib=state_rank/2**30,
                context_state_gib_one_copy=st['resident_bytes']/2**30,
                expected_expert_union=union,expected_padded_expert_rows=padded,
                ms=dict(routed=1000*routed_s,other_weights=1000*other_s,attention=1000*attention_s,
                        communication=1000*comm,other_execution=1000*overhead),
                decode_tokens_s=r,decode_only_monthly_output_million=SECONDS*r/1e6,
                rebuild_compute_seconds=prefill,pool_rebuild_compute_seconds=b*prefill,decode_time_fraction=decode_fraction,
                sustained_tokens_s=sustained,monthly_output_million=SECONDS*sustained/1e6,
                usd_month_per_worker=cost,usd_per_million=cost/(SECONDS*sustained/1e6),
                status='analytical scenario, not measured; rejected when capacity_feasible=false')


def main():
    for s in json.loads((ROOT/'long-context-manifest.json').read_text()):
        assert hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest()==s['sha256']
    # Cross-check independent frozen state ledgers at their original 1,048,576-token point.
    for fn,name in [(v4_state,'v4-state-audit.json'),(k3_state,'k3-state-audit.json')]:
        assert fn(1048576)['resident_bytes']*64==load(name)['summary']['resident_bytes']
    models=[model(n) for n in ['DeepSeek-V4-Flash','Kimi-K3']]
    layouts=[dict(models[0],tp=t) for t in [2,4,8]]+[models[1]]
    rows=[estimate(m,n,b,dcp,p) for m in layouts for n in [200000,1000000]
          for b in [1,2,4,8,16,32,64,128] for dcp in ([1] if m['name']=='DeepSeek-V4-Flash' else [1,8]) for p in PROFILES]
    selected=[]
    for name in [m['name'] for m in models]:
        for n in [200000,1000000]:
            for p in PROFILES:
                for target in [20,30]:
                    candidates=[x for x in rows if x['model']==name and x['context_tokens']==n and x['profile']==p
                                and x['capacity_feasible'] and x['decode_tokens_s']>=target]
                    best=min(candidates,key=lambda x:(x['usd_month_per_worker'],-x['sustained_tokens_s'])) if candidates else None
                    selected.append(dict(model=name,context_tokens=n,profile=p,target_tokens_s=target,best=best))
    result=dict(status='completed analytical revision; no measured long-context serving',
                hardware=HW,profiles=PROFILES,models=[{k:v for k,v in m.items() if k!='state'} for m in models],
                scenarios=rows,selected=selected)
    (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    central=[s for s in selected if s['profile']=='central' and s['target_tokens_s']==30]
    report=['# 数字员工：V4 Flash / Kimi K3 的长上下文自建 serving 估算',
      '2026-09-09 修订。200K = 200,000，1M = 1,000,000 个已占用历史 token。每月 720 小时。金额 USD。下面均为资源与效率假设推导，未租卡实测；输入和公式见 [README](README.md)。',
      '## 权重与单员工状态',
      table(['模型','权重及量化元数据 GB','200K 状态 GiB','1M 状态 GiB','GPU 组'],
            [[m['name'],f"{m['weight_bytes']/1e9:.2f}",f"{m['state'](200000)['resident_bytes']/2**30:.2f}",f"{m['state'](1000000)['resident_bytes']/2**30:.2f}",'2/4/8×B200' if m['name']=='DeepSeek-V4-Flash' else '16×B200'] for m in models]),
      '状态列为不复制的一份逻辑状态。V4 的状态在 TP2/4/8 上复制；K3 分开算 TP 复制与 DCP8 分片，容量检查另保留每请求 5 个 KDA 状态槽、逐阶段不均匀及 20% 卡容量余量。K3 仅文本主干；视觉编码服务另计。',
      '## 主情景：至少 30 token/s 的员工',
      '主表遵循持续 decode 基线，以纯 decode 30 token/s 为比较门槛；这是题设情景，不是实测 SLO。周期重建另列敏感性，加入后可能不再满足 30 token/s。只在枚举 batch 和指定拓扑内选择，不声称全局最低成本。',
      table(['模型','占用历史','共享人数','TP/PP/DCP','纯 decode tok/s','重建后 tok/s','纯 decode 月输出 M','每人 $/月','纯 decode $/M'],
            [[s['model'],s['context_tokens'],x['batch'],f"{x['tp']}/{x['pp']}/{x['dcp']}",f"{x['decode_tokens_s']:.1f}",f"{x['sustained_tokens_s']:.1f}",f"{x['decode_only_monthly_output_million']:.1f}",f"{x['usd_month_per_worker']:.2f}",f"{x['usd_month_per_worker']/x['decode_only_monthly_output_million']:.2f}"] if (x:=s['best']) else [s['model'],s['context_tokens'],'无候选','—','—','—','—','—','—'] for s in central]),
      '## 独占一组 GPU：只服务一名员工',
      table(['模型','历史','GPU数','布局 DCP','重建后 tok/s','$/月','$/M 输出'],
            [[x['model'],x['context_tokens'],x['gpus'],x['dcp'],f"{x['sustained_tokens_s']:.1f}",f"{x['usd_month_per_worker']:.2f}",f"{x['usd_per_million']:.2f}"] for x in rows if x['batch']==1 and x['profile']=='central' and x['tp']==(2 if x['model']=='DeepSeek-V4-Flash' else 8) and x['dcp']==(1 if x['model']=='DeepSeek-V4-Flash' else 8)]),
      '## 效率敏感性：纯 decode 30 token/s 门槛',
      table(['模型','历史','效率情景','选中人数','$/人月'],
            [[s['model'],s['context_tokens'],s['profile'],s['best']['batch'] if s['best'] else '无候选',f"{s['best']['usd_month_per_worker']:.2f}" if s['best'] else '—'] for s in selected if s['target_tokens_s']==30]),
      '这不是统计置信区间。slow／central／fast 是尚未校准的 HBM、矩阵效率与每层固定开销组合；价格每变化 10%，相同配置费用也变化 10%。B200 多节点集群需另询价，公开 Pod 价格仅作统一 GPU 租金基准。',
      '## K3：复制缓存与分片缓存的容量差异',
      table(['历史','DCP','主情景容量允许的最大枚举 batch','其中满足30 tok/s的最大 batch'],
            [[n,dcp,max([x['batch'] for x in rows if x['model']=='Kimi-K3' and x['context_tokens']==n and x['dcp']==dcp and x['profile']=='central' and x['capacity_feasible']],default=0),max([x['batch'] for x in rows if x['model']=='Kimi-K3' and x['context_tokens']==n and x['dcp']==dcp and x['profile']=='central' and x['capacity_feasible'] and x['decode_tokens_s']>=30],default=0)] for n in [200000,1000000] for dcp in [1,8]]),
      '## Agent 周期重建',
      table(['模型','历史','一次重建计算时间秒','主情景选中 batch','可用于 decode 的时间占比'],
            [[s['model'],s['context_tokens'],f"{s['best']['rebuild_compute_seconds']:.1f}" if s['best'] else '—',s['best']['batch'] if s['best'] else '—',f"{s['best']['decode_time_fraction']:.1%}" if s['best'] else '—'] for s in central]),
      '持续生成使上下文触及边界。本题保留约 90% 历史，每生成相当于窗口 10% 的 token 后重建；上表按满窗口计算该次 prefill。B 名员工一轮共支付 B 次重建，未把一次重建成本摊成 B 人免费复用。这里只预算重建矩阵工作，摘要模型、工具返回的新输入及其他 prefill 开销尚未计入，所以重建后产出仍有乐观偏差。无重建的理想 decode 另列，不能把省 prefill 当作长上下文 attention 免费。',
      '完整 240 个容量／速度情景（含被容量排除的候选）、逐阶段延迟、20 token/s 门槛、效率输入保存在 [results.json](results.json)。不以 API 售价折算，不用 8B 速度外推，也不把两模型串成一个员工或假设两者完成任务的质量相同。']
    (ROOT/'RESULTS.md').write_text('\n\n'.join(report)+'\n')
    print('Verified source hashes and independent state baselines; wrote',len(rows),'scenarios.')


if __name__=='__main__':
    main()
