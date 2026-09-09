"""Source-level array expressions in the pinned experiment 5-1 C loops.

These counts deliberately do not simulate compiler optimization or CPU cache
misses. Measured samples are imported alongside, not explained away by counts.
"""
import hashlib
import json
import statistics
from ..paths import PROJECT
from ..units import positive_int, ceil_div


def counts(m,k,n,method,tile=32):
    for name,value in [('m',m),('k',k),('n',n),('tile',tile)]: positive_int(value,name)
    if method not in ('ijk','ikj','blocked'): raise ValueError('Unknown loop method')
    work=m*k*n
    a=work if method=='ijk' else m*k if method=='ikj' else m*k*ceil_div(n,tile)
    c_reads=0 if method=='ijk' else work
    c_updates=m*n if method=='ijk' else work
    zeros=0 if method=='ijk' else m*n
    return dict(method=method,tile=tile if method=='blocked' else None,
                a_array_reads=a,b_array_reads=work,c_array_reads=c_reads,
                c_update_writes=c_updates,c_zeroed_elements=zeros,
                source_array_bytes=4*(a+work+c_reads+c_updates+zeros),
                mathematical_flops=2*work,
                b_inner_word_stride=n if method=='ijk' else 1)


def events(m,k,n,method,tile=32):
    """Small-size explicit address witness, used for independent enumeration."""
    counts(m,k,n,method,tile)
    if method=='ijk':
        for i in range(m):
            for j in range(n):
                for z in range(k):
                    yield 'a_array_reads',i*k+z
                    yield 'b_array_reads',z*n+j
                yield 'c_update_writes',i*n+j
        return
    for address in range(m*n): yield 'c_zeroed_elements',address
    spans=[(0,m,0,n,0,k)] if method=='ikj' else [
        (i,min(i+tile,m),j,min(j+tile,n),z,min(z+tile,k))
        for i in range(0,m,tile) for j in range(0,n,tile) for z in range(0,k,tile)]
    for i0,i1,j0,j1,k0,k1 in spans:
        for i in range(i0,i1):
            for z in range(k0,k1):
                yield 'a_array_reads',i*k+z
                for j in range(j0,j1):
                    yield 'b_array_reads',z*n+j
                    yield 'c_array_reads',i*n+j
                    yield 'c_update_writes',i*n+j


def calculate(m: int = 64,k: int = 64,n: int = 64,tiles: list | None = None) -> dict:
    choices=[8,16,32,64,128,256] if tiles is None else tiles
    if not isinstance(choices,list) or not choices: raise ValueError('tiles must be a nonempty list')
    lock=json.loads((PROJECT/'configs/cpu-loops.lock.json').read_text())
    contents={}
    for record in lock:
        data=(PROJECT/record['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']: raise ValueError('CPU loop snapshot changed')
        contents[record['file'].split('/')[-1]]=data
    measured=json.loads(contents['raw.json'])['rows']
    rows=[counts(m,k,n,'ijk'),counts(m,k,n,'ikj')]+[counts(m,k,n,'blocked',t) for t in choices]
    for row in rows:
        matches=[r for r in measured if (r['m'],r['k'],r['n'],r['method'],r['tile'])==
                 (m,k,n,row['method'],row['tile'] or 0)]
        if len(matches)>1: raise ValueError('Ambiguous measured case')
        row['measured_samples_us']=matches[0]['samples_us'] if matches else None
        row['measured_median_us']=statistics.median(matches[0]['samples_us']) if matches else None
    return dict(schema_version=1,calculation='c-loop-source-accesses',model='',
                scenario=dict(m=m,k=k,n=n,tiles=choices),sources=[dict(r,url='../'+r['file']) for r in lock],
                loop_access_rows=rows,
                summary=dict(mathematical_flops=2*m*k*n,distinct_array_bytes=4*(m*k+k*n+m*n),
                             candidates=len(rows),candidates_with_recorded_samples=sum(r['measured_median_us'] is not None for r in rows),
                             measured_cache_misses=None,measured_hbm_bytes=None),
                assumptions=[
                    '循环严格对应实验5-1固定 matmul.c：行主序 FP32、ijk 局部 sum、ikj 的 v=a[i,k]，以及 ii-jj-kk-i-k-j blocked。C 源码与原测量数据保存独立哈希副本，未重新执行基准。',
                    '计数层次是 C 源码数组表达式；sum/v 等局部标量不计数组访问。memset 计零初始化元素与字节，不推断实际 store 指令次数。ijk 直接覆写 C，其他两种先清零再读改写。',
                    '编译器可能寄存器保留、向量化、提升加载或合并写入，源码字节不等于指令流量，更不等于缓存 miss 或 DRAM 字节；相同逐元素 k 顺序也不证明所有编译选项都逐位相同。',
                    'blocked 的 A 每个列块读取一次，含尾块；B 与 C 读改写仍每乘加一次。B 的最内层地址步长为 ijk 的 N 与其他两者的1，边界跳转另算。',
                    '测量值从实验原始9次样本重新取中位数，只在形状／方法／tile完全匹配时附上，未匹配留空。数据来自既有 M2 Max 单CPU线程实验，不作为 Qwen GPU 或普遍硬件性能证据。',
                    '实验计时包括实现内部输出初始化；ijk没有单独清零。不同算法源码数组字节可能更多而运行更快，不能只用本计数解释时间差。',
                ])
