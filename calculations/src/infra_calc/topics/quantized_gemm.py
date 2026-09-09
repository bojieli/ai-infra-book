"""One actual Qwen expert projection under three declared quantization schedules."""
from ..models import qwen3_moe
from ..sources import model_config, provenance
from ..units import positive_int, ceil_div


def calculate(model: str = 'qwen3-235b-a22b', tokens: int = 4096,
              tile_m: int = 128, tile_n: int = 128, tile_k: int = 128) -> dict:
    c=model_config(model);qwen3_moe.validate(c)
    for name,value in [('tokens',tokens),('tile_m',tile_m),('tile_n',tile_n),('tile_k',tile_k)]:
        positive_int(value,name)
    m,k,n=tokens,c['hidden_size'],c['moe_intermediate_size']
    bm,bn,bk=ceil_div(m,tile_m),ceil_div(n,tile_n),ceil_div(k,tile_k)
    a=2*m*k;aq=m*k;w=k*n;y=2*m*n
    rows=[]
    for name,scan,quant_write,activation,scale_write,scale_read,same_scale in [
        ('separate_full_row_quantization',a,aq,aq*bn,4*m,4*m*bn,True),
        ('full_row_scale_fused_cast',a,0,a*bn,4*m,4*m*bn,True),
        ('prefix_scale_fused_cast',0,0,a*bn,0,0,False),
    ]:
        main=scan+quant_write+activation+w*bm+y
        rows.append(dict(name=name,scale_scan_input_bytes=scan,quantized_activation_write_bytes=quant_write,
                         gemm_activation_read_bytes=activation,gemm_weight_read_bytes=w*bm,
                         output_write_bytes=y,main_tensor_interface_bytes=main,
                         scale_write_bytes=scale_write,scale_read_bytes=scale_read,
                         declared_interface_with_scales_bytes=main+scale_write+scale_read,
                         uses_final_full_row_scale=same_scale))
    return dict(schema_version=1,calculation='qwen-expert-quantized-gemm-interface',model=model,
                scenario=dict(tokens=tokens,tile_m=tile_m,tile_n=tile_n,tile_k=tile_k),sources=provenance(model),
                quantization_schedules=rows,shapes=dict(A=[m,k],W_storage=[n,k],Y=[m,n]),
                summary=dict(matrix_flops=2*m*k*n,fully_padded_matrix_flops=2*bm*bn*bk*tile_m*tile_n*tile_k,
                             output_tiles=bm*bn,m_blocks=bm,n_blocks=bn,k_blocks=bk,
                             fp16_activation_bytes=a,fp8_activation_bytes=aq,fp8_weight_bytes=w,fp16_output_bytes=y,
                             retained_fp16_input_per_quantization_row_bytes=2*k,
                             global_fp32_row_scales_bytes=4*m,
                             separate_main_bytes=rows[0]['main_tensor_interface_bytes'],
                             full_scale_fused_main_bytes=rows[1]['main_tensor_interface_bytes'],
                             prefix_scale_fused_main_bytes=rows[2]['main_tensor_interface_bytes'],
                             full_scale_fusion_extra_main_bytes=rows[1]['main_tensor_interface_bytes']-rows[0]['main_tensor_interface_bytes'],
                             actual_peak_working_bytes=None,measured_hbm_bytes=None,predicted_seconds=None),
                assumptions=[
                    '固定官方 Qwen3 MoE 的一个专家一支 gate/up 投影，K=hidden_size、N=moe_intermediate_size；M 是该专家此次收到的教学 token 数，不乘专家数、层数或 top-k，也不是实测路由。',
                    '声明 FP16 激活、FP8 权重／量化激活、FP16 输出与 FP32 累加；这些是格式情景，不由官方 checkpoint dtype 推断实际部署，未选择任何硬件峰值。',
                    '输出 tile 外层、完整 K 归约保留累加器；不同输出 tile 间无 A/W 复用，每个输出列块重读一次 A、每个输出行块重读一次 W。尾部按有效元素读写，完整padding矩阵工作另列。',
                    '独立量化先扫描并保留整行FP16输入至最终尺度可用，再写FP8矩阵，输入只读取一次需要每活动行至少2K字节驻留。这里只给该必要载荷，未声称完整工作区可放。',
                    '最终尺度融合先单独扫描A求全行尺度，随后每个输出tile重读较宽FP16 A并cast。两种全行方案显式存每行一个FP32 scale，按每行每列块读取一次；权重尺度、其它元数据和局部scratch未计，主张量与已声明scale接口分列。',
                    '前缀尺度融合在K块中更新尺度，省去预扫描和全局scale数组；需局部尺度／累加器调整且改变cast舍入语义。它不是全行量化的等价替换，局部算术与数值误差需另外验证。',
                    '接口为所声明加载边界，不特指HBM。减少物化量可能增加宽输入重读；增大tile、改变共享或缓存策略会改变结果，不能由这些字节直接推出时延。',
                ])
