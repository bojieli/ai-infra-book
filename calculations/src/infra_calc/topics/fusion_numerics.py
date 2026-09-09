"""Exact finite E4M3FN rounding and counterexamples to unsafe fusion claims."""
from fractions import Fraction
import struct
from ..sources import read_source,provenance
from ..units import positive_int


def e4m3fn_positive_values():
    result=[]
    for code in range(127):  # 0x7f is NaN, not a finite number.
        exponent,mantissa=divmod(code,8)
        value=Fraction(mantissa,512) if exponent==0 else Fraction(8+mantissa,8)*Fraction(2)**(exponent-7)
        result.append((code,value))
    return result


VALUES=e4m3fn_positive_values()


def round_e4m3fn(value):
    """Finite input, saturating nearest-even; exact rationals, unsigned zero."""
    value=Fraction(value)
    sign=-1 if value<0 else 1
    _,closest=min(VALUES,key=lambda pair:(abs(pair[1]-abs(value)),pair[0]%2))
    return sign*closest


def quantized_dot(values,weights,block_size,prefix_scale=False):
    positive_int(block_size,'block_size')
    if not values or len(values)!=len(weights): raise ValueError('Need equal nonempty value/weight arrays')
    values=list(map(Fraction,values));weights=list(map(Fraction,weights))
    final_max=max(map(abs,values))
    if not final_max: return Fraction(0)
    if not prefix_scale:
        return sum(round_e4m3fn(x*448/final_max)*w for x,w in zip(values,weights))*final_max/448
    maximum=Fraction(0);accumulator=Fraction(0)
    for start in range(0,len(values),block_size):
        block=values[start:start+block_size]
        new_max=max(maximum,max(map(abs,block)))
        if not new_max: continue
        accumulator*=maximum/new_max
        accumulator+=sum(round_e4m3fn(x*448/new_max)*w for x,w in zip(block,weights[start:start+block_size]))
        maximum=new_max
    return accumulator*maximum/448


def calculate(block_size: int = 128, larger_first: bool = False) -> dict:
    positive_int(block_size,'block_size')
    if not isinstance(larger_first,bool): raise ValueError('larger_first must be boolean')
    read_source('sources/formats/onnx-float8.html')
    small=[1]+[0]*(block_size-1);large=[10]+[0]*(block_size-1)
    weight_small=[1]+[0]*(block_size-1);weight_large=[0]*block_size
    values=(large+small) if larger_first else (small+large)
    weights=(weight_large+weight_small) if larger_first else (weight_small+weight_large)
    full=quantized_dot(values,weights,block_size)
    prefix=quantized_dot(values,weights,block_size,True)
    half=lambda x:struct.unpack('e',struct.pack('e',float(x)))[0]
    # m=sum(x), c=m*sum(y). Partial c loses sum(y) when local m is zero.
    x=[1,-1,1];y=[1,1,1]
    partials=[dict(m=sum(x[a:b]),sum_y=sum(y[a:b]),c=sum(x[a:b])*sum(y[a:b])) for a,b in [(0,2),(2,3)]]
    global_m=sum(x)
    unsafe=sum(Fraction(p['c']*global_m,p['m'] or 1) for p in partials)
    correct=global_m*sum(p['sum_y'] for p in partials)
    return dict(schema_version=1,calculation='fusion-rounding-and-state-counterexamples',model='',
                scenario=dict(block_size=block_size,larger_first=larger_first),sources=provenance('float8-format'),
                quantization_witness=dict(values=values,weights=weights,full_row_output=str(full),prefix_output=str(prefix)),
                lost_state_partials=partials,
                summary=dict(finite_nonnegative_e4m3fn_encodings=len(VALUES),maximum_finite=448,
                             full_row_exact=str(full),prefix_exact=str(prefix),exact_difference=str(prefix-full),
                             full_row_fp16=half(full),prefix_fp16=half(prefix),
                             equal_after_fp16=half(full)==half(prefix),
                             lost_state_full_result=correct,lost_state_unsafe_result=str(unsafe),
                             sufficient_state_result=correct,actual_gpu_kernel_result=None),
                assumptions=[
                    'E4M3FN按官方ONNX位布局枚举非负有限编码，bias=7、3位fraction，subnormal步长2^-9，最大448；转换只接受有限数，饱和最近偶数舍入，零统一为正零。不是E4M3FNUZ或均匀INT8刻度。',
                    '反例两块首项分别1与10，只给1对应权重设1，其他项为0。整行尺度取amax/448；前缀尺度随块更新，已累加量按旧／新amax重新缩放。larger_first同时重排值和权重，不改变原始数学点积。',
                    'FP8舍入用Fraction精确计算，其余算术也用有理数隔离舍入影响；最后另转IEEE FP16。未模拟真实FP32累加、融合指令或GPU执行，不能把此结果称某个kernel实测。',
                    '不可逆因子反例保留各块(m,c)：m为零时c丢失sum(y)，将零分母换成1无法恢复。增加sum(y)状态才可正确合并，不将防除零等同于语义证明。',
                    '本例证明某些输入和分块会不等价，不估计一般误差分布或质量影响；前缀顺序改变结果，也不能由随机宽容差测试推出逐位等价。',
                ])
