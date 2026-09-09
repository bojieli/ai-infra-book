"""Scalar word requests mapped to banks, with explicit broadcast semantics."""
from ..sources import read_source, provenance
from ..units import positive_int, ceil_div


def service(word_addresses: list, banks: int = 32, ports: int = 1,
            broadcast: bool = False) -> dict:
    positive_int(banks,'banks'); positive_int(ports,'ports')
    if not isinstance(broadcast,bool): raise ValueError('broadcast must be boolean')
    if not isinstance(word_addresses,list) or not word_addresses: raise ValueError('Need nonempty addresses')
    buckets=[[] for _ in range(banks)]
    for lane,address in enumerate(word_addresses):
        positive_int(address,'word address',allow_zero=True)
        buckets[address % banks].append((lane,address))
    rows=[]
    for bank,requests in enumerate(buckets):
        addresses=[address for _,address in requests]
        words=len(set(addresses)) if broadcast else len(addresses)
        rows.append(dict(bank=bank,lanes=[lane for lane,_ in requests],word_addresses=addresses,
                         distinct_words=len(set(addresses)),service_requests=words,rounds=ceil_div(words,ports)))
    return dict(bank_rows=rows,service_rounds=max(r['rounds'] for r in rows),
                lane_requests=len(word_addresses),distinct_words=len(set(word_addresses)),
                serviced_words=sum(r['service_requests'] for r in rows))


def calculate(stride_words: int = 32, access: str = 'column', ports: int = 1,
              broadcast: bool = False) -> dict:
    positive_int(stride_words,'stride_words')
    if stride_words<32: raise ValueError('Stride must hold 32 columns without overlap')
    if access not in ('row','column','same-word'): raise ValueError('Unknown access pattern')
    read_source('sources/hardware/nvidia-async-copies-13-2-1.html')
    addresses=([i for i in range(32)] if access=='row' else [i*stride_words for i in range(32)]
               if access=='column' else [0]*32)
    result=service(addresses,32,ports,broadcast)
    return dict(schema_version=1,calculation='scalar-shared-bank-mapping',model='',
                scenario=dict(stride_words=stride_words,access=access,ports=ports,broadcast=broadcast),
                sources=provenance('bank-mapping'),bank_rows=result['bank_rows'],
                summary=dict(lanes=32,banks=32,word_bytes=4,logical_tile_bytes=4096,
                             allocated_tile_bytes=32*stride_words*4,
                             padding_bytes=32*(stride_words-32)*4,
                             padding_fraction=(stride_words-32)/32,
                             lane_requested_bytes=result['lane_requests']*4,
                             distinct_requested_bytes=result['distinct_words']*4,
                             serviced_word_bytes=result['serviced_words']*4,
                             service_rounds=result['service_rounds'],predicted_kernel_speedup=None),
                assumptions=[
                    '正文 32×32 FP32 暂存块，32 lane 各发一个标量 32-bit 字读取；连续字映射到连续 bank，bank=word_address mod 32。CUDA 13.2.1 官方原件固定在来源中。',
                    '每 bank 每轮默认一个字端口，所有 bank 同时服务，轮数取各 bank 请求数/端口数向上取整的最大值。ports>1 是假设的端口变体，不声明某张 GPU 具备该规格。',
                    'broadcast 默认关闭，逐 lane 计服务；打开后仅将同一字地址的读取合并，不合并同 bank 的不同地址。这是显式服务语义开关，不处理重复地址写入、原子或向量指令。',
                    'row 访问第0行，column 访问第0列，same-word 全部读取地址0。分配量为32整行乘 stride，含最后行尾部 padding；有效32×32数据量不变。',
                    '这是单次请求的端口服务模型，不是内核加速比。标量行 padding 与 TMA 的16-byte分组 swizzle不同；未模拟指令拆分、bank宽度变体、同步、跨warp并发或实际分配粒度。',
                ])
