"""Final teacher features versus full logits: storage, replay IO and head GEMM."""
from fractions import Fraction

from ..sources import model_config, provenance
from ..units import positive_int


SUPPORTED_MODELS = (
    'qwen3-8b', 'qwen3-30b-a3b', 'qwen3-235b-a22b',
    'deepseek-v4-flash', 'deepseek-v4-pro', 'kimi-k3',
)
DTYPE_BYTES = {'bf16': 2, 'fp16': 2, 'fp32': 4}


def calculate(model='qwen3-8b', tokens=8192, dtype='bf16', replays=4,
              chunk_tokens=256, bandwidth_bytes_per_second=10**9,
              head_flops_per_second=10**14):
    """Compare identical token positions and precision with explicitly effective rates."""
    if model not in SUPPORTED_MODELS:
        raise ValueError('Teacher text-head geometry is not audited for this model')
    if dtype not in DTYPE_BYTES:
        raise ValueError('Choose bf16, fp16 or fp32 cache elements')
    for name, value in (
        ('tokens', tokens), ('replays', replays), ('chunk_tokens', chunk_tokens),
        ('bandwidth_bytes_per_second', bandwidth_bytes_per_second),
        ('head_flops_per_second', head_flops_per_second),
    ):
        positive_int(value, name)
    config = model_config(model)
    text_config = config.get('text_config', config)
    hidden = text_config['hidden_size']
    vocabulary = text_config['vocab_size']
    width = DTYPE_BYTES[dtype]
    hidden_bytes = tokens * hidden * width
    logits_bytes = tokens * vocabulary * width
    head_weights = hidden * vocabulary * width
    head_flops = 2 * tokens * hidden * vocabulary
    active_chunk = min(tokens, chunk_tokens)
    # One cache write, then one complete read per replay, through the same interface.
    hidden_io = (1 + replays) * hidden_bytes
    logits_io = (1 + replays) * logits_bytes
    # The producer pays this head GEMM once for logits; hidden pays it on each replay.
    hidden_head_work = replays * head_flops
    logits_head_work = head_flops
    hidden_time = Fraction(hidden_io, bandwidth_bytes_per_second) + Fraction(hidden_head_work, head_flops_per_second)
    logits_time = Fraction(logits_io, bandwidth_bytes_per_second) + Fraction(logits_head_work, head_flops_per_second)
    return dict(
        schema_version=1, calculation='teacher-cache', model=model,
        scenario=dict(model=model, tokens=tokens, dtype=dtype, replays=replays,
                      chunk_tokens=chunk_tokens, bandwidth_bytes_per_second=bandwidth_bytes_per_second,
                      head_flops_per_second=head_flops_per_second),
        sources=provenance(model),
        summary=dict(
            hidden_size=hidden, vocabulary_size=vocabulary,
            hidden_cache_bytes=hidden_bytes, full_logits_cache_bytes=logits_bytes,
            logits_to_hidden_ratio_exact=str(Fraction(vocabulary, hidden)),
            head_weight_bytes=head_weights, one_head_gemm_flops=head_flops,
            hidden_total_cache_io_bytes=hidden_io, logits_total_cache_io_bytes=logits_io,
            hidden_total_head_flops=hidden_head_work, logits_total_head_flops=logits_head_work,
            head_chunk_count=(tokens + chunk_tokens - 1) // chunk_tokens,
            head_tail_tokens=tokens % chunk_tokens or chunk_tokens,
            head_live_tensor_bytes=head_weights + active_chunk * (hidden + vocabulary) * width,
            hidden_serial_budget_exact_seconds=str(hidden_time),
            logits_serial_budget_exact_seconds=str(logits_time),
            hidden_serial_budget_is_lower=hidden_time < logits_time,
            serial_budget_difference_hidden_minus_logits_exact_seconds=str(hidden_time - logits_time),
        ),
        assumptions=[
            '仅保留最终归一化后、输出投影之前的文本hidden [T,H]，不是所有层激活、KV或多模态编码器特征。全logits为[T,V]；二者采用同一声明dtype，shape源自锁定官方config。',
            '教师权重与token身份、位置、mask、tokenizer、模型revision必须固定且另行校验；预算不实现这些校验。改变教师版本必须失效旧cache，不把hidden缓存当可更新教师的前向替代。',
            '两方案共享的教师主干前向不计；hidden在每次replay做一次2THV输出投影，全logits生产时做一次。未计softmax、温度、损失、学生计算、归约、bias和kernel工作区，不证明数值一致或蒸馏质量。',
            'IO为同一接口一次写入加每次replay一次完整读取；假设无跨replay常驻复用。有效带宽与矩阵FLOPs/s均为教学输入，无精度或稀疏性不明的硬件峰值。串行时间是声明阶段相加，不能替代重叠执行实测。',
            'chunk只切token维，head权重常驻；live tensor量仅为一个chunk输入、完整词表输出与head权重之和，不是系统显存峰值。输出被消费即释放，未包括完整cache驻留、学生状态或双缓冲。',
            '保持全词表输出；top-k logits不能无条件替代完整分布。BF16/FP16/FP32仅元素字节预算，不将低精度重投影自动视为逐位重建。',
        ],
    )
