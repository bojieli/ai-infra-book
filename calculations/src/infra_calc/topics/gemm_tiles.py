"""Two declared GEMM schedules at a working-buffer/next-level boundary.

No inter-output-tile input retention. Output-stationary keeps its accumulator
across all K tiles; k-outer spills FP32 partial sums between K tiles.
"""
from ..models import qwen3
from ..sources import model_config, provenance
from ..units import positive_int, ceil_div


def account(m: int, k: int, n: int, tile_m: int, tile_k: int, tile_n: int,
            order: str = 'output-stationary', input_buffers: int = 1) -> dict:
    for name,value in locals().copy().items():
        if name != 'order': positive_int(value,name)
    if order not in ('output-stationary','k-outer'):
        raise ValueError('Unsupported accumulator schedule')
    if input_buffers not in (1,2):
        raise ValueError('input_buffers must be 1 or 2')
    bm,bk,bn=ceil_div(m,tile_m),ceil_div(k,tile_k),ceil_div(n,tile_n)
    a=2*m*k*bn
    b=2*k*n*bm
    output=2*m*n
    # Each nonfinal K tile stores FP32; each nonfirst K tile reloads it.
    partial_store=4*m*n*(bk-1) if order=='k-outer' else 0
    partial_load=partial_store
    capacity=input_buffers*(2*tile_m*tile_k+2*tile_k*tile_n)+4*tile_m*tile_n
    traffic=a+b+output+partial_store+partial_load
    return dict(tile_m=tile_m,tile_k=tile_k,tile_n=tile_n,order=order,input_buffers=input_buffers,
                m_blocks=bm,k_blocks=bk,n_blocks=bn,output_tiles=bm*bn,
                valid_matrix_flops=2*m*k*n,
                fully_padded_matrix_flops=2*bm*bk*bn*tile_m*tile_k*tile_n,
                a_read_bytes=a,b_read_bytes=b,output_write_bytes=output,
                partial_store_bytes=partial_store,partial_load_bytes=partial_load,
                next_level_bytes=traffic,reserved_working_bytes=capacity,
                arithmetic_intensity=2*m*k*n/traffic)


def calculate(model: str = 'qwen3-8b', tokens: int = 1024,
              tiles: list | None = None, tile_k: int = 32,
              capacity_bytes: int = 81920, order: str = 'output-stationary',
              input_buffers: int = 1) -> dict:
    c=model_config(model); qwen3.validate(c)
    positive_int(tokens,'tokens'); positive_int(capacity_bytes,'capacity_bytes')
    if tokens>c['max_position_embeddings']: raise ValueError('Tokens exceed official context')
    choices=[32,64,128] if tiles is None else tiles
    if not isinstance(choices,list) or not choices: raise ValueError('tiles must be a nonempty list')
    rows=[]
    for tile in choices:
        r=account(tokens,c['hidden_size'],c['intermediate_size'],tile,tile_k,tile,order,input_buffers)
        r['fits_capacity']=r['reserved_working_bytes']<=capacity_bytes
        rows.append(r)
    feasible=[r for r in rows if r['fits_capacity']]
    best=min(feasible,key=lambda r:r['next_level_bytes']) if feasible else None
    minimum=2*(tokens*c['hidden_size']+c['hidden_size']*c['intermediate_size']+tokens*c['intermediate_size'])
    return dict(schema_version=1,calculation='qwen-up-projection-tiles',model=model,
                scenario=dict(tokens=tokens,tiles=choices,tile_k=tile_k,capacity_bytes=capacity_bytes,
                              order=order,input_buffers=input_buffers),sources=provenance(model),
                gemm_tile_rows=rows,shapes=dict(A=[tokens,c['hidden_size']],W_math=[c['hidden_size'],c['intermediate_size']],
                                              W_storage=[c['intermediate_size'],c['hidden_size']]),
                summary=dict(valid_matrix_flops=2*tokens*c['hidden_size']*c['intermediate_size'],
                             one_read_write_payload_bytes=minimum,
                             feasible_candidates=len(feasible),
                             best_enumerated_tile=None if best is None else [best['tile_m'],best['tile_k'],best['tile_n']],
                             best_enumerated_next_level_bytes=None if best is None else best['next_level_bytes'],
                             measured_hbm_bytes=None,predicted_seconds=None),
                assumptions=[
                    '固定官方 Qwen3 Dense 的单支 up projection，M=输入 token 数、K=hidden、N=intermediate；不包含 gate、SiLU 或 down。BF16 输入／最终输出、FP32 累加，FMA=2。',
                    'output-stationary：外层逐输出块，内层遍历 K；A/B 每次只保留当前块，不跨输出块复用，累加器在整个 K 归约期间保留，输出只写一次，无旧 C。',
                    'k-outer：外层逐 K 块，每个输出块处理后若不是最终 K 块就写 FP32 partial；后续 K 块先读 partial，最终转换 BF16 写出。仍不跨输出块保留 A/B，本例不自动获得额外输入复用。',
                    '下一层字节按实际边界元素计，masked 尾部不读写；fully_padded_matrix_flops 单列若所有块执行完整 tile 的工作，不能把它与有效 FLOPs 混用。活动容量按完整 tile 保留，输入双缓冲只改变声明容量，不凭此减少流量或预测时延。',
                    '接口为工作缓冲与其下一层，不特指 HBM；L2 可能服务重读。累加器与输入缓冲合并仅是抽象容量约束，不声称寄存器和共享内存可任意互换，未计地址、同步、布局和其他工作区。',
                    'best 仅为输入候选集合内、满足容量且下一层流量最小的方案，不是全局 I/O 下界或性能最佳 tile；无可行候选时留空。一读一写载荷也不证明能在有限容量下达到。',
                ])
