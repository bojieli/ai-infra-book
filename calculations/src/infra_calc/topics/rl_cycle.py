"""Declared RL batch matrix ledger; generation and learning use one sample cohort.

This is a Qwen workload example, not a reproduction of any published RL run.
Generation's first output comes from prefill, so G outputs require G-1 decodes.
"""
from ..models import forward
from ..schema import Scenario
from ..sources import provenance
from ..units import positive_int
from . import training_matrix


def calculate(model: str = 'qwen3-8b', prompts: int = 8, samples_per_prompt: int = 4,
              prompt_tokens: int = 1024, output_tokens: int = 256,
              accepted_samples: int = 16, update_epochs: int = 1,
              reference_passes: int = 1, teacher_passes: int = 0,
              rollout_replicas: int = 1, head_strategy: str = 'dense') -> dict:
    for key, value in locals().copy().items():
        if key not in ('model', 'head_strategy'):
            positive_int(value, key, allow_zero=key in ('reference_passes', 'teacher_passes'))
    generated = prompts * samples_per_prompt
    if accepted_samples > generated:
        raise ValueError('accepted_samples cannot exceed generated samples')
    # Validate architecture, sequence extent and output-head policy first.
    length = prompt_tokens + output_tokens - 1
    update = training_matrix.calculate(model=model, batch=accepted_samples, tokens=length,
                                      supervised_tokens=accepted_samples * output_tokens,
                                      head_strategy=head_strategy)
    prefill = forward(model, Scenario(batch=generated, tokens=prompt_tokens))['summary']['matrix_flops']
    decodes = output_tokens - 1
    first = last = decode_work = 0
    if decodes:
        first = forward(model, Scenario(batch=generated, history=prompt_tokens, tokens=1))['summary']['matrix_flops']
        last = forward(model, Scenario(batch=generated, history=prompt_tokens + decodes - 1, tokens=1))['summary']['matrix_flops']
        # For these Qwen adapters only attention depends on history, linearly.
        twice = decodes * (first + last)
        if twice % 2:
            raise ValueError('Affine decode sum must be integral')
        decode_work = twice // 2
    scoring = training_matrix.calculate(model=model, batch=generated, tokens=length,
                                       supervised_tokens=generated * output_tokens,
                                       head_strategy=head_strategy)['summary']['forward_matrix_flops']
    stages = [
        dict(name='rollout_prefill', samples=generated, passes=1, matrix_flops=prefill),
        dict(name='rollout_decode', samples=generated, passes=decodes, matrix_flops=decode_work),
        dict(name='reference_scoring', samples=generated, passes=reference_passes, matrix_flops=scoring * reference_passes),
        dict(name='teacher_scoring', samples=generated, passes=teacher_passes, matrix_flops=scoring * teacher_passes),
        dict(name='policy_update', samples=accepted_samples, passes=update_epochs,
             matrix_flops=update['summary']['training_matrix_flops'] * update_epochs),
    ]
    total = sum(stage['matrix_flops'] for stage in stages)
    parameters = update['summary']['parameters']
    return dict(schema_version=1, calculation='qwen-rl-cycle-matrix', model=model,
                scenario=dict(prompts=prompts, samples_per_prompt=samples_per_prompt,
                              prompt_tokens=prompt_tokens, output_tokens=output_tokens,
                              accepted_samples=accepted_samples, update_epochs=update_epochs,
                              reference_passes=reference_passes, teacher_passes=teacher_passes,
                              rollout_replicas=rollout_replicas, head_strategy=head_strategy),
                sources=provenance(model), rl_stages=stages,
                summary=dict(generated_samples=generated, accepted_samples=accepted_samples,
                             acceptance_fraction=accepted_samples / generated,
                             generated_output_tokens=generated * output_tokens,
                             accepted_output_tokens=accepted_samples * output_tokens,
                             training_input_tokens_per_epoch=accepted_samples * length,
                             supervised_tokens_per_epoch=accepted_samples * output_tokens,
                             prefill_calls_per_sample=1, decode_calls_per_sample=decodes,
                             first_decode_matrix_flops=first, last_decode_matrix_flops=last,
                             rollout_matrix_flops=prefill + decode_work,
                             cycle_matrix_flops=total,
                             matrix_flops_per_accepted_sample=total / accepted_samples,
                             matrix_flops_per_accepted_output_token=total / (accepted_samples * output_tokens),
                             policy_parameter_state_bytes=update['summary']['unsharded_parameter_state_bytes'],
                             bf16_weight_snapshot_bytes=2 * parameters,
                             independent_unicast_weight_sync_bytes=2 * parameters * rollout_replicas,
                             verifier_work=None, complete_cycle_flops=None, predicted_cycle_seconds=None),
                assumptions=[
                    '教学 RL 批次：所有 prompt 和 response 等长，无 EOS 提前停止、重试、跨样本前缀共享或 speculative decoding。先生成全部候选再评分／筛选；拒收样本仍消耗 rollout 和评分。accepted_samples 是已声明的本批整数结果，不用概率倒推一个确定的成功数。',
                    'prefill 最后位置产生第一个输出，随后 G-1 次 decode；不再把最后一个已生成 token 喂回模型。Qwen 有效因果注意力随历史呈仿射，首尾等差求和严格复现逐步矩阵计量；专家路由采用已有 balanced 情景，无容量 padding。',
                    '训练／评分输入长度 P+G-1，标签是 G 个输出，位置从 P-1 至 P+G-2。普通 dense head 计算全部位置；compact 假设只对这 G 个位置计算 head，backbone 仍完整执行。',
                    'reference 和 teacher 是与 policy 相同配置的独立快照，每 pass 对全部候选做 teacher-forced 前向；次数可为零。仅报告矩阵工作，不含 log-softmax、KL、优势估计、奖励／规则验证或辅助损失，也不冒充实际奖励模型配置。',
                    'update_epochs 次完整遍历已接受样本，计前向与反向矩阵；批次均为分析聚合规模，不代表能同时放入某张卡。优化器更新、激活、重计算、微批调度、通信及等待另算，未用 FLOPs 直接预测周期时间。',
                    '周期末同步一次完整 BF16 policy 权重到每个 rollout 副本，独立 unicast 发送量为副本数乘快照大小；不含优化器状态，不假定广播树、增量更新或参数转换。policy 状态与 rollout/reference/teacher 常驻内存不混加成设备峰值。',
                    '有效样本归一化包含拒收候选开销；质量、真实吞吐和各阶段有效供给未知，不能仅按工作量大小决定增配哪类设备。本例不声称复现 V4/K3 的 RL 系统。',
                ])
