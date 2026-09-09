"""Dense full-parameter training matrix work, without inferring kernel execution.

Reuse pinned Qwen shapes, then differentiate each bilinear operation. Loss rows
are bookkeeping; only an explicitly compacted head changes executed GEMM rows.
"""
from ..models import qwen3, qwen3_moe
from ..schema import Scenario
from ..sources import model_config, provenance
from ..units import positive_int


def calculate(model: str = 'qwen3-8b', batch: int = 1, tokens: int = 8192,
              supervised_tokens: int | None = None, head_strategy: str = 'dense',
              gradient_bytes: int = 4, master_weight_bytes: int = 4,
              routing: str = 'balanced') -> dict:
    c = model_config(model)
    adapter = qwen3_moe if c['model_type'] == 'qwen3_moe' else qwen3
    adapter.validate(c)
    if routing not in ('balanced', 'concentrated'):
        raise ValueError('routing must be balanced or concentrated')
    scenario = Scenario(batch=batch, tokens=tokens, output_head='all')
    rows = scenario.rows
    supervised = rows if supervised_tokens is None else supervised_tokens
    positive_int(supervised, 'supervised_tokens')
    if supervised > rows:
        raise ValueError('supervised_tokens cannot exceed batch*tokens')
    if head_strategy not in ('dense', 'compact'):
        raise ValueError('head_strategy must be dense or compact')
    positive_int(gradient_bytes, 'gradient_bytes')
    positive_int(master_weight_bytes, 'master_weight_bytes', allow_zero=True)
    head_rows = rows if head_strategy == 'dense' else supervised
    ledger = []
    hist = None
    mlp = None
    if adapter is qwen3_moe:
        hist = qwen3_moe.routing_counts(rows, c['num_experts'], c['num_experts_per_tok'], routing)
        mlp = qwen3_moe.expert_operators(c, scenario, hist)
    for op in qwen3.build_operators(c, scenario, mlp):
        if not op.matrix_flops:
            continue
        shapes = dict(op.shapes)
        forward = op.matrix_flops
        if op.category == 'linear' and 'input_per_expert' in shapes:
            n, k = shapes['weight_storage_each']
            shapes['gradient_matmuls_per_expert'] = [
                dict(expert=e, d_input=[[m, n], [n, k]], d_weight=[[n, m], [m, k]])
                for e, m in enumerate(hist)]
            gradients = ['d_expert_input', 'd_expert_weight']
        elif op.category == 'linear':
            m, k = shapes['input']
            n = shapes['output'][1]
            if op.name == 'lm_head':
                m = head_rows
            shapes = dict(input=[m, k], weight_storage=[n, k], output=[m, n],
                          d_input_matmul=[[m, n], [n, k]],
                          d_weight_matmul=[[n, m], [m, k]])
            forward = 2 * m * k * n
            gradients = ['d_input', 'd_weight']
        else:
            gradients = ['d_Q', 'd_K'] if op.name == 'qk' else ['d_P', 'd_V']
        ledger.append(dict(name=op.name, category=op.category, shapes=shapes,
                           repeats=op.repeats, gradient_names=gradients,
                           forward_flops=forward, gradient_each_flops=forward,
                           training_matrix_flops=3 * forward * op.repeats))
    weights = adapter.weights(c)
    parameters = sum(w.parameters for w in weights)
    storage = dict(bf16_weights=2 * parameters,
                   gradients=gradient_bytes * parameters,
                   master_weights=master_weight_bytes * parameters,
                   adam_first_moment_fp32=4 * parameters,
                   adam_second_moment_fp32=4 * parameters)
    total = sum(r['training_matrix_flops'] for r in ledger)
    attention = sum(r['training_matrix_flops'] for r in ledger if r['category'] == 'attention')
    approximation = 6 * parameters * rows
    return dict(schema_version=1, calculation='qwen-training-matrix', model=model,
                scenario=dict(batch=batch, tokens=tokens, supervised_tokens=supervised,
                              head_strategy=head_strategy, gradient_bytes=gradient_bytes,
                              master_weight_bytes=master_weight_bytes, routing=routing if hist is not None else None),
                sources=provenance(model), training_matrix_rows=ledger,
                tokens_per_expert_per_layer=hist,
                parameter_state_bytes=storage,
                summary=dict(parameters=parameters, input_tokens=rows, loss_tokens=supervised,
                             expert_assignments_per_layer=sum(hist) if hist is not None else 0,
                             active_experts_per_layer=sum(n > 0 for n in hist) if hist is not None else 0,
                             executed_head_rows=head_rows,
                             forward_matrix_flops=total // 3,
                             backward_matrix_flops=2 * (total // 3),
                             training_matrix_flops=total, attention_training_matrix_flops=attention,
                             six_nd_flops=approximation,
                             matrix_minus_six_nd_flops=total - approximation,
                             matrix_to_six_nd_ratio=total / approximation,
                             unsharded_parameter_state_bytes=sum(storage.values()),
                             activation_peak_bytes=None, complete_training_step_flops=None,
                             predicted_step_seconds=None),
                assumptions=[
                    'MoE 的每层路由直方图是显式情景，无 token drop 或容量填充；专家矩阵按各 n_e 求和。top-k 离散选择固定，router 矩阵仍计梯度，概率、合并、辅助损失和选择反向不在矩阵子账内。全部专家参数都纳入常驻状态，未激活专家不执行矩阵乘；6ND 用总参数仅作不适用的对照，不能预测 MoE 工作。',
                    '固定官方 Qwen3 Dense/MoE 配置，全参数训练，无历史 KV、无重计算；每个序列 T 个输入位置，D=B*T。loss_tokens 为调用方在移位、padding 和 mask 后给定的有效标签数，未假定等于原始文本 token 数。',
                    '每个线性矩阵列出前向、输入梯度、权重梯度；每次乘加计 2。QK/PV 各有两个输入梯度，按有效因果位置计数学工作；GQA 共享头的梯度归并算术另计，不用本表推断后端 tile 或矩形 kernel 工作。',
                    'dense 输出头始终执行 B*T 行，loss mask 不自动降低矩阵 FLOPs。compact 明确假设先 gather 有监督 hidden 再计算输出头；backbone 仍执行全部行，未根据标签位置剪枝，gather/scatter 与稀疏梯度特化未计。',
                    '6ND 的 N 是全部参数，包括 embedding 查表与 norm；它们并非每 token 都执行参数矩阵乘。实际矩阵账单列输出头与因果注意力，因此差额不必为正。',
                    '状态是无分片、无 offload 的声明方案：BF16 权重、显式梯度字节和 master 字节、FP32 Adam 两份 moment；不声称是某框架默认，master=0 仅代表取消独立副本。',
                    '未包含 embedding 梯度 scatter、归一化/激活/softmax/损失的前反向、优化器更新算术、激活存储、重计算、通信、临时缓冲及格式转换；这是训练矩阵子账，不是完整训练 FLOPs 或设备容量需求。',
                ])
