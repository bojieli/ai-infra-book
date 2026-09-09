"""Compare frozen coarse/fine expert work under explicit serial resource costs."""
from pathlib import Path
from fractions import Fraction as F
from math import prod
import json,hashlib
P=Path(__file__).resolve().parents[2]


EXPECTED_INPUTS = {'results/qwen235-granularity-coarse64.json': '050f788294c47e7c56a691b9bd9003b51841a53cfa00dda0a8f9b33f39a887b0', 'results/qwen235-granularity-fine256-k16.json': 'adb3aa0d55db34cd2b0c35164c25f5e6f28c0b8633855ccb23beede48d609141', 'sources/qwen3/modeling_qwen3_moe.py': '3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8', 'configs/models/qwen3-235b-a22b/config.json': '0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4'}

def calculate(coarse_flops_per_second=100_000_000_000_000,fine_flops_per_second=100_000_000_000_000,operand_bytes_per_second=3_000_000_000_000,wire_bytes_per_second=100_000_000_000,capacity_bytes=80_000_000_000,router_flops_per_second=100_000_000_000_000,coarse_remaining_ns=None,fine_remaining_ns=None):
    inputs=locals().copy()
    for key,value in inputs.items():
        if key.endswith('_remaining_ns'):
            if value is not None and (type(value) is not int or value<0):
                raise ValueError(key+' must be a nonnegative integer or null')
        elif type(value) is not int or value<=0:
            raise ValueError(key+' must be a positive integer')
    for name,expected in EXPECTED_INPUTS.items():
        if hashlib.sha256((P/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen input changed: '+name)
    rows=[];bindings=[]
    for name,rate in [('coarse64',coarse_flops_per_second),('fine256-k16',fine_flops_per_second)]:
        path=P/'results'/('qwen235-granularity-'+name+'.json')
        raw=path.read_bytes();r=json.loads(raw)
        bindings.append(dict(file=str(path.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest()))
        rank_rows=[]
        for rank in r['ranks']:
            operand=0;matrix=0
            for expert in rank['expert_matrices']:
                if expert['token_rows']==0:continue
                for projection in ('gate','up','down'):
                    gemm=expert[projection]
                    matrix+=gemm['flops']
                    operand+=2*sum(prod(gemm[field]) for field in ('input','weight','output'))
            if matrix!=rank['expert_matrix_flops']:raise ValueError('Matrix conservation')
            rank_rows.append(dict(rank=rank['rank'],expert_matrix_flops=matrix,expert_gemm_operand_bytes=operand,necessary_capacity_bytes=rank['conditional_resident_bytes']))
        peak=max(x['necessary_capacity_bytes'] for x in rank_rows)
        work=max(x['expert_matrix_flops'] for x in rank_rows)
        operands=max(x['expert_gemm_operand_bytes'] for x in rank_rows)
        wire=sum(x['wire_bytes'] for x in r['messages'])
        geo=r['geometry']; layers=geo['layers']; hidden=geo['hidden']; count=geo['experts']
        tokens=r['scenario']['requests']*r['scenario']['tokens']
        router_work=2*layers*tokens*hidden*count
        # Explicit replicated router on every TP/EP rank. BF16 GEMM operands;
        # following FP32 softmax is separately counted below, not a BF16 GEMM.
        router_operands=2*layers*(tokens*hidden+hidden*count+tokens*count)
        replicas=len(r['ranks'])
        if router_work*replicas!=r['summary']['router_matrix_flops_if_executed_on_all_tp_ep_replicas']:
            raise ValueError('Replicated router conservation')
        router_time=F(router_work,router_flops_per_second)+F(router_operands,operand_bytes_per_second)
        compute=F(work,rate);memory=F(operands,operand_bytes_per_second);network=F(wire,wire_bytes_per_second)
        rows.append(dict(variant=name,ranks=rank_rows,peak_necessary_capacity_bytes=peak,necessary_capacity_fits=peak<=capacity_bytes,max_rank_expert_flops=work,max_rank_operand_bytes=operands,total_wire_bytes=wire,serial_compute_seconds_exact=str(compute),serial_operand_seconds_exact=str(memory),serial_wire_seconds_exact=str(network),conditional_subaccount_seconds_exact=str(compute+memory+network+router_time),router_gemm_flops_per_rank=router_work,router_gemm_operand_bytes_per_rank=router_operands,serial_router_seconds_exact=str(router_time),router_selection_work_per_rank=dict(softmax_scalar_flops=layers*tokens*(3*count-1),exp_ops=layers*tokens*count,max_comparisons=layers*tokens*(count-1),topk_rows=layers*tokens,topk_candidates=layers*tokens*count,renormalize_scalar_flops=layers*tokens*(2*geo['top_k']-1)),router_selection_seconds=None,router_matrix_flops_all_replicas=r['summary']['router_matrix_flops_if_executed_on_all_tp_ep_replicas'],full_runtime_seconds=None,quality=None))
    a,b=rows
    # Fine compute must fit the remaining coarse subaccount time after paying
    # fine operand/network cost. This excludes all explicitly unmodeled work.
    remaining=F(a['conditional_subaccount_seconds_exact'])-F(b['serial_operand_seconds_exact'])-F(b['serial_wire_seconds_exact'])-F(b['serial_router_seconds_exact'])
    threshold=F(b['max_rank_expert_flops'])/remaining if remaining>0 else None
    # Let U_i be all remaining elapsed service in the explicitly serial
    # comparison. Never substitute zero when the caller has not supplied it.
    slack=F(a['conditional_subaccount_seconds_exact'])-F(b['conditional_subaccount_seconds_exact'])
    selected=None
    for row,remaining_ns in zip(rows,(coarse_remaining_ns,fine_remaining_ns)):
        row['declared_remaining_seconds_exact']=str(F(remaining_ns,10**9)) if remaining_ns is not None else None
        row['conditional_extended_seconds_exact']=(
            str(F(row['conditional_subaccount_seconds_exact'])+F(remaining_ns,10**9))
            if remaining_ns is not None else None)
    if coarse_remaining_ns is not None and fine_remaining_ns is not None:
        eligible=[row for row in rows if row['necessary_capacity_fits']]
        if eligible:
            best=min(F(row['conditional_extended_seconds_exact']) for row in eligible)
            selected=[row['variant'] for row in eligible if F(row['conditional_extended_seconds_exact'])==best]
        else:
            selected=[]
    return dict(calculation='granularity-conditional-selection',scenario=inputs,bindings=bindings,variants=rows,
        fine_strictly_faster_rate_threshold_exact=str(threshold) if threshold else None,
        fine_can_win_with_finite_compute_rate=remaining>0,
        same_wire_bytes=a['total_wire_bytes']==b['total_wire_bytes'],
        fine_remaining_minus_coarse_must_be_less_than_seconds_exact=str(slack),
        conditional_capacity_eligible_fastest_variants=selected,
        extended_condition='T_fine < T_coarse iff U_fine - U_coarse < reported slack; equality is a tie. Both require necessary capacity admission.',
        scope=[
            'Fixed 16-token balanced TP2/EP4 cohort and 8192 retained positions; two untrained E/F/top-k alternatives from actual Qwen235 configuration. Full parameters differ because routers differ.',
            'Necessary capacity includes all stored weights, KV and declared workspace. It does not prove executable runtime feasibility.',
            'Expert GEMM operand bytes count each visited matrix call input/weight/output in BF16. These are logical interfaces, not measured HBM; gate/up rereads are explicit.',
            'Service model serially adds max-rank expert compute, max-rank logical operand service and total message wire over one shared fabric server. Effective rates are declared inputs, not official peaks or observed execution.',
            'Router GEMM is replicated on every TP/EP rank under an explicit policy, with BF16 interface bytes and a separately supplied effective rate. FP32 softmax/top-k/renormalization work is retained but its runtime is unknown. Attention/shared framework operations, nonlinearities, launch costs, queueing, real caches and topology remain outside this conditional subaccount. This is not a full-request ranking.',
            'Equal wire demand cannot create a bandwidth-driven ordering reversal at common wire rate. A different result requires changed routing/placement or an explicitly different service model.',
            'U_i is a caller-declared elapsed remainder under this serial service model, including unmodeled selection/nonlinearities and any other included stage costs. It is not measured here. Supplying only one remainder never enables a complete conditional choice; explicit zero is allowed but never inferred.',
            'No quality-equivalence assertion; conditional speed comparison only applies to the named partial resource account.'
        ])

def markdown(result):
    """Display necessary capacity, accounted cost and the unknown-cost boundary."""
    lines=["# 专家颗粒度：容量与服务条件", "",
        "固定16token、TP2/EP4和8192位置，对比未训练的64/3072/k4与256/768/k16变体。有效服务率由输入声明，不是官方峰值或实测。", "",
        "| 变体 | 必要容量 bytes | 已计串行成本 ms | 给定剩余成本 ms | 容量通过 |",
        "|---|---:|---:|---:|---|"]
    for row in result['variants']:
        rest=row['declared_remaining_seconds_exact']
        rest_text=f"{float(F(rest))*1000:.6f}" if rest is not None else "未知"
        lines.append(f"| {row['variant']} | {row['peak_necessary_capacity_bytes']:,} | {float(F(row['conditional_subaccount_seconds_exact']))*1000:.6f} | {rest_text} | {row['necessary_capacity_fits']} |")
    slack=result['fine_remaining_minus_coarse_must_be_less_than_seconds_exact']
    lines += ["", "令 U 为尚未计入的串行阶段耗时，细粒度严格更快的条件是：", "",
        f"`U_fine - U_coarse < {slack} 秒`（约 {float(F(slack))*1e6:.6f} 微秒）。等号表示并列。", "",
        "共同wire字节相同，共同fabric带宽不能改变两者的差值。逻辑GEMM操作数服务与物理HBM不同；U需要覆盖所选比较中的其余差异工作，不能自动当零。必要容量通过不证明运行时可部署，给定剩余耗时也不证明模型质量相同。", "",
        f"满足必要容量条件后的条件最快方案：{result['conditional_capacity_eligible_fastest_variants']}（null表示剩余输入不足；空列表表示两者均未通过容量条件）。", "",
        "## 完整输入与计算明细", "", "```json",json.dumps(result,indent=2),"```",""]
    return "\n".join(lines)

if __name__=='__main__':
    print(json.dumps(calculate(),indent=2))
