"""Stable mergeable attention states, with an explicit empty-state identity."""
import math
from ..units import positive_int


def block_state(scores, values):
    if len(scores)!=len(values): raise ValueError('Scores and values must have equal lengths')
    if not scores: return None
    width=len(values[0])
    if not width or any(len(v)!=width for v in values): raise ValueError('Value vectors require one positive width')
    if any(not math.isfinite(x) for v in values for x in v): raise ValueError('Values must be finite')
    selected=[]
    for score,value in zip(scores,values):
        if score is None or score == -math.inf: continue
        if not math.isfinite(score): raise ValueError('Scores must be finite or explicitly masked')
        selected.append((score,value))
    if not selected: return None
    maximum=max(score for score,_ in selected)
    weights=[math.exp(score-maximum) for score,_ in selected]
    denominator=math.fsum(weights)
    numerator=tuple(math.fsum(w*v[j] for w,(_,v) in zip(weights,selected)) for j in range(width))
    return maximum,denominator,numerator


def merge(left,right):
    if left is None: return right
    if right is None: return left
    lm,ll,lu=left;rm,rl,ru=right
    if len(lu)!=len(ru): raise ValueError('State widths differ')
    maximum=max(lm,rm)
    a,b=math.exp(lm-maximum),math.exp(rm-maximum)
    return maximum,a*ll+b*rl,tuple(a*x+b*y for x,y in zip(lu,ru))


def finish(state):
    return None if state is None else [v/state[1] for v in state[2]]


def tree_merge(states):
    if not states: return None
    if len(states)==1: return states[0]
    middle=len(states)//2
    return merge(tree_merge(states[:middle]),tree_merge(states[middle:]))


def calculate(scores: list | None = None, values: list | None = None,
              block_sizes: list | None = None) -> dict:
    scores=[0,math.log(2),math.log(4)] if scores is None else scores
    values=[[1],[3],[-2]] if values is None else values
    sizes=[2,1] if block_sizes is None else block_sizes
    if not isinstance(scores,list) or not isinstance(values,list) or not isinstance(sizes,list) or not sizes:
        raise ValueError('Inputs must be lists and block_sizes nonempty')
    for size in sizes:positive_int(size,'block size',allow_zero=True)
    if sum(sizes)!=len(scores): raise ValueError('Block sizes must cover exactly all positions')
    whole=block_state(scores,values)
    states=[];offset=0;sequential=None;rows=[];merges=0
    for index,size in enumerate(sizes):
        state=block_state(scores[offset:offset+size],values[offset:offset+size])
        merges+=int(sequential is not None and state is not None)
        sequential=merge(sequential,state)
        states.append(state)
        rows.append(dict(block=index,start=offset,size=size,valid=state is not None,state=state,
                         standalone_output=finish(state),prefix_output=finish(sequential)))
        offset+=size
    direct=finish(whole);seq=finish(sequential);tree=finish(tree_merge(states))
    outputs=[finish(s) for s in states if s is not None]
    naive=None if not outputs else [math.fsum(v[j] for v in outputs)/len(outputs) for j in range(len(outputs[0]))]
    error=lambda a:None if direct is None else max(abs(x-y) for x,y in zip(a,direct))
    width=0 if whole is None else len(whole[2])
    return dict(schema_version=1,calculation='online-softmax-state-merge',model='',
                scenario=dict(scores=scores,values=values,block_sizes=sizes),sources=[],softmax_blocks=rows,
                summary=dict(direct_output=direct,sequential_output=seq,tree_output=tree,
                             naive_mean_of_block_outputs=naive,sequential_max_abs_error=error(seq),
                             tree_max_abs_error=error(tree),naive_mean_max_abs_error=error(naive),
                             nonempty_blocks=len(outputs),nontrivial_merges=merges,
                             merge_exp_calls=2*merges,merge_subtractions=2*merges,
                             merge_weighted_sum_flops=3*(width+1)*merges,
                             merge_max_comparisons=merges,final_divisions=width,
                             actual_kernel_flops=None),
                assumptions=[
                    '每块保存最大值m、稳定指数和l、未归一化加权向量U。两块先换到共同最大值后分别合并l/U；最终只除一次l，不能将各块最终输出等权平均。',
                    'None或负无穷分数为显式掩码，空块／全掩码块用None状态作合并单位元，避免exp(-inf-(-inf))。全体无有效位置的最终输出留空，不擅自定义成零。',
                    'Python双精度与math.fsum作为小规模数值参照；顺序和树形在实数上等价，浮点检查采用误差容限，不声称任意GPU树或低精度路径逐位相同。',
                    '普通非空合并的最大值比较、两个exp／减法、l/U加权和及最终除法分别计量。空状态直接返回不计普通合并；局部QK/PV、局部softmax、拷贝及实际kernel填充不在合并子账内。',
                    '默认是正文三个分数和标量值的教学例；可通过JSON输入多维值、不同块划分及掩码。状态字节、执行时序与硬件性能需另给格式和后端。',
                ])
