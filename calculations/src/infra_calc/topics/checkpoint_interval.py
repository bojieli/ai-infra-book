"""First-order checkpoint loss and a separately specified Poisson retry model."""
from fractions import Fraction
from math import expm1, sqrt

from ..models import qwen3, qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int


def renewal_seconds(interval, save_cost, rate, recovery):
    """E = integral_0^L P(X>t)dt + P(X<L)*(r+E), L=tau+c.

Failures also interrupt saving, but cannot interrupt the fixed recovery period.
"""
    if rate == 0:
        return float(interval+save_cost)
    exponent = float(rate*(interval+save_cost))
    if exponent > 700:
        raise ValueError('Retry expectation exceeds supported floating-point range')
    return expm1(exponent)*(1/float(rate)+float(recovery))


def calculate(model='qwen3-8b', devices=1024, device_mtbf_seconds=365*86400,
              common_job_mtbf_seconds=None, save_bandwidth_bytes_per_second=8*10**9,
              recovery_ns=120*10**9, intervals_seconds=None, failure_free=False):
    for name,value in (('devices',devices),('device_mtbf_seconds',device_mtbf_seconds),
                       ('save_bandwidth_bytes_per_second',save_bandwidth_bytes_per_second)):
        positive_int(value,name)
    positive_int(recovery_ns,'recovery_ns',allow_zero=True)
    if common_job_mtbf_seconds is not None:
        positive_int(common_job_mtbf_seconds,'common_job_mtbf_seconds')
    if not isinstance(failure_free,bool):
        raise ValueError('failure_free must be boolean')
    config=model_config(model)
    adapter=qwen3_moe if config['model_type']=='qwen3_moe' else qwen3
    parameters=sum(w.parameters for w in adapter.weights(config))
    payload=14*parameters
    save=Fraction(payload,save_bandwidth_bytes_per_second)
    independent=Fraction(devices,device_mtbf_seconds)
    common=Fraction(1,common_job_mtbf_seconds) if common_job_mtbf_seconds else Fraction(0)
    rate=Fraction(0) if failure_free else independent+common
    recovery=Fraction(recovery_ns,10**9)
    candidates=[60,120,300,600,900,1800,3600] if intervals_seconds is None else intervals_seconds
    if not isinstance(candidates,list) or not candidates:
        raise ValueError('Supply nonempty useful-work interval candidates')
    rows=[]
    for interval in candidates:
        positive_int(interval,'interval_seconds')
        c_over_tau=save/interval
        recompute=rate*interval/2
        restart=rate*recovery
        total=c_over_tau+recompute+restart
        elapsed=renewal_seconds(Fraction(interval),save,rate,recovery)
        rows.append(dict(useful_interval_seconds=interval,save_fraction_exact=str(c_over_tau),
                         recompute_fraction_exact=str(recompute),recovery_fraction_exact=str(restart),
                         first_order_loss_exact=str(total),first_order_loss=float(total),
                         first_order_loss_below_one=total<1,
                         poisson_cycle_expected_seconds=elapsed,
                         poisson_retained_useful_fraction=interval/elapsed,
                         poisson_failure_probability_per_attempt=-expm1(-float(rate*(interval+save)))))
    approx_opt=sqrt(float(2*save/rate)) if rate else None
    poisson_opt=None
    if rate:
        # Unique positive root y - 1 + exp(-y-lambda*c)=0, y=lambda*tau in (0,1).
        lo,hi=0.0,1.0
        a=float(rate*save)
        for _ in range(100):
            mid=(lo+hi)/2
            value=mid+expm1(-mid-a)
            if value<0:lo=mid
            else:hi=mid
        poisson_opt=(lo+hi)/2/float(rate)
    best_approx=min(Fraction(row['first_order_loss_exact']) for row in rows)
    best_renewal=max(row['poisson_retained_useful_fraction'] for row in rows)
    return dict(schema_version=1,calculation='checkpoint-interval',model=model,
                scenario=dict(model=model,devices=devices,device_mtbf_seconds=device_mtbf_seconds,
                              common_job_mtbf_seconds=common_job_mtbf_seconds,
                              save_bandwidth_bytes_per_second=save_bandwidth_bytes_per_second,
                              recovery_ns=recovery_ns,intervals_seconds=candidates,failure_free=failure_free),
                sources=provenance(model),checkpoint_interval_rows=rows,
                summary=dict(parameters=parameters,checkpoint_payload_bytes=payload,
                             blocking_save_cost_exact_seconds=str(save),
                             job_failure_rate_exact_per_second=str(rate),
                             job_mtbf_exact_seconds=str(1/rate) if rate else None,
                             first_order_optimal_useful_interval_seconds=approx_opt,
                             poisson_optimal_useful_interval_seconds=poisson_opt,
                             best_enumerated_first_order_intervals=[r['useful_interval_seconds'] for r in rows if Fraction(r['first_order_loss_exact'])==best_approx],
                             best_enumerated_poisson_intervals=[r['useful_interval_seconds'] for r in rows if r['poisson_retained_useful_fraction']==best_renewal]),
                assumptions=[
                    '官方Qwen全参数14byte检查点，以有效全局写入带宽推保存成本c，整个c阻塞训练；这是串行持久化教学假设，不把异步API暂停替换成c，未含CPU状态、metadata和存储放大。',
                    'tau定义为两次保存之间新增有用计算秒，成功一轮墙钟为tau+c。稀少故障的一阶损失c/tau+lambda*tau/2+lambda*r及sqrt(2c/lambda)按此近似使用；损失超过1不裁剪，也不当有效概率。',
                    '单设备独立指数故障率叠加为devices/MTBF；common_job项是独立的作业级共同冲击率，只加一次，不乘设备数。不是时间相关故障或相关硬件失效的实测分布，输入均为教学假设。',
                    '另列Poisson重试模型：计算和保存均可失败；失败即丢弃本轮全部新增工作，固定恢复r期间不会再失败，旧检查点永远可用。E=(exp(lambda*(tau+c))-1)*(1/lambda+r)，保留有用比例tau/E；该模型与一阶近似的假设和分母分别保留。',
                    'Poisson最优用y-1+exp(-y-lambda*c)=0求根，y=lambda*tau；100次二分和expm1为数值求解，不宣称有理数精确。固定不再失败的r只乘E，不改变本模型最优tau。',
                    '零故障时无有限连续最优，null表示应减少保存次数的边界，有限候选仍可比较。未模拟有限训练终点、异步积压、检测延迟、多层检查点、恢复失败或实际训练质量，不能把这些结果作为生产最优周期。',
                ])
