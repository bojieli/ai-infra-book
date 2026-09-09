"""Official Wan UMT5-XXL encoder: two padded prompt calls, no text decoder."""
import ast
import hashlib
import json

from ..paths import PROJECT
from ..units import positive_int


def configuration():
    """Read the literal official umt5_xxl factory config without importing torch."""
    lock=json.loads((PROJECT/'configs/video-generation.lock.json').read_text())['sources']
    needed={'wan/modules/t5.py','wan/modules/tokenizers.py','wan/configs/shared_config.py',
            'wan/configs/wan_ti2v_5B.py','wan/textimage2video.py'}
    found={r['upstream_file'] for r in lock if r['upstream_file'] in needed}
    if found!=needed:raise ValueError('Wan encoder requires generator, tokenizer and configuration sources')
    for record in lock:
        if record['upstream_file'] not in needed:continue
        data=(PROJECT/record['file']).read_bytes()
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise ValueError('Wan encoder supporting source hash mismatch')
    record=next(r for r in lock if r['upstream_file']=='wan/modules/t5.py')
    raw=(PROJECT/record['file']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=record['sha256'] or len(raw)!=record['bytes']:
        raise ValueError('Wan UMT5 source hash mismatch')
    tree=ast.parse(raw)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='umt5_xxl')
    assign=next(n for n in function.body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id=='cfg' for t in n.targets))
    if not isinstance(assign.value,ast.Call) or not isinstance(assign.value.func,ast.Name) or assign.value.func.id!='dict':
        raise ValueError('Official UMT5 factory configuration structure changed')
    return {kw.arg:ast.literal_eval(kw.value) for kw in assign.value.keywords}


def calculate(padded_tokens=512,positive_tokens=256,negative_tokens=128,dtype_bytes=2):
    for name,value in locals().copy().items():positive_int(value,name)
    if dtype_bytes not in (2,4):
        raise ValueError('UMT5 supports declared 2-byte or 4-byte floating-point storage only')
    if padded_tokens!=512 or max(positive_tokens,negative_tokens)>padded_tokens:
        raise ValueError('Wan tokenizer pads/truncates to 512; valid prompt rows must be in 1..512')
    c=configuration();p=padded_tokens;h=c['dim'];a=c['dim_attn'];f=c['dim_ffn']
    layers=c['encoder_layers'];heads=c['num_heads'];d=a//heads
    if c['shared_pos'] or a%heads:raise ValueError('Unsupported UMT5 relative-position/head geometry')
    rows=[]
    def matrix(name,m,k,n,copies,weights=True):
        rows.append(dict(operator=name,a_shape=[m,k],b_shape=[k,n],output_shape=[m,n],
            copies=copies,matrix_flops=2*m*k*n*copies,
            matrix_parameters=k*n*copies if weights else 0,
            logical_operand_bytes=(m*k+k*n+m*n)*dtype_bytes*copies))
    matrix('encoder.qkv',p,h,a,3*layers)
    matrix('encoder.out',p,a,h,layers)
    matrix('encoder.ffn_gate_and_up',p,h,f,2*layers)
    matrix('encoder.ffn_down',p,f,h,layers)
    matrix('encoder.qk',p,d,p,heads*layers,False)
    matrix('encoder.pv',p,p,d,heads*layers,False)
    matrix_work=sum(r['matrix_flops'] for r in rows)
    positions=c['num_buckets']*heads*layers
    parameters=sum(r['matrix_parameters'] for r in rows)+c['vocab_size']*h+(2*layers+1)*h+positions
    scores=heads*p*p*layers;norm_rows=(2*layers+1)*p;gelu=p*f*layers
    scalar=dict(rmsnorm_arithmetic=norm_rows*(4*h+1),rsqrt=norm_rows,
        gelu_reference_multiply=6*gelu,gelu_reference_add=2*gelu,tanh=gelu,
        gated_ffn_multiply=gelu,residual_add=2*layers*p*h,
        relative_bias_and_attention_bias_add=2*scores,
        softmax_subtract=scores,softmax_exp=scores,softmax_sum_add=heads*p*(p-1)*layers,
        softmax_divide=scores,softmax_max_compare=heads*p*(p-1)*layers,
        attention_scale_multiply=0,
        relative_bucket_log_calls=p*p*layers)
    branches=[]
    for name,valid in [('positive',positive_tokens),('negative',negative_tokens)]:
        branches.append(dict(branch=name,encoder_evaluations=1,padded_tokens=p,valid_tokens=valid,
            dense_attention_pairs_per_head=p*p,valid_unpadded_pairs_per_head=valid*valid,
            matrix_flops=matrix_work,returned_hidden_shape=[valid,h],
            returned_hidden_bytes=valid*h*dtype_bytes,
            embedding_lookup_bytes=p*h*dtype_bytes,input_index_bytes=p*8,
            relative_embedding_lookup_bytes=heads*p*p*layers*dtype_bytes,
            materialized_one_layer_score_fp32_bytes=heads*p*p*4))
    return dict(status='accounted',configuration=c,encoder_evaluations=2,
        matrix_flops=2*matrix_work,matrix_flops_per_encoder_call=matrix_work,
        learned_encoder_parameters=parameters,declared_weight_bytes=parameters*dtype_bytes,
        output_valid_hidden_bytes=sum(r['returned_hidden_bytes'] for r in branches),
        scalar_reference_counts_per_call=scalar,
        scalar_reference_counts_total={k:2*v for k,v in scalar.items()},
        operators_per_call=rows,branches=branches,
        assumptions=[
            '官方Wan TI2V5B textimage2video.py的无输入图像分支分别调用positive/negative文本encoder各一次；与去噪steps及CFG evaluations分开，不按每去噪步重跑UMT5。',
            '锁定tokenizer明确padding=max_length/truncation/max_length512；输入valid token数量含特殊token且是截断后计数，不执行实际分词。encoder完整512行forward后再截取valid hidden，mask不缩小源码einsum矩阵。',
            '仅UMT5 encoder_only：24层、4096宽、64头、10240 gated-GELU FFN、每层独立relative bias；没有UMT5 decoder或词表logit head。图像/视频生成DiT的text投影和cross-attention仍在原core内，不能重复算。',
            '矩阵均计实际矩形512²；noncausal，T5 attention不做1/sqrt(d)缩放。scalar为声明代数参考，特殊函数分列；relative bucket的全部索引/类型转换与mask决策未穷尽，不称完整kernel指令数。',
            'TI2V5B配置加载models_t5_umt5-xxl-enc-bf16.pth，shared_config指定t5_dtype=torch.bfloat16；dtype_bytes=2对应该路径，4为明确FP32容量敏感性，不声称切换实际checkpoint。dtype_bytes为声明边界存储，softmax/RMSNorm内部FP32及工作区另计；逻辑操作数bytes不是HBM流量。positive/negative共用一份模型参数，不把两次encoder调用变成两份驻留模型。',
        ])
