"""Recorded batch-average projection times and conditional whole-system costs."""
from fractions import Fraction
import json, hashlib
from ..paths import PROJECT
from ..sources import model_config, provenance
ROOT = PROJECT

def exact(value):
    return dict(numerator=value.numerator,denominator=value.denominator)


def rates(value,name):
    if value is None:return None
    if not isinstance(value,dict) or set(value)!= {'mps','cuda'}:
        raise ValueError(name+' requires both mps and cuda')
    result={}
    for key,number in value.items():
        if type(number) not in (int,str):raise ValueError('Use integer or exact numeric-string rates')
        q=Fraction(number)
        if q<=0:raise ValueError('Rates must be positive')
        result[key]=q
    return result


def calculate(hourly_cost_units=None,whole_system_watts=None):
    costs=rates(hourly_cost_units,'hourly cost');power=rates(whole_system_watts,'whole-system power')
    locked=json.loads((ROOT/'configs/paired-projection-cost.lock.json').read_text())
    for source in locked:
        if hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Archived timing/source input changed: '+source['file'])
    base=ROOT/'sources/paired-projection-cost'
    original_manifest=json.loads((base/'results/projection-manifest.json').read_text())
    for name in ['projection.py','results/projection-mps/results.json','results/projection-cuda/results.json']:
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=original_manifest[name]:
            raise ValueError('Original experiment manifest mismatch')
    raw={device:json.loads((base/f'results/projection-{device}/results.json').read_text(),parse_float=str)
         for device in ('mps','cuda')}
    if raw['mps']['environment']['source_sha256']!=original_manifest['projection.py'] or raw['cuda']['environment']['source_sha256']!=original_manifest['projection.py']:
        raise ValueError('Runner identity differs')
    if raw['mps']['environment']['weight_sha256']!=raw['cuda']['environment']['weight_sha256']:
        raise ValueError('Weight fixture differs')
    config=model_config('qwen3-8b');h=config['hidden_size'];q=config['num_attention_heads']*config['head_dim']
    rows=[]
    for m in (1,256):
        matched={dev:next(row for row in data['rows'] if row['m']==m) for dev,data in raw.items()}
        if matched['mps']['input_sha256']!=matched['cuda']['input_sha256']:raise ValueError('Activation fixture differs')
        if any((x['n'],x['k'])!=(q,h) or x['all_16_weight_buffers_checked'] is not True for x in matched.values()):
            raise ValueError('Projection shape or original buffer checks differ')
        for mode in ('reused','rotating'):
            times={}
            for dev,row in matched.items():
                samples=[Fraction(x) for x in row['paths'][mode]['wall_us']]
                if len(samples)!=11 or any(x<=0 for x in samples):raise ValueError('Expected 11 positive trial batch means')
                times[dev]=sorted(samples)[5]/10**6
            threshold=times['mps']/times['cuda']
            cost={dev:times[dev]*costs[dev]/3600 for dev in times} if costs else None
            energy={dev:times[dev]*power[dev] for dev in times} if power else None
            def winner(values):
                if values is None:return None
                best=min(values.values());return [dev for dev,v in values.items() if v==best]
            rows.append(dict(m=m,n=q,k=h,mode=mode,matrix_flops=2*m*q*h,
                times_seconds_exact={dev:exact(t) for dev,t in times.items()},
                reported_reference_max_abs_error={dev:matched[dev]['max_abs_error'] for dev in times},
                rtx_over_mac_rate_tie_ratio=exact(threshold),
                cost_per_call_proxy={dev:exact(v) for dev,v in cost.items()} if cost else None,
                joules_per_call_proxy={dev:exact(v) for dev,v in energy.items()} if energy else None,
                lower_declared_cost=winner(cost),lower_declared_energy=winner(energy),
                measured_task_energy_joules=None,observed_cost_per_call=None))
    return dict(calculation='paired-projection-conditional-cost',sources=locked,model_sources=provenance('qwen3-8b'),
                scenario=dict(hourly_cost_units=hourly_cost_units,whole_system_watts=whole_system_watts),rows=rows,
                assumptions=['Recorded wall samples are 11 trial averages, each from 16 calls plus submission/synchronization, divided by16. Their median is not median single-call latency or p95.',
                             'MPS and CUDA use matching BF16 input/weight fixtures and Qwen3-8B Q-projection dimensions. Original reference checks are reported, not rerun here; whole-model quality and MPS internal accumulation precision are not established.',
                             'Compare only the same M and reused/rotating mode. Rotation is not proof of cold DRAM. Wall-to-wall comparison includes host/runtime differences; CUDA event time is not substituted for MPS wall time.',
                             'RTX is cheaper in the declared active-time proxy iff its hourly whole-system cost divided by Mac cost is below t_Mac/t_RTX; equality ties. The same algebra holds for declared average whole-system watts.',
                             'Rates and watts are user-declared scenario inputs for the same service window. They are not hardware price, rental quote, TDP, measured energy or total ownership cost.',
                             'No synchronized power trace or cost input exists in the timing source. Unknowns remain null; applying a declared constant power to median time gives a proxy, not measured median energy.',
                             'Fractions preserve arithmetic on recorded decimal values, not physical clock accuracy. Initialization, idle lifecycle, utilization and whole application quality/cost remain outside this task proxy.'])



def markdown(result):
    def fmt(value):
        return '未知' if value is None else f"{float(Fraction(**value)):.9g}"
    lines = ["# 配对投影：时间费用与平均功率条件", "", "墙钟记录为11组每组16调用平均值的中位数，不是单次调用p95。两端使用相同BF16夹具和Qwen8 Q投影形状，数值不是checkpoint权重。", "",
             "| M | 权重模式 | MPS墙钟代理秒 | CUDA墙钟代理秒 | RTX/Mac费用率或平均功率持平比 |",
             "|---:|---|---:|---:|---:|"]
    for row in result['rows']:
        lines.append(f"| {row['m']} | {row['mode']} | {fmt(row['times_seconds_exact']['mps'])} | {fmt(row['times_seconds_exact']['cuda'])} | {fmt(row['rtx_over_mac_rate_tie_ratio'])} |")
    lines += ["", "若同一服务窗口的RTX/Mac整机小时费用率低于持平比，RTX的时间费用代理较低；等号持平。对声明的平均整机功率比同理。这不是实际报价或测得的能耗。", "",
              "| M/模式 | MPS费用代理 | CUDA费用代理 | MPS焦耳代理 | CUDA焦耳代理 |",
              "|---|---:|---:|---:|---:|"]
    for row in result['rows']:
        cost=row['cost_per_call_proxy'];energy=row['joules_per_call_proxy']
        values=[fmt(cost[d] if cost else None) for d in ('mps','cuda')]+[fmt(energy[d] if energy else None) for d in ('mps','cuda')]
        lines.append('| '+str(row['m'])+'/'+row['mode']+' | '+' | '.join(values)+' |')
    lines += ["", "## 适用范围", ""]
    lines += ['- '+text for text in result['assumptions']]
    lines += ["", "## 原始来源与完整计算", "", "```json", json.dumps(result,ensure_ascii=False,indent=2), "```", ""]
    return '\n'.join(lines)
