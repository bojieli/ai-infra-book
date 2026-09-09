"""Pinned V4 shared-expert FP8 kernel copy coordinates, not lowered PTX counts."""
import json
import re
from ..sources import model_config, read_source, provenance
from ..units import positive_int

def call(name,m,k,n):
    """One contiguous aligned GEMM invocation; offsets are relative to each tensor."""
    for value in (m,k,n):positive_int(value,'GEMM dimension')
    if m%32 or k%128 or n%128:
        raise ValueError('Aligned M32/N128/K128 only; no tail predicate inference')
    mb,nb,kb=m//32,n//128,k//128
    transfers=[];outputs=[]
    for by in range(mb):
        for bx in range(nb):
            for ki in range(kb):
                transfers.append(dict(block=[by,bx],k_iteration=ki,
                    A=dict(origin=[by*32,ki*128],offset_bytes=by*32*k+ki*128,
                           rows=32,row_bytes=128,row_stride_bytes=k),
                    B=dict(origin=[bx*128,ki*128],offset_bytes=bx*128*k+ki*128,
                           rows=128,row_bytes=128,row_stride_bytes=k),
                    scale_B=dict(origin=[bx,ki],offset_bytes=bx*kb+ki,bytes=1),
                    scale_A=dict(first_origin=[by*32,ki],first_offset_bytes=by*32*kb+ki,
                                 rows=32,element_bytes=1,row_stride_bytes=kb)))
            outputs.append(dict(block=[by,bx],origin=[by*32,bx*128],
                                offset_bytes=2*(by*32*n+bx*128),rows=32,
                                row_bytes=256,row_stride_bytes=2*n))
    iterations=mb*nb*kb;blocks=mb*nb
    return dict(name=name,M=m,N=n,K=k,tensor_shapes={'A':[m,k],'B':[n,k],'C':[m,n],
                'scale_A':[m,kb],'scale_B':[nb,kb]},input_dtype='FP8',scale_dtype='E8M0',
                output_dtype='BF16',accumulator_dtype='FP32',
                input_copy_coordinates=transfers,output_copy_coordinates=outputs,
                summary=dict(grid_blocks=blocks,k_iterations_all_blocks=iterations,
                    A_T_copy_calls=iterations,B_T_copy_calls=iterations,
                    accumulator_to_C_shared_T_copy_calls=blocks,C_shared_to_global_T_copy_calls=blocks,
                    scalar_scale_A_reads=iterations*32,scalar_scale_B_reads=iterations,
                    A_copy_payload_bytes=iterations*32*128,B_copy_payload_bytes=iterations*128*128,
                    scale_A_read_bytes=iterations*32,scale_B_read_bytes=iterations,
                    output_global_write_bytes=2*m*n,unique_A_bytes=m*k,unique_B_bytes=n*k,
                    unique_scale_A_bytes=m*kb,unique_scale_B_bytes=nb*kb,
                    valid_matrix_flops=2*m*n*k,
                    lowered_load_store_instructions=None,integer_address_instructions=None,
                    TMA_descriptor_count=None,measured_hbm_bytes=None))


def calculate(rows=32):
    positive_int(rows,'rows')
    if rows%32:raise ValueError('Rows must be divisible by32 for this source coordinate audit')
    c=model_config('deepseek-v4-flash',reference=True)
    source=read_source('sources/deepseek-v4-flash/inference/kernel.py').decode()
    read_source('sources/deepseek-v4-flash/inference/model.py')
    body=source.split('def fp8_gemm_kernel(',1)[1].split('\ndef fp8_gemm(',1)[0]
    for name,value in [('block_M',32),('block_N',128),('block_K',128),('group_size',128)]:
        if not re.search(rf'{name}\s*=\s*{value}\b',body):raise ValueError('Unsupported source tiling')
    if c['dtype']!='fp8' or c.get('scale_dtype','fp8')!='fp8' or c['n_shared_experts']!=1:
        raise ValueError('Pinned single shared FP8 expert/E8M0 configuration required')
    h,f=c['dim'],c['moe_inter_dim']
    calls=[call('shared.w1',rows,h,f),call('shared.w3',rows,h,f),call('shared.w2',rows,f,h)]
    keys=[key for key,value in calls[0]['summary'].items() if type(value) is int]
    totals={key:sum(x['summary'][key] for x in calls) for key in keys}
    return dict(calculation='v4-shared-fp8-copy-coordinates',sources=provenance('deepseek-v4-flash'),
                scenario=dict(rows=rows,layers_accounted=1,world_size=1),calls=calls,totals=totals,
                assumptions=['One actual shared Expert in one layer: w1 and w3 are separate invocations, w2 consumes the gated activation. The two up-projection input reads remain separate.',
                             'Coordinates follow pinned fp8_gemm_kernel source. All dimensions aligned, contiguous FP8 inputs/weights and E8M0 scales; offsets are tensor-relative, not physical pointers.',
                             'Each T.copy uses a strided rectangular region. Payload counts valid elements of those regions, including repeated tiles; not a contiguous span including row gaps.',
                             'Calls are source-level TileLang operations. Compiler expansion, vectorization, CSE, TMA descriptors and integer instruction count are unknown without compiled artifacts.',
                             'num_stages=4 is a source annotation, not proof of four distinct physical input buffers or achieved overlap.',
                             'This subaccount excludes activation quantization, gating, cast internals, inter-layer repetitions and full runtime traffic. FP32 accumulator-to-shared conversion is not counted as an external FP32 write.',
                             'Distinct source argument coordinates can be hoisted or reused by compilation; expression evaluation counts must not be advertised as SASS instruction counts.'])

def markdown(result):
    lines = ["# V4共享专家FP8搬运坐标", "", "单层共享专家三次GEMM；源级T.copy及索引访问不等于PTX/SASS指令数。全部坐标、偏移均相对于各自张量基址。", "",
             "| 调用 | M/N/K | grid块 | A复制调用 | B复制调用 | A载荷 bytes | B载荷 bytes | scale读取 bytes | 输出 bytes |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for call in result['calls']:
        s = call['summary']
        lines.append(f"| {call['name']} | {call['M']}/{call['N']}/{call['K']} | {s['grid_blocks']} | {s['A_T_copy_calls']} | {s['B_T_copy_calls']} | {s['A_copy_payload_bytes']} | {s['B_copy_payload_bytes']} | {s['scale_A_read_bytes']+s['scale_B_read_bytes']} | {s['output_global_write_bytes']} |")
    lines += ["", "N方向分块重复读取A，M方向分块重复读取B；矩形区域每行只读有效字节，不把stride间隙当成传输。TMA descriptor数量、整数地址指令和真实HBM字节仍未知。", "", "## 适用范围", ""]
    lines += ['- ' + item for item in result['assumptions']]
    lines += ["", "## 完整坐标、stride、形状与来源", "", "```json", json.dumps(result,ensure_ascii=False,indent=2), "```", ""]
    return '\n'.join(lines)
