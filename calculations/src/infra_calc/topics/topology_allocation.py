"""Small periodic placement, directed cut capacity and ring reconfiguration cost."""
from fractions import Fraction
from functools import lru_cache
from ..units import positive_int
from .ring_collective import calculate as ring
from .graph_execution import amortization


def pack_windows(free_cells):
    """Enumerate all periodic 2x2 windows on a fixed 4x4 teaching grid."""
    free=set(free_cells)
    if any(not isinstance(x,int) or isinstance(x,bool) or not 0<=x<16 for x in free):
        raise ValueError('Cell IDs must be integers 0..15')
    windows=[]
    for row in range(4):
        for col in range(4):
            cells=sorted({((row+dr)%4)*4+(col+dc)%4 for dr in range(2) for dc in range(2)})
            if set(cells)<=free:windows.append(dict(origin=[row,col],cells=cells,mask=sum(1<<x for x in cells)))
    @lru_cache(None)
    def choose(index,used):
        if index==len(windows):return ()
        best=choose(index+1,used)
        mask=windows[index]['mask']
        if not used&mask:
            candidate=(index,)+choose(index+1,used|mask)
            if len(candidate)>len(best):best=candidate
        return best
    chosen=choose(0,0)
    return dict(free_cells=sorted(free),candidate_windows=windows,
                maximum_simultaneous_allocations=len(chosen),selected_windows=[windows[i] for i in chosen])


def calculate(model='qwen3-8b',tokens=1024,participants=8,startup_ns=5000,
              old_bandwidth_bytes_per_second=25*10**9,new_bandwidth_bytes_per_second=75*10**9,
              extra_setup_ns=100000000,calls=256,flows=4,
              flow_demand_bytes_per_second=25*10**9,cut_capacity_bytes_per_second=50*10**9):
    inputs=locals().copy()
    for name,value in inputs.items():
        if name!='model':positive_int(value,name,allow_zero=name in ('startup_ns','extra_setup_ns'))
    collective=ring(model=model,tokens=tokens,participants=participants,
                    bandwidth_bytes_per_second=old_bandwidth_bytes_per_second,startup_ns=startup_ns)
    c=collective['summary'];sent=c['all_reduce_send_bytes_per_rank']
    startup=c['all_reduce_rounds']*startup_ns
    before=Fraction(startup)+Fraction(sent*10**9,old_bandwidth_bytes_per_second)
    after=Fraction(startup)+Fraction(sent*10**9,new_bandwidth_bytes_per_second)
    saving=before-after
    strip=pack_windows(range(8))
    checker=pack_windows([r*4+c for r in range(4) for c in range(4) if (r+c)%2==0])
    offered=flows*flow_demand_bytes_per_second
    fair=min(Fraction(flow_demand_bytes_per_second),Fraction(cut_capacity_bytes_per_second,flows))
    return dict(schema_version=1,calculation='qwen-topology-allocation',model=model,
                scenario={k:v for k,v in inputs.items() if k!='model'},sources=collective['sources'],
                placement_patterns=dict(strip=strip,checkerboard=checker),
                summary=dict(message_bytes=c['message_bytes_per_rank'],rounds=c['all_reduce_rounds'],
                             per_rank_send_bytes=sent,startup_ns=startup,
                             before_exact_ns=str(before),after_exact_ns=str(after),
                             before_ns=float(before),after_ns=float(after),saving_exact_ns=str(saving),
                             call_speedup=float(before/after) if after else None,
                             before_lifetime_exact_ns=str(calls*before),after_lifetime_exact_ns=str(extra_setup_ns+calls*after),
                             new_path_wins_within_lifetime=extra_setup_ns+calls*after<calls*before,
                             **amortization(extra_setup_ns,saving),
                             strip_simultaneous_jobs=strip['maximum_simultaneous_allocations'],
                             checkerboard_simultaneous_jobs=checker['maximum_simultaneous_allocations'],
                             cut_offered_bytes_per_second=offered,cut_demand_fits=offered<=cut_capacity_bytes_per_second,
                             equal_flow_rate_upper_exact=str(fair),equal_flow_rate_upper_bytes_per_second=float(fair),
                             full_rate_simultaneous_flows=min(flows,cut_capacity_bytes_per_second//flow_demand_bytes_per_second),
                             actual_collective_seconds=None),
                assumptions=[
                    '复用官方Qwen BF16激活和ring逐轮载荷，时长为rounds*alpha+每rank发送字节/有效单向带宽；25/75GB/s、alpha5us及重构100ms是教学输入，不是光开关实测或设备规格。',
                    '两个带宽情景假设所有发送／接收端和物理路径均可支持对应流量；未从设备总端口速率推定切片可用速率。归约算术、HBM供数、其它作业和实际算法选择另核。',
                    '额外准备相对原路径只计一次，按实际调用寿命摊销，启动项不因带宽增大而缩短。每次无正节省且准备为正时无有限回本。',
                    '放置独立采用固定4x4周期位置图，边界可环绕，作业必须占一个相邻2x2窗口。两种图各八个空闲位置，穷举不相交窗口最大集合；不是完整TPU允许配置或物理推荐。',
                    '割集是四条同时经过同一方向容量的流的独立条件模型，均分上限截断于每流需求；反向容量不抵扣正向拥塞。不将空闲位置数量、放置成功和带宽满足混为一谈。',
                    '放置与割集两个小模型未给出从所选窗口到流路径的映射，不能把它们拼成已验证的端到端可行方案；故障重连与训练状态恢复另计。',
                ])
