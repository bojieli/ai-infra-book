"""Human-readable results and expanded per-layer CSV, derived from the same data."""
import csv
import io
import json
from fractions import Fraction


def markdown(result: dict) -> str:
    if result.get("calculation") == "protocol-handshake-declared-packet-graph":
        from .topics.protocol_handshake import markdown as render
        return render(result)
    if result.get("calculation") == "quic-early-stream-declared-packets":
        from .topics.protocol_early_stream import markdown as render
        return render(result)
    if result.get("calculation") == "finite-ack-window-sequence":
        from .topics.connection_sequence import markdown as render
        return render(result)
    if result.get("calculation") == "finite-ack-window-image":
        from .topics.connection_window import markdown as render
        return render(result)
    if result.get("calculation") == "image-request-streaming":
        from .topics.image_request_streaming import markdown as render
        return render(result)
    if result.get("calculation") == "image-request-budget":
        from .topics.image_request_budget import markdown as render
        return render(result)
    if result.get("calculation") == "hierarchical-gradient":
        from .topics.hierarchical_gradient import markdown as render
        return render(result)
    if result.get("calculation") == "paired-projection-conditional-cost":
        from .topics.paired_projection_cost import markdown as render
        return render(result)
    if result.get("calculation") == "qwen-matrix-vector-handoff":
        from .topics.matrix_vector_handoff import markdown as render
        return render(result)
    if result.get("calculation") == "v4-shared-fp8-copy-coordinates":
        from .topics.v4_copy_coordinates import markdown as render
        return render(result)
    if result.get("calculation") == "qwen-attention-input-pipeline":
        from .topics.attention_input_pipeline import markdown as render
        return render(result)
    if result.get("calculation") == "fa4-single-sm-resource-balance":
        from .topics.fa4_resource_balance import markdown as render
        return render(result)
    if result.get("calculation") == "storage-generation-comparison":
        from .topics.storage_generation_comparison import markdown as render
        return render(result)
    if result.get("calculation") == "granularity-conditional-selection":
        from .topics.granularity_selection import markdown as render
        return render(result)
    if result.get("calculation") == "sealed-trace-cache-lifecycle":
        from .topics.trace_cache_lifecycle import markdown as render
        return render(result)
    if result.get("calculation") == "v4-flash-mtp-single-call":
        from .topics.v4_mtp_forward import markdown as render
        return render(result)
    if result.get("calculation") == "qwen8-training-input-supply":
        from .topics.training_input_supply import markdown as render
        return render(result)
    if result.get("schema") == "qwen235-cohort-execution-v1":
        from .topics.qwen235_execution import markdown as render
        return render(result)
    if result.get("schema") == "qwen235-expert-granularity-v1":
        from .topics.qwen235_expert_granularity import markdown as render
        return render(result)
    if result.get("schema") == "architecture-tile-work-v1":
        from .topics.architecture_tile_work import markdown as render
        return render(result)
    if result.get("schema") == "trace-resource-bridge-v1":
        from .topics.trace_resource_bridge import markdown as render
        return render(result)
    if result.get("schema") == "request-hardware-bridge-v1":
        from .topics.request_hardware_bridge import markdown as render
        return render(result)
    if result.get("calculation") == "omni-audio-preprocess":
        from .topics.omni_audio_preprocess import markdown as render
        return render(result)
    if result.get("schema") == "v4-optimizer-reference-v1":
        from .topics.v4_optimizer import markdown as render
        return render(result)
    if result.get("calculation") == "v4-fixed-selection-moe-training":
        from .topics.v4_moe_training import markdown as render
        return render(result)
    if result.get("calculation") == "qwen8-pipeline-gemm-saved-identities":
        from .topics.training_pipeline_gemm_state import markdown as render
        return render(result)
    if result.get("calculation") == "v4-compressor-online-timegraph-training":
        from .topics.v4_compressor_online import markdown as render
        return render(result)
    if result.get("calculation") == "stage-resource-bounds":
        from .topics.stage_resource_bounds import markdown as render
        return render(result)
    if result.get("calculation") == "vision-preprocess":
        from .topics.vision_preprocess import markdown as render
        return render(result)
    if result.get("calculation") == "qwen8-training-pipeline-schedule":
        from .topics.training_pipeline_schedule import markdown as render
        return render(result)
    if result.get("calculation") == "v4-ratio4-overlap-prefill-training-reference":
        from .topics.v4_compressor_overlap import markdown as render
        return render(result)
    if result.get("calculation") == "v4-ratio128-compressor-training-reference":
        from .topics.v4_compressor_training import markdown as render
        return render(result)
    if result.get("calculation") == "v4-attention-periphery-training-reference":
        from .topics.v4_attention_projections import markdown as render
        return render(result)
    if result.get("calculation") == "v4-tied-kv-attention-training-reference":
        from .topics.v4_attention_training import markdown as render
        return render(result)
    if result.get("calculation") == "v4-training-smooth-primitives":
        from .topics.v4_training_primitives import markdown as render
        return render(result)
    if result.get("calculation") == "v4-hc-training-wrapper":
        from .topics.v4_hc_training import markdown as render
        return render(result)
    if result.get("calculation") == "real-scaling-lifetime-proxy":
        from .topics.real_scaling_lifecycle import markdown as render
        return render(result)
    if result.get("calculation") == "real_scaling_fit":
        from .topics.real_scaling_fit import markdown as render
        return render(result)
    if result.get("calculation") == "qwen8-training-nonmatrix-reference":
        from .topics.training_nonmatrix import markdown as render
        return render(result)
    if result.get("calculation") == "archived-strategy-record-cost":
        from .topics.strategy_record_cost import markdown as render
        return render(result)
    if result.get("calculation") == "fish-cli-wave-export":
        from .topics.fish_wave_export import markdown as render
        return render(result)
    if result.get("calculation") == "request-model-comparison":
        from .topics.request_model_comparison import markdown as render
        return render(result)
    if result.get("calculation") == "dense-quantized-placement":
        from .topics.dense_quantized_placement import markdown as render
        return render(result)
    if result.get("calculation") == "qwen235-placement-capacity":
        from .topics.qwen235_placement import markdown as render
        return render(result)
    if result.get("calculation") == "v4-sequential-prefix-continuation":
        from .topics.v4_prefix_continuation import markdown as render
        return render(result)
    if result.get("calculation") == "flux2-vae-decoder-dag":
        from .topics.flux_vae_decode import markdown as render
        return render(result)
    if result.get("calculation") == "architecture-variants":
        from .topics.architecture_variants import markdown as render
        return render(result)
    if result.get("calculation") == "recorded-workload-profiles":
        from .topics.workload_profiles import markdown as profile_markdown
        return profile_markdown(result)
    if result.get("calculation") == "qwen36-base-text-ledger":
        from .topics.qwen36_forward import markdown as render
        return render(result)
    if result.get("calculation") == "supernode-cohort-cost":
        from .topics.supernode_cohort_cost import markdown as render
        return render(result)
    if result.get("calculation") == "growing-remote-kv":
        from .topics.growing_remote_kv import markdown as render
        return render(result)
    if result.get("calculation") == "memory-pool-access":
        from .topics.memory_pool_access import markdown as render
        return render(result)
    if result.get("calculation") == "qwen36-capacity":
        from .topics.qwen36_capacity import markdown as render
        return render(result)
    if result.get("calculation") == "qwen35-base-text-ledger":
        from .topics.qwen35_forward import markdown as qwen35_markdown
        return qwen35_markdown(result)
    if result.get("calculation") == "tp-ep-reconfiguration":
        from .topics.reconfiguration import markdown as migration_markdown
        return migration_markdown(result)
    if result.get("calculation") == "scaling-law":
        from .topics.scaling_law import markdown as scaling_markdown
        return scaling_markdown(result)
    if result.get("calculation") == "ub-scope":
        return ub_scope_markdown(result)
    scenario = dict(result['scenario'])
    if result.get('calculation') == 'connection-states':
        scenario['relations'] = 'Explicit active relations are preserved in the JSON result.'
    if isinstance(scenario.get('routes'), list):
        scenario['routes'] = 'Explicit per-token routes are preserved in the JSON result.'
    lines = [f"# {result['calculation']} — {result.get('model', '')}", "",
             "输入：`" + json.dumps(scenario, ensure_ascii=False, sort_keys=True) + "`", "",
             ("CPU/RSS来自封存实际进程记录；采样积分与有限窗恒等式不代表生产稳态或物理内存。" if "environment_process_runs" in result or "environment_rounds" in result else "来自封存DCP重分片恢复与下一步实际训练记录，非GPU性能。" if "checkpoint_resume_tensors" in result else "来自封存DCP元数据提交前终止实验，未完成提交不填时间。" if "checkpoint_fault_rows" in result else "来自封存CPU保存基线与实际文件核验，非Qwen或GPU性能。" if "checkpoint_baseline_runs" in result else "来自实际坏页请求记录；未完成观测保留null，成功回退不等于修复存储。" if "fault_policy_rows" in result else "缺页恢复及输出来自封存实验，原页／恢复页逐BF16元素核验；不推断差异原因。" if "missing_page_cases" in result else "文件载荷与调用来自封存正常重启实验，读入量与复用量分开。" if "restart_requests" in result else "时间与负载来自封存双worker压力实验；目标与两任务完成分开，非预测路由。" if "pressure_requests" in result else "命中、时间和worker身份来自封存原生路由回放，矩阵工作按官方配置复算。" if "router_policy_rows" in result else "容量、输出和时间来自封存KV实验；自然质量与固定输出计时分开，含Q精度控制。" if "kv_quality_conditions" in result else "请求时间来自封存实际交付；SLO阈值为本次分析输入，仅衡量计时达标。" if "service_requests" in result else "CUDA event区间来自封存逐块实测；有效配对和backbone矩阵工作按官方配置独立复算。" if "chunk_history_rows" in result else "时长与接受直方图为教学输入；结果是有限输出请求的精确期望，不是实测延迟。" if "budget_policies" in result else "数值为教学概率的精确有理数枚举，不是模型采样实测。" if "sampling_tokens" in result else "命中与时长来自封存Agent回放；矩阵工作按官方配置复算。" if "apc_rounds" in result else "KV块与调度来自封存引擎记录，字节容量按官方模型配置复算。" if "kv_trace_runs" in result else "RPC阶段来自封存实测；两端阶段不可重复相加，SSH转发条件必须保留。" if "rpc_groups" in result else "本机FFN计时与Nsight事件来自固定实验；MPK为作者另机报告，二者不可混算。" if "runtime_timings" in result else "模型／工具墙钟来自固定实验记录；矩阵与 KV 为分析计量，条件式替换另列。" if "agent_rounds" in result else "数组访问为源码计数；匹配时长来自固定 CPU 实验，非缓存测量。" if "loop_access_rows" in result else "数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。"), "",
             "| 结果 | 值 |", "| --- | ---: |"]
    for key, value in result["summary"].items():
        formatted = f"{value:,}" if isinstance(value, (int, float)) and not isinstance(value, bool) else f"`{json.dumps(value)}`"
        lines.append(f"| {key} | {formatted} |")
    if 'omni_vision_matrices' in result:
        lines.extend(['', 'Omni视觉编码；每行FLOPs已乘repeats。时间块之间不做视觉attention。', '', '| 矩阵 | 输入 | 权重/右矩阵 | repeats | 矩阵FLOPs | 读/写接口bytes |', '| --- | --- | --- | --- | --- | --- |'])
        for row in result['omni_vision_matrices']:
            lines.append(f"| {row['name']} | {row['input_shape']} | {row['weight_shape']} | {row['repeats']} | {row['matrix_flops']} | {row['interface_read_bytes']}/{row['interface_write_bytes']} |")
        lines.extend(['', '| 非矩阵步骤 | 元素数 | repeats | 已汇总标量工作 | 已汇总特殊函数 |', '| --- | --- | --- | --- | --- |'])
        for row in result['omni_vision_scalars']:
            lines.append(f"| {row['name']} | {row['elements']} | {row['repeats']} | {row['scalar_flops']} | {row['special_ops']} |")
        lines.extend(['', '逐项grid/时间/命中：`' + json.dumps(result['omni_vision_items'], ensure_ascii=False) + '`', '', '独立Thinker注入接口：`' + json.dumps(result['deepstack_delivery'], ensure_ascii=False) + '`'])
    if 'thinker_prefill' in result:
        lines.extend(['', '| 请求节点 | 依赖 | 矩阵FLOPs | 已计标量 | 已计接口bytes |', '| --- | --- | --- | --- | --- |'])
        for row in result['request_execution_nodes']:
            lines.append(f"| {row['id']} | {row['depends_on']} | {row['matrix_flops']} | {row['accounted_scalar_flops']} | {row['accounted_interface_bytes']} |")
        selected=[('prefill',result['thinker_prefill'])]
        if result['thinker_decode']:
            selected.append(('first_decode',result['thinker_decode'][0]))
            if len(result['thinker_decode'])>1:selected.append(('last_decode',result['thinker_decode'][-1]))
        for label, stage in selected:
            lines.extend(['', label + '；所有decode逐次工作见JSON。', '', '| 矩阵 | M | K | N | 层重复 | 已汇总FLOPs |', '| --- | --- | --- | --- | --- | --- |'])
            for row in stage['matrices']:
                lines.append(f"| {row['name']} | {row['rows_per_layer']} | {row['input_width']} | {row['output_width']} | {row['repeats']} | {row['matrix_flops']} |")
        lines.extend(['', '音频缓存身份及实际miss分段：`' + json.dumps(result['audio_cache_contract'], ensure_ascii=False) + '`', '', 'DeepStack注入：`' + json.dumps(result['deepstack_injection'], ensure_ascii=False) + '`'])
    if 'training_history_rows' in result:
        lines.extend(['', '公开字段与代理算量：6ND不是全模型逐算子训练FLOPs。', '',
                      '| 模型 | 总/激活参数（报告值） | 代理N | tokens及范围 | 6ND代理FLOPs | GPU小时/型号 |',
                      '| --- | --- | --- | --- | --- | --- |'])
        for row in result['training_history_rows']:
            data = row['input']; context = row['parameter_context']
            lines.append(f"| {data['id']} | {context['total_reported']}/{context['active_reported']} | {data['parameter_proxy']} ({row['proxy_kind']}) | {data['training_tokens']} / {data['token_scope']} | {row['proxy_flops']} | {data['gpu_hours']}/{data['gpu_family']} |")
        lines.extend(['', '| 模型 | D/N精确值 | 卡数角色 | 条件固定卡数天数 | 附同scope条件的最大卡数下界天数 | 来源与范围 |', '| --- | --- | --- | --- | --- | --- |'])
        for row in result['training_history_rows']:
            data = row['input']; duration = row['duration']
            lines.append(f"| {data['id']} | {row['tokens_per_parameter_exact']} | {data['gpu_count']}/{data['gpu_count_role']} | {duration['conditional_constant_count_days_exact']} | {duration['conditional_calendar_lower_bound_days_exact']} | {data['source_id']} / {data['source_location']}；{data['scope_notes']} |")
        lines.extend(['', '论文报告的阶段观测（非全程MFU）：', '', '| 模型 | GPU/数量 | 序列长度 | TP/CP/PP/DP | TFLOPs/GPU | BF16 MFU | 来源 |', '| --- | --- | --- | --- | --- | --- | --- |'])
        for row in result['reported_performance']:
            lines.append(f"| {row['model']} | {row['gpu_family']}/{row['gpu_count']} | {row['sequence_length']} | {row['tp']}/{row['cp']}/{row['pp']}/{row['dp']} | {row['reported_tflops_per_gpu']} | {row['reported_bf16_mfu_fraction']} | {row['source_id']} / {row['source_location']} |")
        for key in ('stage_reports', 'comparisons', 'duration_scenarios', 'lifecycle'):
            lines.extend(['', key, ''])
            for row in result[key]:
                lines.append('- `' + json.dumps(row, ensure_ascii=False) + '`')
        lines.extend(['', 'None/null为未知；条件卡数时间不是实测日期。Llama405跨模型卡总GPU小时与论文最大卡数仅给附加同scope假设的下界。reported_performance为论文单独报告的阶段观测，不能替代全程MFU。成本使用caller声明单位和范围，不用于不同任务质量的效率排名。'])
    if 'clone_placements' in result:
        for key in ('clone_placements', 'creation_paths', 'measured_prewarm_trials'):
            rows = result[key]
            columns = list(rows[0])
            lines.extend(['', key, '', '| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |'])
            for row in rows:
                lines.append('| ' + ' | '.join(json.dumps(row[c], ensure_ascii=False) for c in columns) + ' |')
        for key in ('snapshot_budget', 'prewarm_budget'):
            lines.extend(['', key + '：`' + json.dumps(result[key], ensure_ascii=False) + '`'])
        lines.extend(['', '本地进程记录不代表云端microVM创建实测；创建API、首工具完成、重连、真实增量格式与完整物理内存峰值仍未核实。'])
    if 'sequence_work' in result:
        for key, title in [('sequence_work', '同模型执行路径工作'), ('sequence_states', '历史状态与下一token读写'), ('sequence_checks', '同模型缓存/重算输出核验'), ('sequence_matrices', '完整逐矩阵形状和接口')]:
            rows=result[key]
            columns=list(rows[0])
            lines.extend(['', title, '', '| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |'])
            for row in rows:
                lines.append('| ' + ' | '.join(json.dumps(row[c], ensure_ascii=False) for c in columns) + ' |')
        lines.extend(['', '逐节点/边依赖图、实际教学权重和输入保留于同名JSON；单位节点关键路径不是硬件时延。'])
    if 'tpu_capacity_candidates' in result:
        lines.extend(['', '| 条件候选 | 增量/原容量 | 总量/原容量 | 声明新增整服务器当量 |', '| --- | --- | --- | --- |'])
        for row in result['tpu_capacity_candidates']:
            lines.append(f"| {row['candidate']} | {row['incremental_capacity_in_baseline_units_exact']} | {row['total_capacity_in_baseline_units_exact']} | {row['added_whole_server_equivalents']} |")
        lines.extend(['', '逐因子推算：`' + json.dumps(result['tpu_demand_factors'], ensure_ascii=False) + '`；服务器当量只在显式给出教学基准时计算，不是历史实际数量。'])
    if 'nic_cpu_candidates' in result:
        lines.extend(['', '| 历史/声明每核包率 | 忙核秒/秒 | 留余量后的核当量 | 专用整数核 |', '| --- | --- | --- | --- |'])
        for row in result['nic_cpu_candidates']:
            lines.append(f"| {row['baseline_packets_per_core_second_exact']} | {row['busy_core_seconds_per_second_exact']} | {row['required_core_equivalents_exact']} | {row['dedicated_integer_cores']} |")
        lines.extend(['', '包数分布：`' + json.dumps(result['nic_packet_classes'], ensure_ascii=False) + '`', '', '独立PCIe约束：`' + json.dumps(result['pcie_budget'], ensure_ascii=False) + '`'])
    if 'image_setup_boundary_memory_summary' in result:
        lines.extend(['', '加入setup helper的声明存活图：`' + json.dumps(result['image_setup_boundary_memory_summary'], ensure_ascii=False) + '`；逐事件见JSON，未覆盖完整allocator。'])
    if 'audio_encoder_operators' in result:
        lines.extend(['', '输入音频编码；每行乘repeats。完整chunk与attention分段边界保留在JSON。', '', '组批：`' + json.dumps(result['chunk_execution'], ensure_ascii=False) + '`', '', '| 算子 | 类型 | 形状 | repeats | 矩阵FLOPs | 标量工作 | 特殊操作 |', '| --- | --- | --- | --- | --- | --- | --- |'])
        for row in result['audio_encoder_operators']:
            lines.append(f"| {row['name']} | {row['kind']} | {row['shape']} | {row['repeats']} | {row['matrix_flops']} | {row['scalar_flops']} | {row['special_ops']} |")
    if result.get('vision_image_rows'):
        lines.extend(['', '| 图片 | 缓存命中 | grid THW | patch数 | 语言图像位置 | 本次编码矩阵FLOPs | 完整EC bytes |', '| --- | --- | --- | --- | --- | --- | --- |'])
        for r in result['vision_image_rows']:
            lines.append(f"| {r['image_index']} | {r['cache_hit']} | {r['grid_thw']} | {r['patches']} | {r['merged_positions']} | {r['matrix_flops']} | {r['complete_encoder_bytes']} |")
    image_details = result.get('vision_encoding', {}).get('per_image_encodings', [])
    if image_details:
        lines.extend(['', '逐图视觉矩阵：本次工作已乘该图是否未命中；copies仍表示模型内部重复。', '', '| 图片 | 算子 | A | B | copies | 本次矩阵FLOPs |', '| --- | --- | --- | --- | --- | --- |'])
        for image in image_details:
            runs = int(not image['cache_hit'])
            for row in image['encoding']['vision_encoding_matrices']:
                lines.append(f"| {image['image_index']} | {row['operator']} | {row['a_shape']} | {row['b_shape']} | {row['copies']} | {runs*row['matrix_flops']} |")
    if 'position_bridge' in result:
        bridge = result['position_bridge']
        lines.extend(['', '## 静态图像位置构造', '',
                      '旋转坐标跨度与实际KV位置数分开；以下整数/张量接口不重复加入视觉或语言矩阵，也不是HBM测量。', '',
                      '| 指标 | 值 |', '| --- | --- |'])
        for key, value in bridge['summary'].items():
            lines.append(f"| {key} | `{json.dumps(value, ensure_ascii=False)}` |")
        lines.extend(['', '| 源码步骤 | 声明工作与接口 |', '| --- | --- |'])
        for step in bridge['source_steps']:
            details = {key: value for key, value in step.items() if key != 'name'}
            lines.append(f"| {step['name']} | `{json.dumps(details, ensure_ascii=False)}` |")
        lines.extend([''] + ['- ' + note for note in bridge['boundaries']])
    if 'vl_request_stages' in result:
        lines.extend(['', '| 请求阶段 | 执行次数 | 已汇总矩阵FLOPs |', '| --- | ---: | ---: |'])
        for r in result['vl_request_stages']:
            lines.append(f"| {r['stage']} | {r['executions']} | {r['matrix_flops']} |")
        for name in ('language_prefill', 'language_decode_first', 'language_decode_last'):
            stage = result.get(name)
            if stage is None:
                continue
            lines.extend(['', name + '：每行成本乘repeats；完整decode等差和见JSON。', '', '| 算子 | repeats | 形状 | 矩阵FLOPs | 读权重bytes | 读/写激活bytes |', '| --- | ---: | --- | ---: | ---: | --- |'])
            for r in stage['operators']:
                lines.append(f"| {r['name']} | {r['repeats']} | {r['shapes']} | {r['matrix_flops']} | {r['weight_read_bytes']} | {r['activation_read_bytes']}/{r['activation_write_bytes']} |")
    if 'image_text_encoder_matrices' in result:
        lines.extend(['', '| 文本编码矩阵 | 左形状 | 权重形状 | 重复 | 矩阵FLOPs |', '| --- | --- | --- | ---: | ---: |'])
        for r in result['image_text_encoder_matrices']:
            lines.append(f"| {r['branch']}/{r['name']} | {r['lhs_shape']} | {r['parameter_framework_shape']} | {r['repeats']} | {r['matrix_flops']} |")
        lines.extend(['', '| VAE操作 | 输入 | 输出 | kernel | dense核FLOPs | nonpadding FLOPs |', '| --- | --- | --- | --- | ---: | ---: |'])
        for r in result['image_vae_convolutions']:
            lines.append(f"| {r['name']} | {r['input_shape']} | {r['output_shape']} | {r['kernel_shape']} | {r['dense_kernel_flops']} | {r['nonpadding_flops']} |")
    for key, title in [('image_reference_operations', '参考非矩阵运算（特殊函数单列）'), ('image_boundary_memory_events', '声明边界缓冲区生命周期（非运行时显存峰值）')]:
        rows = result.get(key, [])
        if rows:
            columns = list(rows[0])
            lines.extend(['', title, '', '| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |'])
            for row in rows:
                lines.append('| ' + ' | '.join(json.dumps(row.get(c), ensure_ascii=False) for c in columns) + ' |')
    if 'image_matrix_service_bound' in result:
        lines.extend(['', '条件式矩阵供给下界：`' + json.dumps(result['image_matrix_service_bound'], ensure_ascii=False) + '`'])
    if 'audio_supply' in result:
        lines.extend(['', '音频阶段供给：`' + json.dumps(result['audio_supply'], ensure_ascii=False) + '`'])
        codec = result.get('audio_codec_operations')
        if codec:
            lines.extend(['', '| codec算子 | 类型 | 矩阵FLOPs | 标量FLOPs | 权重/读/写接口bytes |', '| --- | --- | ---: | ---: | --- |'])
            for r in codec['operators']:
                lines.append(f"| {r['name']} | {r['kind']} | {r['matrix_flops']} | {r['scalar_flops']} | {r['weight_interface_bytes']}/{r['activation_read_bytes']}/{r['activation_write_bytes']} |")
    if 'retry_terminal_paths' in result:
        lines.extend(['', '| 节点路径 | 终点 | 路径概率 | 全路径费用 | 时间秒 | CPU核秒 | 驻留bytes·s | 质量且按时 |', '| --- | --- | --- | --- | --- | --- | --- | --- |'])
        for r in result['retry_terminal_paths']:
            lines.append(f"| {' → '.join(r['nodes'])} | {r['terminal']} | {r['probability_exact']} | {r['cost_exact']} | {r['seconds_exact']} | {r['cpu_seconds_exact']} | {r['resident_byte_seconds_exact']} | {r['quality_and_deadline_success']} |")
    if 'vision_encoding_matrices' in result:
        lines.extend(['', '以下每项已经乘copies，均为每张未命中图片；请求总量再乘编码次数。', '', '| 视觉矩阵 | A | B | copies | FLOPs/图 | 语义读bytes | 语义写bytes |', '| --- | --- | --- | ---: | ---: | ---: | ---: |'])
        for r in result['vision_encoding_matrices']:
            lines.append(f"| {r['operator']} | {r['a_shape']} | {r['b_shape']} | {r['copies']} | {r['matrix_flops']} | {r['semantic_read_bytes']} | {r['semantic_write_bytes']} |")
        lines.extend(['', '| 非矩阵步骤 | 形状 | 已汇总参考运算次数/图 | 语义读bytes | 语义写bytes |', '| --- | --- | --- | ---: | ---: |'])
        for r in result['vision_encoding_scalars']:
            lines.append(f"| {r['operator']} | {r['shape']} | {r['counts']} | {r['semantic_read_bytes']} | {r['semantic_write_bytes']} |")
    if 'audio_stages' in result:
        for stage in result['audio_stages']:
            lines.extend(['', '阶段：' + stage['name'], '', '| 矩阵 | M | K | N | 层重复 | 已汇总矩阵FLOPs |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
            for r in stage['matrices']:
                lines.append(f"| {r['name']} | {r['rows_per_layer']} | {r['input_width']} | {r['output_width']} | {r['repeats']} | {r['matrix_flops']} |")
            lines.extend(['', '本阶段QK/PV与KV：`' + json.dumps(stage['summary'], ensure_ascii=False) + '`'])
        lines.extend(['', '码本循环：`' + json.dumps(result['audio_codebook_loops'], ensure_ascii=False) + '`', '', 'codec时间轴：`' + json.dumps(result['audio_codec_timing'], ensure_ascii=False) + '`'])
    if 'image_generation_matrices' in result:
        lines.extend(['', '| 分支/矩阵 | 左形状 | 右形状 | 重复 | 矩阵FLOPs | 左/右/输出逻辑bytes |', '| --- | --- | --- | ---: | ---: | --- |'])
        for r in result['image_generation_matrices']:
            lines.append(f"| {r['branch']}/{r['name']} | {r['lhs_shape']} | {r['rhs_mathematical_shape']} | {r['repeats']} | {r['matrix_flops']} | {r['logical_lhs_operand_bytes']}/{r['logical_rhs_operand_bytes']}/{r['logical_output_bytes']} |")
    for key, title in [('image_setup_operations', '模型初始化与请求setup运算'), ('image_setup_data_operations', 'setup转换、索引与随机数（非FLOPs）')]:
        if key in result:
            lines.extend(['', title + '：', ''])
            for row in result[key]:
                lines.append('- `' + json.dumps(row, ensure_ascii=False) + '`')
    wan_vae = result.get('wan_vae_decode')
    if wan_vae:
        lines.extend(['', 'Wan VAE：首块、第二块与稳定缓存块分别展开；FLOPs已乘repeats。非矩阵及完整工作区另计。', '', '| 阶段/算子 | 类型 | 输入或Q形状 | 输出或V形状 | repeats | 矩阵FLOPs | 逻辑接口bytes |', '| --- | --- | --- | --- | --- | --- | --- |'])
        for row in wan_vae['operators']:
            lines.append(f"| {row['phase']}/{row['name']} | {row['kind']} | {row.get('input_shape',row.get('q_shape'))} | {row.get('output_shape',row.get('v_shape'))} | {row['repeats']} | {row['matrix_flops']} | {row['logical_operand_bytes']} |")
    if wan_vae and 'nonmatrix_work' in wan_vae:
        work=wan_vae['nonmatrix_work']
        lines.extend(['', 'Wan VAE非矩阵边界：`' + json.dumps(work.get('summary'), ensure_ascii=False) + '`', '', '| 算子 | 源码行 | calls | 算术 | 比较 | exp | sqrt | 逻辑读/写bytes |', '| --- | --- | --- | --- | --- | --- | --- | --- |'])
        for row in work['operators']:
            lines.append(f"| {row['operator']} | {row['official_source_line']} | {row['calls']} | {row['scalar_arithmetic_ops']} | {row['comparisons']} | {row['exp_evaluations']} | {row['sqrt_evaluations']} | {row['logical_read_bytes']}/{row['logical_write_bytes']} |")
        lines.extend(['', '形状计数依据与限制：`' + json.dumps(work.get('shape_proof'), ensure_ascii=False) + '`；原件和捕获记录见JSON sources。逻辑bytes与矩阵接口可能交叠，不相加冒充唯一HBM流量。'])
    wan_text = result.get('wan_text_encoding')
    if wan_text:
        lines.extend(['', 'Wan文本encoder：每个分支独立一次完整padding forward，之后才裁有效hidden；不随去噪步数重复。', '', '| 分支 | padding行 | 有效行 | 矩阵FLOPs | 返回hidden bytes |', '| --- | --- | --- | --- | --- |'])
        for row in wan_text['branches']:
            lines.append(f"| {row['branch']} | {row['padded_tokens']} | {row['valid_tokens']} | {row['matrix_flops']} | {row['returned_hidden_bytes']} |")
        lines.extend(['', '| 每次encoder矩阵 | A | B | copies | 汇总FLOPs |', '| --- | --- | --- | --- | --- |'])
        for row in wan_text['operators_per_call']:
            lines.append(f"| {row['operator']} | {row['a_shape']} | {row['b_shape']} | {row['copies']} | {row['matrix_flops']} |")
    if 'video_generation_stages' in result:
        for stage in result['video_generation_stages']:
            lines.extend(['', '阶段：' + stage['stage'] + '；执行次数=' + str(stage['evaluations']), '', '| 矩阵 | A | B | C | copies | 每evaluation汇总FLOPs | 逻辑bytes |', '| --- | --- | --- | --- | ---: | ---: | ---: |'])
            conditioning = stage.get('scheduled_conditioning')
            if conditioning:
                lines.extend(['', '实际调度条件化（完整逐步矩阵及缓存账见同名JSON）：`' + json.dumps({k:v for k,v in conditioning.items() if k != 'step_rows'}, ensure_ascii=False) + '`'])
                lines.extend(['', '| step | video time | audio time | distinct times | 每evaluation条件化矩阵FLOPs |', '| --- | --- | --- | --- | --- |'])
                for row in conditioning.get('step_rows', []):
                    lines.append(f"| {row['step']} | {row['video_timestep']} | {row['audio_timestep']} | {row['unique_timestep_count']} | {row['matrix_flops_per_evaluation']} |")
            for r in stage['operators']:
                lines.append(f"| {r['operator']} | {r['a_shape']} | {r['b_shape']} | {r['c_shape']} | {r['copies']} | {r['flops']} | {r['logical_operand_bytes']} |")
    if 'environment_condition_medians' in result:
        lines.extend(['', '| 条件中位数 | 窗口秒 | CPU核秒 | 采样RSS峰值和bytes | RSS bytes·s |', '| --- | ---: | ---: | ---: | ---: |'])
        for r in result['environment_condition_medians']:
            lines.append(f"| {r['condition']} | {r['observation_window_seconds']} | {r['recorded_process_cpu_seconds']} | {r['sampled_rss_peak_bytes']} | {r['sampled_rss_byte_seconds']} |")
    if result.get('calculation') == 'deepseek-v3-base-forward':
        lines.extend(['', '覆盖边界：`' + json.dumps(result['coverage'], ensure_ascii=False) + '`'])
    if 'multimodal_pool_assignments' in result:
        lines.extend(['', '| E workers | PD workers | 编码上界req/s | PD上界req/s | 网络上界req/s | 已知最小界req/s |', '| ---: | ---: | --- | --- | --- | --- |'])
        for r in result['multimodal_pool_assignments']:
            lines.append(f"| {r['encoder_workers']} | {r['pd_workers']} | {r['uncached_encode_requests_per_second_exact']} | {r['pd_requests_per_second_exact']} | {r['network_requests_per_second_exact']} | {r['bound_requests_per_second_exact']} |")
    if 'v4_fp8_linear_rows' in result:
        lines.extend(['', '| Linear | 调用数 | 权重shape | 有效矩阵FLOPs | tile矩阵FLOPs | scale FLOPs |', '| --- | ---: | --- | ---: | ---: | ---: |'])
        for r in result['v4_fp8_linear_rows']:
            t = r['totals']
            lines.append(f"| {r['name']} | {r['invocation_count']} | {r['per_invocation']['weight_shape']} | {t['valid_matrix_flops']} | {t['padded_tile_matrix_flops']} | {t['logical_scale_flops']} |")
    if 'routing_cost_rows' in result:
        lines.extend(['', '| 假想服务 | 总费用 | 预期质量成功数 | 每质量成功费用 | 预期质量且按时成功数 | 每联合成功费用 |', '| --- | --- | --- | --- | --- | --- |'])
        for r in result['routing_cost_rows']:
            lines.append(f"| {r['candidate']} | {r['total_cost_exact']} | {r['expected_quality_successes_exact']} | {r['cost_per_quality_success_exact']} | {r['expected_joint_successes_exact']} | {r['cost_per_joint_success_exact']} |")
    if 'weight_handoff_ranks' in result:
        lines.extend(['', '| 交接阶段 | 同时驻留bytes |', '| --- | ---: |'])
        for name, value in result['summary']['phase_live_bytes'].items():
            lines.append(f"| {name} | {value} |")
        lines.extend(['', '| rank | 专家区间[start,stop) | 专家bytes | 全部所需权重bytes |', '| --- | --- | ---: | ---: |'])
        for r in result['weight_handoff_ranks']:
            lines.append(f"| {r['rank']} | [{r['expert_start']},{r['expert_stop']}) | {r['expert_bytes']} | {r['required_weight_bytes']} |")
        lines.extend(['', '| 单播策略 | 生产端出口bytes | 最大接收bytes | 传输下界秒（精确） |', '| --- | ---: | ---: | --- |'])
        for r in result['weight_handoff_transfers']:
            lines.append(f"| {r['strategy']} | {r['producer_egress_bytes']} | {r['largest_receiver_bytes']} | {r['transfer_bound_exact_seconds']} |")
    if 'routing_metadata_components' in result:
        lines.extend(['', '| 声明载荷组成 | bytes |', '| --- | ---: |'])
        for name,value in result['routing_metadata_components'].items():
            lines.append(f"| {name} | {value} |")
        lines.extend(['', '| ID编码 | bytes/ID | 最大ID | 能表示全部专家 | ID载荷bytes |', '| --- | ---: | ---: | --- | --- |'])
        for r in result['routing_metadata_encodings']:
            lines.append(f"| {r['encoding']} | {r['bytes_per_id']} | {r['max_id']} | {r['can_represent_all_experts']} | {r['routed_id_bytes']} |")
    if 'dense_scale_rows' in result:
        lines.extend(['', '名义Dense 6ND粗估，不代替真实模型逐算子账；卡数为必要下界。', '',
                      '| 型号 | 参数 | task tokens | 效率 | 训练天 | 持久状态总bytes | 总容量可容纳 |',
                      '| --- | ---: | ---: | --- | ---: | ---: | --- |'])
        for r in result['dense_scale_rows']:
            lines.append(f"| {r['device']} | {r['parameters']} | {r['task_tokens']} | {r['efficiency_exact']} | {r['training_days']:.6f} | {r['persistent_state_bytes']} | {r['aggregate_persistent_capacity_fits']} |")
        lines.extend(['', '| 型号 | 参数 | 效率 | 期限天 | 算力张数 | 持久容量张数 | 必要张数 |', '| --- | ---: | --- | ---: | ---: | ---: | ---: |'])
        for r in result['dense_scale_rows']:
            for d in r['deadline_requirements']:
                lines.append(f"| {r['device']} | {r['parameters']} | {r['efficiency_exact']} | {d['deadline_days']} | {d['compute_card_count']} | {d['state_card_count']} | {d['necessary_card_count']} |")
        lines.extend(['', '| 型号 | 效率 | 期限天 | 算力允许参数上界 | 持久容量允许参数上界 | 两者min |', '| --- | --- | ---: | ---: | ---: | ---: |'])
        for r in result['dense_scale_bounds']:
            lines.append(f"| {r['device']} | {r['efficiency_exact']} | {r['deadline_days']} | {r['max_parameters_compute']} | {r['max_parameters_persistent_capacity']} | {r['max_parameters_necessary_conditions']} |")
    if 'training_deadline_rows' in result:
        lines.extend(['', '效率分母严格BF16输入／FP32累加／tensor／dense，每张设备；并非已校准MFU。', '',
                      '| 型号 | 矩阵效率 | 算力张数下界 | 持久容量张数下界 | 两者max | 条件式训练秒 |',
                      '| --- | --- | ---: | ---: | ---: | --- |'])
        for r in result['training_deadline_rows']:
            lines.append(f"| {r['device']} | {r['matrix_work_efficiency_exact']} | {r['compute_count_bound']} | {r['persistent_capacity_count_bound']} | {r['combined_necessary_count']} | {r['conditional_training_seconds_exact']} |")
        lines.extend(['', '| 型号 | 可选状态 | 持久容量张数下界 | 缺项原因 |', '| --- | --- | ---: | --- |'])
        for r in result['training_deadline_devices']:
            lines.append(f"| {r['device']} | {r['status']} | {r['capacity_bound_devices']} | {r.get('reason','已核对精度与单设备范围')} |")
    if 'checkpoint_resume_tensors' in result:
        lines.extend(['', '| 操作 | world | axis | 最大rank API s | 全组局部状态 bytes | 第一权重各rank形状 |', '| --- | ---: | ---: | ---: | ---: | --- |'])
        for r in result['checkpoint_resume_groups']:
            lines.append(f"| {r['mode']} | {r['world']} | {r['axis']} | {r['max_rank_api_seconds']} | {r['sum_rank_local_logical_bytes']} | {r['first_weight_local_shapes']} |")
        lines.extend(['', '| 状态张量 | 全局shape | dtype | 唯一逻辑 bytes | 保存chunk数 |', '| --- | --- | --- | ---: | ---: |'])
        for r in result['checkpoint_resume_tensors']:
            lines.append(f"| {r['name']} | {r['shape']} | {r['dtype']} | {r['logical_bytes']} | {r['chunk_count']} |")
    if 'checkpoint_fault_rows' in result:
        lines.extend(['', '| 分支 | 快照 | API s | stage s | writer s | 调用到commit s | 未完成观察 s | 数据 bytes | metadata bytes | 实际加载成功 |',
                      '| --- | --- | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |'])
        for r in result['checkpoint_fault_rows']:
            lines.append(f"| {r['case']} | {r['checkpoint']} | {r['api_seconds']} | {r['stage_seconds']} | {r['writer_seconds']} | {r['commit_from_call_seconds']} | {r['unfinished_observation_seconds']} | {r['data_file_bytes']} | {r['metadata_bytes']} | {r['actual_load_succeeded']} |")
    if 'checkpoint_baseline_runs' in result:
        lines.extend(['', '真实CPU小模型；各列为分别取中位数，不能相加。none未测项保留null。', '',
                      '| 模式 | 窗口 s | 训练 s | API s | stage s | writer s | 调用到提交 s |',
                      '| --- | ---: | ---: | --- | --- | --- | --- |'])
        for r in result['checkpoint_baseline_modes']:
            lines.append(f"| {r['mode']} | {r['window_seconds']} | {r['training_seconds']} | {r['api_seconds']} | {r['stage_seconds']} | {r['writer_seconds']} | {r['commit_from_call_seconds']} |")
        lines.extend(['', '| trial | 模式 | 顺序 | 窗口 s | 训练 s | 文件 bytes | RSS高水位差 KiB |', '| ---: | --- | ---: | ---: | ---: | ---: | ---: |'])
        for r in result['checkpoint_baseline_runs']:
            lines.append(f"| {r['trial']} | {r['mode']} | {r['execution_order']} | {r['window_seconds']} | {r['training_seconds']} | {r['checkpoint_file_bytes']} | {r['process_rss_highwater_delta_kib']} |")
        lines.extend(['', '| trial | async−none窗口 s | async−none训练 s | sync−async窗口 s |', '| ---: | ---: | ---: | ---: |'])
        for r in result['checkpoint_baseline_pairs']:
            lines.append(f"| {r['trial']} | {r['async_minus_none_window_seconds']} | {r['async_minus_none_training_seconds']} | {r['sync_minus_async_window_seconds']} |")
    if 'checkpoint_interval_rows' in result:
        lines.extend(['', 'tau为新增有用计算秒；近似损失与重试模型的保留比例不能互换。', '',
                      '| tau s | c/tau | lambda*tau/2 | lambda*r | 一阶损失 | 小于1 | Poisson周期期望 s | Poisson保留比例 |',
                      '| ---: | --- | --- | --- | ---: | --- | ---: | ---: |'])
        for r in result['checkpoint_interval_rows']:
            lines.append(f"| {r['useful_interval_seconds']} | {r['save_fraction_exact']} | {r['recompute_fraction_exact']} | {r['recovery_fraction_exact']} | {r['first_order_loss']:.9f} | {r['first_order_loss_below_one']} | {r['poisson_cycle_expected_seconds']:.9f} | {r['poisson_retained_useful_fraction']:.9f} |")
    if 'checkpoint_save_rows' in result:
        lines.extend(['', '以下为无故障计划；故障后的行是反事实。durable才表示本模型声明的可恢复点。', '',
                      '| 快照 | 槽 | 请求 s | 实际capture s | staging完成 s | upload开始 s | upload完成 s | durable s |',
                      '| ---: | ---: | --- | --- | --- | --- | --- | --- |'])
        for row in result['checkpoint_save_rows']:
            t=row['exact_seconds']
            lines.append(f"| {row['snapshot']} | {row['slot']} | {t['requested']} | {t['capture']} | {t['staging_end']} | {t['upload_start']} | {t['upload_end']} | {t['durable']} |")
        lines.extend(['', '| 训练屏障并集起点 s | 终点 s |', '| --- | --- |'])
        for row in result['checkpoint_pause_intervals']:
            lines.append(f"| {row['start_exact_seconds']} | {row['end_exact_seconds']} |")
    if 'checkpoint_component_plans' in result:
        lines.extend(['', '源文件为原始行主序教学布局；偏移相对各文件及目标分片。完整坐标见JSON。', '',
                      '| 状态 | bytes/element | 各源分片 bytes | 各目标分片 bytes |', '| --- | ---: | --- | --- |'])
        for row in result['checkpoint_component_plans']:
            lines.append(f"| {row['component']} | {row['bytes_per_element']} | {row['source_shard_bytes']} | {row['target_shard_bytes']} |")
        lines.extend(['', '| 源文件 | 目标rank | 全局元素区间 [start,end) | 源偏移 bytes | 目标偏移 bytes | 长度 bytes |',
                      '| --- | ---: | --- | ---: | ---: | ---: |'])
        for row in result['checkpoint_component_plans']:
            for p in row['pieces']:
                lines.append(f"| {p['source_file']} | {p['target_rank']} | [{p['global_element_start']},{p['global_element_end']}) | {p['source_file_offset_bytes']} | {p['target_buffer_offset_bytes']} | {p['length_bytes']} |")
    if 'gradient_cast_paths' in result:
        lines.extend(['', '完整梯度串行路径，转换与链路为有效教学吞吐；终点为CPU可消费FP32。', '',
                      '| 转换端 | 就绪 s | D2H bytes | GPU额外峰值 bytes | GPU含源峰值 bytes | 主机峰值 bytes | 缓冲可容纳 |',
                      '| --- | ---: | ---: | ---: | ---: | ---: | --- |'])
        for row in result['gradient_cast_paths']:
            lines.append(f"| {row['cast_location']} | {row['ready_seconds']:.9f} | {row['link_payload_bytes']} | {row['extra_gpu_peak_bytes']} | {row['gpu_peak_including_common_bytes']} | {row['host_peak_bytes']} | {row['specified_buffers_fit']} |")
        lines.extend(['', '| 路径 | 操作 | 起点 s（精确） | 终点 s（精确） | 逻辑访问／载荷 bytes |', '| --- | --- | --- | --- | ---: |'])
        for row in result['gradient_cast_paths']:
            for op in row['operations']:
                lines.append(f"| {row['cast_location']} | {op['name']} | {op['start_exact_seconds']} | {op['end_exact_seconds']} | {op['logical_bytes']} |")
        lines.extend(['', '| 路径 | 所在端 | 缓冲 | 起点 s（含） | 终点 s（交接／释放） | bytes |', '| --- | --- | --- | --- | --- | ---: |'])
        for row in result['gradient_cast_paths']:
            for buf in row['buffers']:
                lines.append(f"| {row['cast_location']} | {buf['tier']} | {buf['name']} | {buf['start_exact_seconds']} | {buf['end_exact_seconds']} | {buf['bytes']} |")
    if 'training_state_stages' in result:
        lines.extend(['', '持久状态与输入的额外同时驻留量；通过容量比较不证明实际训练峰值可行。', '',
                      '| ZeRO stage | 每rank持久 bytes | 全组持久 bytes | 所列同时驻留 bytes | 剩余净预算 bytes | 所列分配能容纳 |',
                      '| ---: | ---: | ---: | ---: | ---: | --- |'])
        for row in result['training_state_stages']:
            lines.append(f"| {row['stage']} | {row['persistent_bytes_per_rank']} | {row['persistent_bytes_cluster']} | {row['specified_live_bytes_per_rank']} | {row['signed_capacity_headroom_bytes']} | {row['specified_allocations_fit']} |")
        lines.extend(['', '| stage | 状态 | bytes/element | 分片 | 每rank bytes | 全组padding bytes | 额外复制 bytes |',
                      '| ---: | --- | ---: | --- | ---: | ---: | ---: |'])
        for row in result['training_state_stages']:
            for item in row['components']:
                lines.append(f"| {row['stage']} | {item['component']} | {item['bytes_per_element']} | {item['sharded']} | {item['per_rank_bytes']} | {item['partition_padding_bytes']} | {item['replicated_extra_bytes']} |")
    if 'residency_tiers' in result:
        lines.extend(['', '驻留区间为教学输入；同层按物理身份取并集，跨层副本独立计费。', '',
                      '| 层 | 容量 bytes | 峰值 bytes | 实体 byte-seconds | 逻辑 byte-seconds | 共享节省 byte-seconds | 超容量 ns |',
                      '| --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['residency_tiers']:
            lines.append(f"| {row['tier']} | {row['capacity_bytes']} | {row['peak_bytes']} | {row['physical_byte_seconds_exact']} | {row['logical_byte_seconds_exact']} | {row['shared_byte_seconds_saved_exact']} | {row['over_capacity_nanoseconds']} |")
        lines.extend(['', '| 起点 ns（含） | 终点 ns（不含） | 各层实体 bytes | 全层实体 bytes | 全局唯一比较 bytes |',
                      '| ---: | ---: | --- | ---: | ---: |'])
        for row in result['residency_segments']:
            lines.append(f"| {row['start_ns']} | {row['end_ns']} | {json.dumps(row['tier_physical_bytes'],sort_keys=True)} | {row['all_tier_physical_bytes']} | {row['globally_unique_page_bytes']} |")
    if 'fault_policy_rows' in result:
        lines.extend(['', '| 策略 | 完成 | 完成秒 | 未完成观测下界秒 | Short read次数 | 异常距请求秒 | 缓存token | 坏页据记录未变 |', '| --- | --- | --- | --- | ---: | ---: | --- | --- |'])
        for row in result['fault_policy_rows']:
            lines.append(f"| {row['policy']} | {row['completed']} | {row['completion_seconds']} | {row['incomplete_observation_lower_seconds']} | {row['short_read_exceptions']} | {row['exception_after_request_seconds']} | {row['cached_tokens']} | {row['corrupt_file_reported_unchanged']} |")
    if 'device_control_comparisons' in result:
        lines.extend(['', '显存分段控制v2：前置512输入、1输出；随后device命中512／1008／1008。', '',
                      '| KV页比较 | 元素数 | 不同BF16元素 | 最大绝对差 |', '| --- | ---: | ---: | ---: |'])
        for row in result['device_control_comparisons']:
            lines.append(f"| {row['comparison']} | {row['elements']} | {row['different_elements']} | {row['max_abs_difference']} |")
    if 'missing_page_cases' in result:
        lines.extend(['', '| 条件 | get页数 | get bytes | 首次复用token | 重算token | 不同BF16元素 | 最大绝对差 |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['missing_page_cases']:
            lines.append(f"| {row['case']} | {row['successful_get_calls']} | {row['get_file_bytes']} | {row['first_reused_tokens']} | {row['first_recomputed_tokens']} | {row['different_bf16_elements']} | {row['max_abs_difference']} |")
        lines.extend(['', '| 条件 | 请求 | 缓存token | 剩余prefill token | prefill FLOPs |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['missing_page_requests']:
            lines.append(f"| {row['case']} | {row['index']} | {row['cached_tokens']} | {row['remaining_prefill_tokens']} | {row['prefill_matrix_flops']} |")
        lines.extend(['', '| 条件 | 层 | K/V不同元素 | 最大绝对差 |', '| --- | ---: | ---: | ---: |'])
        for row in result['missing_page_layers']:
            lines.append(f"| {row['case']} | {row['layer']} | {row['different_elements']} | {row['max_abs_difference']} |")
    if 'restart_requests' in result:
        lines.extend(['', '| 进程 | 请求 | 缓存token | 来源 | 客户端秒 | prefill节省FLOPs |', '| --- | ---: | ---: | --- | ---: | ---: |'])
        for row in result['restart_requests']:
            lines.append(f"| {row['phase']} | {row['index']} | {row['cached_tokens']} | {row['cache_details']} | {row['client_seconds']} | {row['prefill_saved_matrix_flops']} |")
        lines.extend(['', '| 进程 | 方法 | 调用数 | 所指文件bytes | 调用覆盖墙钟秒 |', '| --- | --- | ---: | ---: | ---: |'])
        for row in result['restart_storage_calls']:
            lines.append(f"| {row['phase']} | {row['method']} | {row['calls']} | {row['file_bytes_named']} | {row['wall_span_seconds']} |")
    if 'pressure_requests' in result:
        lines.extend(['', '| 轮次 | 策略 | 缓存token | 目标秒 | 后台秒 | 两任务完成秒 | 采样等待峰值 | 最大采样间隔秒 |', '| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['pressure_requests']:
            lines.append(f"| {row['trial']} | {row['policy']} | {row['cached_tokens']} | {row['target_seconds']} | {row['background_seconds']} | {row['pair_completion_seconds']} | {row['sampled_waiting_peak']} | {row['max_sample_gap_seconds']} |")
        lines.extend(['', '| 轮次 | queue-first目标节省秒 | 两任务增加秒 | 后台增加秒 |', '| ---: | ---: | ---: | ---: |'])
        for row in result['pressure_pairs']:
            lines.append(f"| {row['trial']} | {row['target_seconds_saved_by_queue_first']} | {row['pair_completion_seconds_added_by_queue_first']} | {row['background_seconds_added_by_queue_first']} |")
    if 'router_policy_rows' in result:
        lines.extend(['', '| 策略 | 输入token | 缓存token | token命中率 | 命中请求 | 客户端中位秒 | 节省矩阵FLOPs |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['router_policy_rows']:
            lines.append(f"| {row['policy']} | {row['prompt_tokens']} | {row['cached_tokens']} | {row['token_weighted_hit_rate']} | {row['hit_requests']}/12 | {row['client_median_s']} | {row['saved_matrix_flops']} |")
        lines.extend(['', '| 输入轮次 | worker | 输入token | 缓存token | 客户端秒 | 命中后逻辑FLOPs |', '| ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['router_request_rows']:
            lines.append(f"| {row['prompt_id']} | {row['worker']} | {row['prompt_tokens']} | {row['cached_tokens']} | {row['client_elapsed_s']} | {row['executed_logical_matrix_flops']} |")
    if 'cache_route_paths' in result:
        lines.extend(['', '| 路径 | GPU等待ns | 状态取回耗时ns | 首token ns |', '| --- | ---: | --- | --- |'])
        for row in result['cache_route_paths']:
            lines.append(f"| {row['path']} | {row['queue_ns']} | {row['ready_ns_exact']} | {row['finish_ns_exact']} |")
    if 'replica_service_rows' in result:
        lines.extend(['', '| 部署 | rank | 矩阵服务ns | 指定接口服务ns | rank服务ns |', '| --- | ---: | --- | --- | --- |'])
        for row in result['replica_service_rows']:
            lines.append(f"| {row['deployment']} | {row['rank']} | {row['compute_ns_exact']} | {row['interface_ns_exact']} | {row['service_ns_exact']} |")
    if 'grouped_rank_rows' in result:
        lines.extend(['', '| rank | 非空物理副本 | token—专家任务 | 有效FLOPs | 完全补齐FLOPs | 权重tile读取bytes | 接口总bytes |', '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['grouped_rank_rows']:
            lines.append(f"| {row['rank']} | {row['active_experts']} | {row['token_expert_tasks']} | {row['valid_matrix_flops']} | {row['padded_matrix_flops']} | {row['weight_read_bytes']} | {row['next_level_bytes']} |")
        lines.extend(['', '| 逻辑专家 | 物理副本 | rank | 有效M | 补齐M |', '| ---: | ---: | ---: | ---: | ---: |'])
        for row in result['grouped_expert_rows']:
            lines.append(f"| {row['expert']} | {row['physical_copy']} | {row['rank']} | {row['tokens']} | {row['padded_token_rows']} |")
    if 'locality_reuse_regions' in result:
        lines.extend(['', '单个非驻留专家的精确整数复用区间（能力与格式保持不变）：', '',
                      '| 每专家最少token | 最多token（null为无穷） | 声明模型较小服务时间 |', '| ---: | --- | --- |'])
        for row in result['locality_reuse_regions']:
            lines.append(f"| {row['min_tokens_per_expert']} | {row['max_tokens_per_expert']} | {row['winner']} |")
        lines.extend(['', '计算／权重读取等时位置：`'+json.dumps(result['reuse_knees'],ensure_ascii=False)+'`。'])
    if 'locality_paths' in result:
        lines.extend(['', '| 非驻留专家路径 | 链路bytes | 启动数 | 权重读取bytes | 矩阵FLOPs | 声明模型ns |', '| --- | ---: | ---: | ---: | ---: | --- |'])
        for row in result['locality_paths']:
            lines.append(f"| {row['name']} | {row['link_bytes']} | {row['launches']} | {row['memory_weight_bytes']} | {row['matrix_flops']} | {row['service_ns_exact']} |")
        lines.extend(['', '| 专家 | token数 | GPU驻留 | gate/up M,K,N | down M,K,N | 矩阵FLOPs | 本批权重bytes |', '| ---: | ---: | --- | --- | --- | ---: | ---: |'])
        for row in result['locality_experts']:
            lines.append(f"| {row['expert']} | {row['tokens']} | {row['gpu_resident']} | {row['gate_up_shape']} | {row['down_shape']} | {row['matrix_flops']} | {row['weight_read_bytes']} |")
    if 'pool_assignments' in result:
        lines.extend(['', '| worker类型 | 副本数 | 每请求P资源秒 | 每请求D资源秒 | 单副本共置请求/s |', '| --- | ---: | --- | --- | --- |'])
        for row in result['pool_worker_rates']:
            lines.append(f"| {row['name']} | {row['count']} | {row['prefill_service_seconds_exact']} | {row['decode_service_seconds_exact']} | {row['colocated_requests_per_second_exact']} |")
        lines.extend(['', '| P分配 | D分配 | P请求/s | D请求/s | 联合上界请求/s | 限制资源 | 到达率严格低于上界 |', '| --- | --- | --- | --- | --- | --- | --- |'])
        for row in result['pool_assignments']:
            lines.append(f"| {row['prefill_workers']} | {row['decode_workers']} | {row['prefill_requests_per_second_exact']} | {row['decode_requests_per_second_exact']} | {row['bound_requests_per_second_exact']} | {row['bottlenecks']} | {row['strictly_below_all_capacity_bounds']} |")
    if 'handoff_cases' in result:
        lines.extend(['', '| 交接 | payload bytes | 消息数 | 接口 | 接口bytes | 启动次数 | 载荷ns | 启动ns |', '| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |'])
        for case in result['handoff_cases']:
            for row in case['resource_demands']:
                lines.append(f"| {case['name']} | {case['payload_bytes']} | {case['messages']} | {row['resource']} | {row['transmitted_bytes']} | {row['launches']} | {row['payload_ns_exact']} | {row['startup_ns']} |")
        lines.extend(['', '| 消息缓冲 | 源GPU bytes | 目的GPU bytes | 源host bytes | 目的host bytes |', '| --- | ---: | ---: | ---: | ---: |'])
        for name,row in result['endpoint_buffers'].items():
            lines.append(f"| {name} | {row['source_gpu_live_bytes']} | {row['destination_gpu_live_bytes']} | {row['source_host_staging_bytes']} | {row['destination_host_staging_bytes']} |")
    if 'kv_quality_conditions' in result:
        lines.extend(['', '| 文档行 | 并发 | 模式 | 正确／请求 | 输出token | 自然截断 | 中位完成秒 | 批次窗口秒 | 输出token/s |', '| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: |'])
        for row in result['kv_quality_conditions']:
            lines.append(f"| {row['document_rows']} | {row['concurrency']} | {row['mode']} | {row['correct']}/{row['requests']} | {row['output_tokens']} | {row['natural_truncated']} | {row['median_latency_s']} | {row['batch_window_s']} | {row['output_tokens_per_s']} |")
    if 'offload_copies' in result:
        lines.extend(['', '| pass／层 | 槽 | 复制开始ns | 复制结束ns | 消费开始ns | 消费结束ns |', '| --- | ---: | --- | --- | --- | --- |'])
        for row in result['offload_copies']:
            lines.append(f"| {row['pass_index']}/{row['layer']} | {row['slot']} | {row['copy_start_ns_exact']} | {row['copy_end_ns_exact']} | {row['consume_start_ns_exact']} | {row['consume_end_ns_exact']} |")
    if 'kv_codec_rows' in result:
        lines.extend(['', '| 格式 | 历史bytes | scale bytes | 追加bytes | 融合总ns | 物化总ns | 融合省ns | 长历史持续获益起点 |', '| --- | ---: | ---: | ---: | --- | --- | --- | --- |'])
        for row in result['kv_codec_rows']:
            lines.append(f"| {row['format']} | {row['history_resident_bytes']} | {row['history_scale_bytes']} | {row['next_token_append_bytes']} | {row['fused_ns_exact']} | {row['materialized_ns_exact']} | {row['fused_saving_ns_exact']} | {row['strict_fused_crossover_length']} |")
    if 'gguf_types' in result:
        lines.extend(['', '| 实际类型 | 张量数 | 元素数 | 块元素／bytes | 码值或浮点bytes | 块尺度元数据bytes | 总载荷bytes |', '| --- | ---: | ---: | --- | ---: | ---: | ---: |'])
        for row in result['gguf_types']:
            lines.append(f"| {row['type']} | {row['tensors']} | {row['elements']} | {row['block_elements']}/{row['block_bytes']} | {row['code_or_float_bytes']} | {row['scale_metadata_bytes']} | {row['payload_bytes']} |")
        lines.extend(['', '| 分片 | 文件bytes | header bytes | header对齐bytes | 张量载荷bytes | 张量padding bytes |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['gguf_shards']:
            lines.append(f"| {row['path']} | {row['file_bytes']} | {row['header_bytes']} | {row['header_alignment_bytes']} | {row['tensor_payload_bytes']} | {row['tensor_padding_bytes']} |")
    if 'gguf_variants' in result:
        lines.extend(['', '| 变体 | 分片 | 总文件bytes | 总文件GiB | 文件后剩余预算bytes | 可容纳独立BF16 KV请求 |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['gguf_variants']:
            lines.append(f"| {row['variant']} | {row['shards']} | {row['file_bytes']} | {row['file_gib']} | {row['budget_after_files_bytes']} | {row['max_independent_bf16_kv_requests']} |")
        lines.extend(['', '| GGUF分片 | 发布文件bytes | 发布LFS SHA256 |', '| --- | ---: | --- |'])
        for variant in result['gguf_variants']:
            for row in variant['shard_files']:
                lines.append(f"| {row['path']} | {row['file_bytes']} | {row['lfs_sha256']} |")
    if 'service_requests' in result:
        lines.extend(['', '| 轮／请求 | 客户端TTFT ms | 客户端E2E ms | 客户端平均TPOT ms | 引擎排队ms | 联合计时达标 |', '| --- | ---: | ---: | ---: | ---: | --- |'])
        for row in result['service_requests']:
            lines.append(f"| {row['trial']}/{row['id']} | {row['delivered_ttft_ms']} | {row['delivered_e2e_ms']} | {row['delivered_mean_tpot_ms']} | {row['engine_queue_ms']} | {row['joint_timing_pass']} |")
        lines.extend(['', '| 轮 | 实际观测窗秒 | 达标请求 | timing goodput请求/秒 |', '| ---: | ---: | ---: | ---: |'])
        for row in result['service_trials']:
            lines.append(f"| {row['trial']} | {row['window_s']} | {row['timing_passed']} | {row['timing_goodput_requests_per_s']} |")
    if 'batching_requests' in result:
        lines.extend(['', '| 请求 | 准入ns | TTFT ns | 完成ns | 最大ITL ns | 矩阵FLOPs |', '| --- | ---: | ---: | ---: | --- | ---: |'])
        for row in result['batching_requests']:
            lines.append(f"| {row['id']} | {row['admitted_ns']} | {row['ttft_ns']} | {row['finish_ns']} | {row['max_itl_ns']} | {row['matrix_flops']} |")
        lines.extend(['', '| 步开始ns | 步结束ns | 新token | 有效配对 | 步内KV bytes | 请求／阶段／新token |', '| ---: | ---: | ---: | ---: | ---: | --- |'])
        for row in result['batching_steps']:
            plans=', '.join(f"{p['request']}:{p['phase']}:{p['new_tokens']}" for p in row['plans'])
            lines.append(f"| {row['start_ns']} | {row['end_ns']} | {row['new_tokens']} | {row['causal_pairs']} | {row['live_kv_bytes_during_step']} | {plans} |")
    if 'batch_reuse_rows' in result:
        lines.extend(['', '| batch | 矩阵FLOPs | 旧KV读bytes | 总声明流量bytes | 省权重读bytes | 声明驻留bytes | 容量可行 | 资源主导 |', '| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |'])
        for row in result['batch_reuse_rows']:
            lines.append(f"| {row['batch']} | {row['matrix_flops']} | {row['kv_history_read_bytes']} | {row['declared_traffic_bytes']} | {row['saved_weight_read_bytes']} | {row['declared_resident_bytes']} | {row['capacity_feasible']} | {row['dominant_resource']} |")
    if 'chunk_history_rows' in result:
        lines.extend(['', '| 历史token | 新token | 有效因果配对 | backbone矩阵FLOPs | 区间中位ms | 最小ms | 最大ms |', '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['chunk_history_rows']:
            lines.append(f"| {row['history_tokens']} | {row['new_tokens']} | {row['causal_pairs']} | {row['backbone_matrix_flops']} | {row['median_ms']} | {row['min_ms']} | {row['max_ms']} |")
    if 'draft_matrices' in result:
        lines.extend(['', '| 算子 | M | K | N | 实例数 | 矩阵FLOPs | 每实例BF16逻辑operand bytes |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['draft_matrices']:
            lines.append(f"| {row['operator']} | {row['m']} | {row['k']} | {row['n']} | {row['count']} | {row['matrix_flops']} | {row['logical_operand_bytes_per_instance']} |")
    if 'budget_policies' in result:
        lines.extend(['', '| 策略 | 期望完成ns | 期望轮数 | 期望草稿数 | 期望截断产出 | 使用准备概率 |', '| --- | --- | --- | --- | --- | --- |'])
        for row in result['budget_policies']:
            lines.append(f"| {row['policy']} | {row['expected_ns_exact']} | {row['expected_rounds_exact']} | {row['expected_drafted_tokens_exact']} | {row['expected_clipped_tokens_exact']} | {row['preparation_probability_exact']} |")
        lines.extend(['', '| 剩余输出 | 已准备 | 选择 | 期望剩余ns |', '| ---: | --- | --- | --- |'])
        for row in result['budget_states']:
            lines.append(f"| {row['remaining_tokens']} | {row['prepared']} | {row['selected']} | {row['expected_ns_exact']} |")
    if 'sampling_tokens' in result:
        lines.extend(['', '| token | 目标 p | 草稿 q | 条件接受 | 接受质量 | 拒绝修正分布 | 正确输出 | 错误输出 |', '| ---: | --- | --- | --- | --- | --- | --- | --- |'])
        for row in result['sampling_tokens']:
            lines.append(f"| {row['token']} | {row['target_exact']} | {row['draft_exact']} | {row['conditional_accept_exact']} | {row['accepted_mass_exact']} | {row['residual_exact']} | {row['output_exact']} | {row['wrong_output_exact']} |")
    if 'speculative_outcomes' in result:
        lines.extend(['', '| 接受草稿 | 次数 | 实际交付 | 保留新增KV bytes | 丢弃新增KV bytes | 匹配串行FLOPs |', '| ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['speculative_outcomes']:
            lines.append(f"| {row['accepted_drafts']} | {row['count']} | {row['delivered_tokens']} | {row['target_new_kv_kept_bytes']} | {row['target_new_kv_discarded_bytes']} | {row['baseline_matrix_flops']} |")
    if 'apc_rounds' in result:
        lines.extend(['', '| 轮 | 输入token | 命中token | 剩余矩阵 FLOPs | 省下矩阵 FLOPs | 实测TTFT秒 |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['apc_rounds']:
            lines.append(f"| {row['id']} | {row['prompt_tokens']} | {row['cached_tokens']} | {row['hit_matrix_flops']} | {row['saved_matrix_flops']} | {row['delivery_ttft_s']} |")
    if 'prefix_candidates' in result:
        lines.extend(['', '| 前缀 | 常驻 bytes | 完整矩阵 FLOPs | 命中后矩阵 FLOPs | 预期节省 FLOPs |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['prefix_candidates']:
            lines.append(f"| {row['id']} | {row['resident_bytes']} | {row['full_matrix_flops']} | {row['hit_matrix_flops']} | {row['expected_saved_matrix_flops_exact']} |")
    if 'restore_policies' in result:
        lines.extend(['', '| 策略 | 容量可行 | 恢复等待 ns | KV释放时长 ns | 搬运 bytes | 重算矩阵 FLOPs |', '| --- | --- | ---: | ---: | ---: | ---: |'])
        for row in result['restore_policies']:
            lines.append(f"| {row['policy']} | {row['feasible']} | {row['stall_exact_ns']} | {row['kv_free_interval_exact_ns']} | {row['transfer_bytes']} | {row['replayed_matrix_flops']} |")
    if 'kv_page_events' in result:
        lines.extend(['', '| 事件 | 操作 | 接纳 | 逻辑 bytes | 唯一有效 bytes | 分配 bytes | 空位 bytes | COW bytes |', '| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['kv_page_events']:
            lines.append(f"| {row['event']} | {row['operation']} | {row['accepted']} | {row['logical_request_bytes']} | {row['unique_live_bytes']} | {row['allocated_page_bytes']} | {row['unused_page_bytes']} | {row['copied_valid_bytes']} |")
    if 'rpc_groups' in result:
        lines.extend(['', '| 实测模式 | 总时间中位 ns | CPU中位 ns | 总时间p95 ns |', '| --- | ---: | ---: | ---: |'])
        for row in result['rpc_groups']:
            lines.append(f"| {row['name']} | {row['medians_ns']['total_ns']} | {row['medians_ns']['client_cpu_ns']} | {row['total_p95_ns']} |")
        lines.extend(['', '| 阶段中位数 ns | JSON worker | binary copy | binary view | inline |', '| --- | ---: | ---: | ---: | ---: |'])
        for field in result['rpc_groups'][0]['medians_ns']:
            values = ' | '.join(str(row['medians_ns'][field]) for row in result['rpc_groups'])
            lines.append(f"| {field} | {values} |")
        lines.extend(['', '| 配对修改 | 差的中位 ns | 两中位数之差 ns | 变快轮数/20 |', '| --- | ---: | ---: | ---: |'])
        for row in result['rpc_pairs']:
            lines.append(f"| {row['before']} → {row['after']} | {row['median_saved_ns']} | {row['median_difference_ns']} | {row['positive_pairs']} |")
    if 'completion_operations' in result:
        lines.extend(['', '| 操作 | 槽位 | 提交 ns | 传输完成 ns | 消费回收 ns |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['completion_operations']:
            lines.append(f"| {row['operation']} | {row['slot']} | {row['submit_ns']} | {row['transfer_complete_ns']} | {row['completion_consumed_ns']} |")
    if 'stale_read_example' in result:
        lines.extend(['', '| 取值／交付事件 | 时间 ns | 值 |', '| --- | ---: | ---: |'])
        for row in sorted(result['stale_read_example']['events'],key=lambda row:row['time_ns']):
            lines.append(f"| {row['event']} | {row['time_ns']} | {row['value']} |")
    if 'completion_policies' in result:
        lines.extend(['', '| 策略 | 平均 ns | p50 ns | p99 ns | max ns |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['completion_policies']:
            lines.append(f"| {row['policy']} | {row['mean_exact_ns']} | {row['p50_exact_ns']} | {row['p99_exact_ns']} | {row['max_exact_ns']} |")
    if 'receive_events' in result:
        lines.extend(['', '| 到达 ns（精确） | 到达序号 | 释放序号 | 保留 bytes |', '| ---: | --- | --- | ---: |'])
        for row in result['receive_events']:
            lines.append(f"| {row['time_exact_ns']} | {row['arrived']} | {row['released']} | {row['retained_bytes']} |")
    if 'queue_segments' in result:
        lines.extend(['', '| 开始 ms | 结束 ms | 到达 GB/s | 初始队列 MB | 末尾队列 MB | 丢弃 bytes |', '| ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['queue_segments']:
            lines.append(f"| {row['start_ns']/10**6:.6f} | {row['end_ns']/10**6:.6f} | {row['arrival_bytes_per_second']/10**9:.6f} | {row['queue_start_bytes']/10**6:.6f} | {row['queue_end_bytes']/10**6:.6f} | {row['dropped_exact_bytes']} |")
    if 'collective_path_patterns' in result:
        lines.extend(['', '| 路径模式 | 轮 | 消息 bytes | 跳数 | 峰值链路消息 | 峰值链路 bytes | 全网物理 bytes | 下界 us |', '| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |'])
        for pattern in result['collective_path_patterns']:
            for row in pattern['rounds']:
                lines.append(f"| {pattern['pattern']} | {row['round']} | {row['message_bytes']} | {row['hops_per_message']} | {row['peak_link_messages']} | {row['peak_link_bytes']} | {row['physical_link_bytes']} | {row['serialization_lower_seconds']*10**6:.6f} |")
        lines.extend(['', '完整逐消息路径及有向链路计数保留在同名JSON。'])
    if 'placement_patterns' in result:
        lines.extend(['', '| 空闲分布 | 空闲数 | 候选窗口数 | 最多同时作业 | 选中单元 |', '| --- | ---: | ---: | ---: | --- |'])
        for name,row in result['placement_patterns'].items():
            lines.append(f"| {name} | {len(row['free_cells'])} | {len(row['candidate_windows'])} | {row['maximum_simultaneous_allocations']} | {[w['cells'] for w in row['selected_windows']]} |")
    if 'microbatch_rows' in result:
        lines.extend(['', '| 微批 tokens | 矩阵 FLOPs | 无缓存完整权重读取 bytes |', '| ---: | ---: | ---: |'])
        for row in result['microbatch_rows']:
            lines.append(f"| {row['tokens']} | {row['matrix_flops']} | {row['weight_read_once_bytes']} |")
    if 'request_schedules' in result:
        for name,schedule in result['request_schedules'].items():
            lines.extend(['', name, '', '| 节点 | 资源 | 开始 ns | 完成 ns | 限制前序 |', '| --- | --- | ---: | ---: | --- |'])
            for row in schedule['tasks']:
                lines.append(f"| {row['id']} | {row['resource']} | {row['start_ns']} | {row['end_ns']} | {row['critical_predecessor']} |")
    if 'persistent_tiles' in result:
        lines.extend(['', '| 块 | 行数 | 生产开始 us | 数据就绪 us | 消费开始 us | 消费完成 us |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['persistent_tiles']:
            t=row['nanoseconds']
            lines.append(f"| {row['tile']} | {row['rows']} | {t['producer_start']/1000:.6f} | {t['producer_ready']/1000:.6f} | {t['consumer_start']/1000:.6f} | {t['consumer_done']/1000:.6f} |")
    if 'runtime_timings' in result:
        lines.extend(['', '| 方案 | 微批数 | 中位 us | 最小 us | 最大 us | 主机提交中位 us | 张量 bytes |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['runtime_timings']:
            lines.append(f"| {row['label']} | {row['chunks']} | {row['measured_median_us']:.6f} | {row['measured_min_us']:.6f} | {row['measured_max_us']:.6f} | {row['host_submit_median_us']:.6f} | {row['live_io_intermediate_bytes']} |")
        if result['runtime_ranges']:
            lines.extend(['', '| Nsight范围 | 主机启动 | 图启动 | kernel数 | 设备活动并集 ns | 未覆盖 ns |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
            for row in result['runtime_ranges']:
                lines.append(f"| {row['label']} | {row['launch_api_count']} | {row['graph_launch_count']} | {row['kernel_count']} | {row['captured_activity_union_ns']} | {row['uncovered_device_interval_ns']} |")
        lines.extend(['', '另列MPK作者结果与环境：`'+json.dumps(result['paper_comparison'],ensure_ascii=False)+'`'])
    if 'specialization_policies' in result:
        lines.extend(['', '| 策略 | 准备 ms | 每频数组 ms | 含准备总计 ms | 补齐 FLOPs | 回退调用数 |', '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['specialization_policies']:
            lines.append(f"| {row['policy']} | {row['prepare_ns']/10**6} | {row['cohort_execution_ns']/10**6} | {row['lifetime_ns']/10**6} | {row['cohort_padding_flops']} | {row['fallback_calls']} |")
        for row in result['specialization_policies']:
            lines.extend(['', row['policy']+'工件与映射：`'+json.dumps(dict(artifacts=row['artifacts'],shapes=row['shape_mapping']),ensure_ascii=False)+'`', ''])
        lines.extend(['', '精确交叉条件：`'+json.dumps(result['specialization_crossings'],ensure_ascii=False)+'`'])
    if 'deployment_candidates' in result:
        lines.extend(['', '| 候选 | 形状等权平均比值 | 频数加权平均 ns | 回退调用数 |', '| --- | ---: | ---: | ---: |'])
        for row in result['deployment_candidates']:
            lines.append(f"| {row['candidate']} | {row['shape_mean_ratio']} | {row['mean_execution_ns']} | {row['fallback_calls']} |")
        lines.extend(['', '| 形状 | 调用数 | 选择 | 含分派 ns |', '| --- | ---: | --- | ---: |'])
        for row in result['deployment_selections']:
            lines.append(f"| {row['shape']} | {row['count']} | {row['selected']} | {row['deployed_execution_ns']} |")
        if result['crossover']:
            lines.extend(['', '两形状交叉条件：`'+json.dumps(result['crossover'],ensure_ascii=False)+'`'])
    if 'graph_paths' in result:
        lines.extend(['', '| 路径 | 每次 us | 含准备总计 ms | 不亏调用数 | 严格更快调用数 |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['graph_paths']:
            lines.append(f"| {row['path']} | {row['execution_ns']/1000:.6f} | {row['lifetime_total_ns']/10**6:.6f} | {row['break_even_calls']} | {row['strictly_faster_calls']} |")
        lines.extend(['', '| 配置流水变体 | 串行 us | 重叠含填充排空 us |', '| --- | ---: | ---: |'])
        for row in result['configuration_pipeline']:
            lines.append(f"| {row['variant']} | {row['serial_total_ns']/1000:.6f} | {row['overlapped_total_ns']/1000:.6f} |")
    if 'fifo_schedules' in result:
        for name, schedule in result['fifo_schedules'].items():
            if schedule is None:
                continue
            lines.extend(['', name+'：教学时间格，同格先取走再发布。', '', '| 时间格 | 事件 | 块 | FIFO占用块数 |', '| ---: | --- | ---: | ---: |'])
            for event in schedule['timeline']:
                lines.append(f"| {event['tick']} | {event['event']} | {event['block']} | {event['occupied_slots']} |")
    if 'transfer_blocks' in result:
        lines.extend(['', '| 块 | 主机槽 | 设备槽 | 准备开始 ms | H2D开始 ms | H2D完成 ms | 消费完成 ms |', '| --- | --- | --- | ---: | ---: | ---: | ---: |'])
        for row in result['transfer_blocks']:
            t=row['seconds']
            lines.append(f"| {row['block']} | {row['host_slot']} | {row['device_slot']} | {t['prepare_start']*1000:.6f} | {t['copy_start']*1000:.6f} | {t['copy_end']*1000:.6f} | {t['consume_end']*1000:.6f} |")
    if 'attention_tile_rows' in result:
        lines.extend(['', '| b | a | 可放 | 接口 bytes | 块对更新 | 旧输出缩放乘法 |', '| --- | --- | --- | ---: | ---: | ---: |'])
        for row in result['attention_tile_rows']:
            lines.append(f"| {row['kv_block']} | {row['query_block']} | {row['feasible']} | {row.get('interface_bytes')} | {row.get('kv_block_pairs')} | {row.get('old_output_scale_multiplications')} |")
    if 'softmax_blocks' in result:
        lines.extend(['', '| 块 | 位置数 | 有效状态 | 块输出 | 前缀合并输出 |', '| --- | ---: | --- | --- | --- |'])
        for row in result['softmax_blocks']:
            lines.append(f"| {row['block']} | {row['size']} | {row['valid']} | {row['standalone_output']} | {row['prefix_output']} |")
    if 'quantization_schedules' in result:
        lines.extend(['', '| 方案 | 主张量 bytes | scale写 bytes | scale读 bytes | 使用最终行尺度 |', '| --- | ---: | ---: | ---: | --- |'])
        for row in result['quantization_schedules']:
            lines.append(f"| {row['name']} | {row['main_tensor_interface_bytes']} | {row['scale_write_bytes']} | {row['scale_read_bytes']} | {row['uses_final_full_row_scale']} |")
    if 'fusion_variants' in result:
        lines.extend(['', '| 物化边界（算子编号） | 接口 bytes | 节省 bytes | 张量峰值 bytes |', '| --- | ---: | ---: | ---: |'])
        for row in result['fusion_variants']:
            lines.append(f"| {row['boundaries']} | {row['interface_bytes']} | {row['saved_interface_bytes']} | {row['declared_tensor_peak_bytes']} |")
        lines.append('逐组输入／输出、阶段内活跃集合及阶段后释放列表完整保存在 JSON。')
    if 'loop_access_rows' in result:
        lines.extend(['', '| 方法 | tile | A读 | B读 | C读 | C更新 | C清零 | 源码bytes | 实测中位 μs |', '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['loop_access_rows']:
            lines.append(f"| {row['method']} | {row['tile']} | {row['a_array_reads']} | {row['b_array_reads']} | {row['c_array_reads']} | {row['c_update_writes']} | {row['c_zeroed_elements']} | {row['source_array_bytes']} | {row['measured_median_us']} |")
    if 'bank_rows' in result:
        lines.extend(['', '| bank | lanes | 不同字 | 服务请求 | 轮数 |', '| --- | --- | ---: | ---: | ---: |'])
        for row in result['bank_rows']:
            lines.append(f"| {row['bank']} | {row['lanes']} | {row['distinct_words']} | {row['service_requests']} | {row['rounds']} |")
    if 'reduction_variants' in result:
        lines.extend(['', '| 策略 | 总组数 | launches | 接口 bytes | 辅助缓冲 bytes |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['reduction_variants']:
            lines.append(f"| {row['name']} | {row['groups']} | {row['launches']} | {row['interface_bytes']} | {row['declared_auxiliary_bytes']} |")
    if 'gemm_tile_rows' in result:
        lines.extend(['', '| m/k/n | 容量 bytes | 下一层 bytes | partial 读+写 bytes | 可放 |', '| --- | ---: | ---: | ---: | --- |'])
        for row in result['gemm_tile_rows']:
            lines.append(f"| {row['tile_m']}/{row['tile_k']}/{row['tile_n']} | {row['reserved_working_bytes']} | {row['next_level_bytes']} | {row['partial_store_bytes']+row['partial_load_bytes']} | {row['fits_capacity']} |")
    if 'audio_chunks' in result:
        lines.extend(['', '| 块 | 到达 ns | 固定截止 ns | 播放 ns | 新增停顿 ns |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['audio_chunks']:
            lines.append(f"| {row['chunk']} | {row['arrival_ns']} | {row['deadline_ns']} | {row['playback_start_ns']} | {row['new_stall_ns']} |")
    if 'agent_rounds' in result:
        lines.extend(['', '| 轮 | 输入 | 命中 | 输出 | 模型墙钟 s | 工具墙钟 s | 冷/命中 prefill FLOPs |', '| --- | ---: | ---: | ---: | ---: | ---: | --- |'])
        for row in result['agent_rounds']:
            lines.append(f"| {row['turn']} | {row['prompt_tokens']} | {row['cached_tokens']} | {row['output_tokens']} | {row['measured_model_seconds']:.6f} | {row['measured_tool_seconds']:.6f} | {row['cold_prefill_matrix_flops']} / {row['cached_prefill_matrix_flops']} |")
    if 'request_rows' in result:
        lines.extend(['', '| 请求 | worker | 开始 ns | 完成 ns | 等待 ns | TTFT ns | 最后 KV bytes |', '| --- | --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['request_rows']:
            lines.append(f"| {row['request']} | {row['worker']} | {row['start_ns']} | {row['finish_ns']} | {row['waiting_ns']} | {row['ttft_ns']} | {row['final_kv_bytes']} |")
        lines.append('逐请求矩阵工作与完整 KV 存活时间线见 JSON。')
    if 'service_stages' in result:
        lines.extend(['', '| 阶段 | 资源池 | 稳态服务需求 s | 孤立批次 s |', '| --- | --- | ---: | ---: |'])
        for row in result['service_stages']:
            lines.append(f"| {row['stage']} | {row['pool']} | {row['service_seconds']:.9f} | {row['isolated_batch_seconds']:.9f} |")
        lines.extend(['', '| 池 | 累积服务需求 s |', '| --- | ---: |'])
        for pool, seconds in result['pool_service_seconds'].items():
            lines.append(f"| {pool} | {seconds:.9f} |")
    if 'rl_stages' in result:
        lines.extend(['', '| 阶段 | 样本 | 次数 | 矩阵 FLOPs |', '| --- | ---: | ---: | ---: |'])
        for row in result['rl_stages']:
            lines.append(f"| {row['name']} | {row['samples']} | {row['passes']} | {row['matrix_flops']} |")
    if 'training_matrix_rows' in result:
        lines.extend(['', '| 矩阵 | 重复 | 单次前向 FLOPs | 每个梯度 FLOPs | 训练矩阵总 FLOPs |', '| --- | ---: | ---: | ---: | ---: |'])
        for row in result['training_matrix_rows']:
            lines.append(f"| {row['name']} | {row['repeats']} | {row['forward_flops']} | {row['gradient_each_flops']} | {row['training_matrix_flops']} |")
        lines.extend(['', '每项包含两个梯度，形状与梯度名称见 JSON；参数状态按声明格式分列：', '', '| 状态 | bytes |', '| --- | ---: |'])
        for name, value in result['parameter_state_bytes'].items():
            lines.append(f"| {name} | {value} |")
    if 'pipeline_operations' in result:
        lines.extend(['', '| step | 微批 | 阶段 | ready ns | start ns | end ns |', '| --- | --- | --- | ---: | ---: | ---: |'])
        for row in result['pipeline_operations']:
            lines.append(f"| {row['step']} | {row['microbatch']} | {row['stage']} | {row['ready_ns']} | {row['start_ns']} | {row['end_ns']} |")
        lines.extend(['', '| 阶段 | busy ns | idle ns | 利用率 |', '| --- | ---: | ---: | ---: |'])
        for row in result['stage_utilization']:
            lines.append(f"| {row['stage']} | {row['busy_ns']} | {row['idle_ns']} | {row['utilization']:.6f} |")
        lines.extend(['', '传输起止、微批完成序列及双端边界缓冲见 JSON；未将边界缓冲当作完整工作区。'])
    if 'communication_operations' in result:
        lines.extend(['', '| 操作 | PP | 层 | 轮次 | 每副本网络发送 bytes | 模型 μs |', '| --- | ---: | --- | ---: | ---: | ---: |'])
        for row in result['communication_operations']:
            lines.append(f"| {row['name']} | {row['stage']} | {row['layer']} | {row['rounds']} | {row['network_send_bytes_per_replica']} | {row['modeled_seconds']*1e6:.6f} |")
    if 'placement_cards' in result:
        lines.extend(['', '| DP / PP / TP | 层 | Q heads | KV heads | 权重 bytes | KV bytes | 总预算占用 bytes | 可容纳 |',
                      '| --- | --- | --- | --- | ---: | ---: | ---: | --- |'])
        for row in result['placement_cards']:
            lines.append(f"| {row['replica']} / {row['stage']} / {row['tp_rank']} | {row['layer_ids']} | {row['query_head_ids']} | {row['kv_head_ids']} | {row['weight_bytes']} | {row['kv_bytes']} | {row['resident_bytes']} | {row['fits_declared_budget']} |")
        lines.extend(['', '逐卡权重矩阵形状、copies、矩阵工作及 TP／PP 消息见 JSON。工作区为显式预算，非实际峰值。'])
    if 'capacity_comparisons' in result:
        lines.extend(['', '| 矩阵位宽 | 预算 GB | 权重 bytes | 工作区 bytes | 每请求 KV bytes | 权重及工作区够放 | 最大并发 |',
                      '| --- | ---: | ---: | ---: | ---: | --- | ---: |'])
        for row in result['capacity_comparisons']:
            lines.append(f"| {row['matrix_bits']} | {row['capacity_bytes']/1e9:g} | {row['weight_bytes']} | {row['workspace_bytes']} | {row['kv_bytes_per_request']} | {row['weights_and_workspace_fit']} | {row['maximum_requests']} |")
        lines.extend(['', '矩阵逐行打包与 scale 元数据分项：', '', '| 位宽 | 参数载荷 bytes | scale bytes |', '| --- | ---: | ---: |'])
        for row in result['storage_formats']:
            lines.append(f"| {row['matrix_bits']} | {row['payload_bytes']} | {row['scale_bytes']} |")
        lines.extend(['', '逐权重形状、copies 和打包字节见 JSON；并发只在声明工作区预算下成立。'])
    if 'dedup_variants' in result:
        lines.extend(['', '| 源 rank | 按 assignment 的目的计数 | 按 token 去重的目的计数 |', '| --- | --- | --- |'])
        for rank, row in enumerate(result['assignment_counts']):
            lines.append(f"| {rank} | {row} | {result['destination_token_counts'][rank]} |")
        lines.extend(['', '归约工作转移：`' + json.dumps(result['reduction_placement']) + '`；逐 token 专家身份见 JSON。'])
    if 'physical_traffic' in result:
        lines.extend(['', '| GPU 发送 → 接收 | 缓冲 NUMA | 依次经过的资源（重复项表示重复服务） |', '| --- | --- | --- |'])
        for path in result['physical_paths']:
            lines.append(f"| {path['sender_gpu']} → {path['receiver_gpu']} | {path['buffer_numa']} | {' → '.join(path['resources'])} |")
        lines.extend(['', '| 物理资源 | bytes | bytes/s | 服务 ms |', '| --- | ---: | ---: | ---: |'])
        for row in result['physical_traffic']['resources']:
            lines.append(f"| {row['resource']} | {row['bytes']} | {row['bandwidth_bytes_per_second']} | {row['service_seconds']*1000:.6f} |")
    if 'all_to_all_phases' in result:
        for name, phase in result['all_to_all_phases'].items():
            lines.extend(['', name, '', '| rank | 发送 bytes | 接收 bytes |', '| --- | ---: | ---: |'])
            for rank, sent in enumerate(phase['send_bytes_per_rank']):
                lines.append(f"| {rank} | {sent} | {phase['receive_bytes_per_rank'][rank]} |")
            lines.extend(['', '| Offset | 有向边 (bytes) | 阶段 μs |', '| --- | --- | ---: |'])
            for row in phase['rounds']:
                edges = '; '.join(f"{e['sender']} → {e['receiver']} ({e['bytes']})" for e in row['edges'])
                lines.append(f"| {row['offset']} | {edges} | {row['modeled_seconds']*1e6:.6f} |")
    if 'tree_rounds' in result:
        lines.extend(['', '| 阶段 | 轮次 | sender → receiver (bytes) |', '| --- | ---: | --- |'])
        for row in result['tree_rounds']:
            edges = '; '.join(f"{e['sender']} → {e['receiver']} ({e['bytes']})" for e in row['edges'])
            lines.append(f"| {row['phase']} | {row['step']} | {edges} |")
        lines.extend(['', '| Rank | 发送 bytes | 接收 bytes | 标量归约加法 |', '| --- | ---: | ---: | ---: |'])
        for row in result['collective_ranks']:
            lines.append(f"| {row['rank']} | {row['sent_bytes']} | {row['received_bytes']} | {row['reduction_adds']} |")
    if 'ring_rounds' in result:
        lines.extend(['', '| 阶段 | 轮次 | sender → receiver : chunk (bytes) |', '| --- | ---: | --- |'])
        for row in result['ring_rounds']:
            edges = '; '.join(f"{e['sender']} → {e['receiver']} : {e['chunk']} ({e['bytes']})" for e in row['edges'])
            lines.append(f"| {row['phase']} | {row['step']} | {edges} |")
    if 'capacity_cards' in result:
        lines.extend(['', '| 卡 | 权重 bytes | 元数据 bytes | 状态 bytes | 工作区 bytes | 可用容量 bytes | 剩余 bytes | 声明预算可容纳 |',
                      '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |'])
        for row in result['capacity_cards']:
            lines.append(f"| {row['card']} | {row['packed_weight_bytes']:,} | {row['metadata_bytes']:,} | {row['state_bytes']:,} | {row['workspace_bytes']:,} | {row['capacity_bytes']:,} | {row['headroom_bytes']:,} | {row['fits_declared_budget']} |")
    if 'cache_variants' in result:
        lines.extend(['', '各路径是比较场景，不能将各行相加：', '',
                      '| 路径 | 每请求每 token bytes | 累计旧历史读 bytes | 追加写 bytes | 最终状态 bytes | Decode QK/PV FLOPs |',
                      '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['cache_variants']:
            lines.append(f"| {row['name']} | {row['history_bytes_per_token']:,} | {row['decode_prior_history_read_payload_bytes']:,} | {row['decode_append_write_bytes']:,} | {row['final_persistent_state_bytes']:,} | {row['decode_attention_matrix_flops']:,} |")
        lines.extend(['', '| 路径 | 完整 prefill QK/PV FLOPs | 命中前缀后 QK/PV FLOPs | 完整写 bytes | 命中后写 bytes | 前缀状态 bytes |',
                      '| --- | ---: | ---: | ---: | ---: | ---: |'])
        for row in result['cache_variants']:
            lines.append(f"| {row['name']} | {row['full_prefill_attention_matrix_flops']:,} | {row['prefix_suffix_attention_matrix_flops']:,} | {row['full_prefill_history_write_bytes']:,} | {row['prefix_suffix_history_write_bytes']:,} | {row['prefix_checkpoint_payload_bytes']:,} |")
        lines.extend(['', 'KDA recurrent／短卷积槽的逐调用读写另见 JSON；未并入全历史读取列。'])
    if 'mathematical_block_work' in result:
        work = result['mathematical_block_work']
        lines.extend(['', '数学块算法（按有效三角项计算，非 FLA 融合 kernel 指令数）：', '',
                      '| 有效块长 | 块数 | 每块矩阵阶段 FLOPs |', '| --- | ---: | --- |'])
        for row in work['blocks']:
            lines.append(f"| {row['valid_tokens']} | {row['chunks']} | {row['matrix_stages_per_chunk']} |")
        lines.extend(['', work['scope']])
    if 'chunk_tensors' in result:
        lines.extend(['', '| Chunk 张量 | 形状 | dtype | bytes |', '| --- | --- | --- | ---: |'])
        for row in result['chunk_tensors']:
            lines.append(f"| {row['name']} | {row['shape']} | {row['dtype']} | {row['bytes']:,} |")
        lines.extend(['', '| 存活阶段 | 已确认重叠张量 | 子集 bytes |', '| --- | --- | ---: |'])
        for row in result['known_live_phases']:
            lines.append(f"| {row['name']} | {', '.join(row['objects'])} | {row['known_live_tensor_bytes']:,} |")
    if 'attn_res_calls' in result:
        lines.extend(['', '| 层 | 分支 | 已存块 | 候选数 | 加权矩阵 FLOPs | 普通 FLOPs |', '| --- | --- | ---: | ---: | ---: | ---: |'])
        for row in result['attn_res_calls']:
            lines.append(f"| {row['layer']} | {row['branch']} | {row['saved_blocks']} | {row['candidates']} | {row['matrix_flops']:,} | {row['scalar_flops']:,} |")
    if 'attention_shapes' in result:
        lines.extend(['', '| 注意力张量 | 形状 |', '| --- | --- |'])
        for key, value in result['attention_shapes'].items():
            lines.append(f'| {key} | {value} |')
    if 'checkpoint' in result:
        checkpoint = result['checkpoint']
        lines.extend(['', '官方 checkpoint 元数据核验（张量载荷，不含文件头）：', '', '| 项目 | 值 |', '| --- | ---: |'])
        for key in ('verified_tensors', 'verified_shards', 'checkpoint_tensor_payload_bytes'):
            lines.append(f"| {key} | {checkpoint[key]:,} |")
        for key, value in checkpoint['byte_groups'].items():
            lines.append(f'| {key} | {value:,} |')
        if checkpoint.get('config_shape_mismatches'):
            lines.extend(['', '**官方配置／参考代码与 checkpoint 形状不一致；不可据此宣称已验证运行兼容。**', '',
                          '| 张量 | 配置／代码形状 | checkpoint 形状 | 参数差值 |', '| --- | --- | --- | ---: |'])
            for row in checkpoint['config_shape_mismatches']:
                lines.append(f"| {row['tensor']} | {row['config_shape']} | {row['checkpoint_shape']} | {row['parameter_delta']:,} |")
        lines.extend(['', checkpoint['scope']])
    if 'parameter_components' in result:
        lines.extend(['', '基础模型逻辑参数分项（排除 MTP、量化 scale 和整数表）：', '', '| 分项 | 参数 |', '| --- | ---: |'])
        for key, value in result['parameter_components'].items():
            lines.append(f'| {key} | {value:,} |')
        lines.extend(['', '覆盖状态：`' + json.dumps(result['coverage'], ensure_ascii=False) + '`', '',
                      'JSON 的 components 保留各个模块及状态子账。'])
    for field, title in (('matrix_components', '矩阵工作分项'), ('scalar_components', '普通算术分项')):
        if field in result:
            lines.extend(['', title + '（特殊函数独立计数）：', '', '| 分项 | FLOPs |', '| --- | ---: |'])
            for key, value in result[field].items():
                lines.append(f'| {key} | {value:,} |')
    if result.get('calculation') == 'llama70-dense-forward':
        initialization = result['initialization']
        operation = initialization['operator']
        lines.extend(['', 'Llama3 RoPE初始化单独执行，不包含在下方每次forward总数中。', '',
                      '| 初始化 | 普通算术 | 特殊操作 | 常驻buffer bytes |',
                      '| --- | ---: | --- | ---: |',
                      f"| {operation['name']} | {operation['scalar_flops']} | {operation['special_ops']} | {initialization['resident_buffer_bytes']} |",
                      '', operation['notes'], '',
                      '| 每次forward特殊操作 | 层重复 | 单次计数 |',
                      '| --- | ---: | --- |'])
        for operation in result['operators']:
            if operation['special_ops']:
                lines.append(f"| {operation['name']} | {operation['repeats']} | {operation['special_ops']} |")
    if "operators" in result:
        lines.extend(["", "每行是一次出现的成本，整模型需乘 repeats；层编号为 0 起。", "",
                      "| 算子 | 重复 | 输入／矩阵／输出 | 矩阵 FLOPs | 普通算术 | 权重读 bytes | 激活读 bytes | 激活写 bytes |",
                      "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |"])
        for op in result["operators"]:
            shapes = "；".join(f"{name}={shape}" for name, shape in op["shapes"].items())
            lines.append(f"| {op['name']} | {op['repeats']} | {shapes} | {op['matrix_flops']:,} | {op['scalar_flops']:,} | {op['weight_read_bytes']:,} | {op['activation_read_bytes']:,} | {op['activation_write_bytes']:,} |")
    if 'residual_operations' in result:
        lines.extend(['', 'mHC 运算总数已乘出现次数；张量尺寸为单次出现。', '',
                      '| 操作 | 次数 | 形状 | 矩阵 FLOPs | 普通 FLOPs | 特殊原语 | 说明 |',
                      '| --- | ---: | --- | ---: | ---: | --- | --- |'])
        for row in result['residual_operations']:
            lines.append(f"| {row['name']} | {row['repeats']} | {row['shapes']} | {row['matrix_flops']:,} | {row['scalar_flops']:,} | {row['special_ops']} | {row['notes']} |")
    if 'matrices' in result:
        lines.extend(['', '矩阵台账按列出的层求和；routed 行的 M 是所有专家的行数之和，各专家尺寸另见下表。', '',
                      '| 矩阵 | 层编号 | 合计 M×K×N／层 | 存储／访问份数每层 | 矩阵 FLOPs | 统一格式权重载荷 bytes |',
                      '| --- | --- | --- | --- | ---: | ---: |'])
        for row in result['matrices']:
            lines.append(f"| {row['name']} | {row['layer_ids']} | {row['rows_summed_per_layer']}×{row['input_width']}×{row['output_width']} | {row['stored_copies_per_layer']}／{row['visited_copies_per_layer']} | {row['matrix_flops']:,} | {row['uniform_weight_payload_bytes']:,} |")
    if 'non_matrix_operations' in result:
        lines.extend(['', '非矩阵算术：表中总数已乘对应层数；特殊函数保持独立原语，不能按 Tensor Core FLOPs 折算。', '',
                      '| 运算 | 层数 | 每层形状 | 普通 FLOPs 合计 | 特殊原语合计 | 计量依据 |',
                      '| --- | ---: | --- | ---: | --- | --- |'])
        for row in result['non_matrix_operations']:
            lines.append(f"| {row['name']} | {len(row['layer_ids'])} | {row['shape']} | {row['scalar_flops']:,} | {row['special_ops']} | {row['notes']} |")
        lines.extend(['', result['non_matrix_scope']])
    if 'sparse_kernel_summary' in result:
        lines.extend(['', '稀疏注意力参考 kernel（固定 64-slot tile）：', '', '| 项目 | 值 |', '| --- | ---: |'])
        for key, value in result['sparse_kernel_summary'].items():
            lines.append(f'| {key} | {value:,} |')
        lines.extend(['', *('- ' + note for note in result['sparse_kernel_scope'])])
    if 'routed_expert_format' in result:
        fmt = result['routed_expert_format']
        lines.extend(['', 'V4 routed 专家实际格式：FP4 权重先转 FP8，再做 FP8×FP8、FP32 累加；不具备原生 FP4 峰值匹配资格。', '',
                      '| 格式／tile 结果 | 值 |', '| --- | ---: |'])
        for key, value in fmt['summary'].items():
            lines.append(f'| {key} | {value:,} |')
        lines.extend(['', *('- ' + note for note in fmt['assumptions'])])
    if 'dispatch_operations' in result:
        lines.extend(['', 'Dispatch 独立操作数载荷（已乘层数）；endpoint_minimum 只计输入输出端点，内部流量未知。', '',
                      '| 操作 | 层数 | 读 bytes | 写 bytes | 口径 | 说明 |',
                      '| --- | ---: | ---: | ---: | --- | --- |'])
        for row in result['dispatch_operations']:
            lines.append(f"| {row['name']} | {len(row['layer_ids'])} | {row['read_bytes']:,} | {row['write_bytes']:,} | {row['accounting_kind']} | {row['notes']} |")
        lines.extend(['', 'Dispatch 汇总：`' + json.dumps(result['dispatch_summary']) + '`', '', result['dispatch_scope']])
    if "expert_matrices" in result:
        lines.extend(["", "以下每个专家的尺寸在各MoE层相同；n_e=0表示本批不执行该专家。gate/up是两个独立矩阵。", "",
                      "| 专家 | n_e | gate/up各自 A × W → Y | down A × W → Y |",
                      "| --- | ---: | --- | --- |"])
        for row in result["expert_matrices"]:
            gate, down = row["gate_and_up_each"], row["down"]
            lines.append(f"| {row['expert']} | {row['tokens']} | {gate['A']} × {gate['W_math']} → {gate['Y']} | {down['A']} × {down['W_math']} → {down['Y']} |")
    lines.extend(["", "计量条件：", ""])
    lines.extend("- " + assumption for assumption in result.get("assumptions", []))
    if result.get("scope"):
        lines.extend(["", result["scope"]])
    lines.extend(["", "固定来源：", ""])
    for source in result.get("sources", []):
        lines.append(f"- [{source['file']}]({source['url']})，SHA256 `{source['sha256']}`。")
    return "\n".join(lines) + "\n"


def operator_csv(result: dict) -> str:
    if result.get("calculation") == "flux2-vae-decoder-dag":
        output = io.StringIO()
        fields = list(dict.fromkeys(key for row in result["operators"] for key in row))
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in result["operators"]:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()})
        return output.getvalue()
    if "operators" not in result:
        raise ValueError("CSV expansion requires an operator report")
    output = io.StringIO()
    columns = ["layer", "name", "category", "shapes", "matrix_flops", "scalar_flops", "special_ops",
               "weight_read_bytes", "activation_read_bytes", "activation_write_bytes", "notes"]
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    if result.get("calculation") in {"deepseek-v3-base-forward", "qwen35-base-text-ledger", "qwen36-base-text-ledger"}:
        # Heterogeneous layers and multiple operations per layer require their
        # declared repeats; expanding each row across every layer would overcount.
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns + ["repeats"])
        writer.writeheader()
        for row in result["operators"]:
            record = {key: row.get(key, "aggregate; see repeats") for key in columns}
            record["repeats"] = row["repeats"]
            for key in ("shapes", "special_ops"):
                record[key] = json.dumps(record[key], ensure_ascii=False)
            writer.writerow(record)
        return output.getvalue()
    # Keep actual execution order, not op0 across all layers followed by op1.
    groups = [[row for row in result["operators"] if row["repeats"] == 1 and row["name"] in ("embedding", "rope_table")]]
    layer_ops = [row for row in result["operators"] if row["repeats"] > 1]
    layer_count = result["dimensions"]["num_hidden_layers"]
    for layer in range(layer_count):
        groups.append([{**row, "layer": layer} for row in layer_ops])
    groups.append([row for row in result["operators"] if row["repeats"] == 1 and row["name"] not in ("embedding", "rope_table")])
    for group in groups:
        for row in group:
            record = {key: row.get(key, "global") for key in columns}
            for key in ("shapes", "special_ops"):
                record[key] = json.dumps(record[key], ensure_ascii=False)
            writer.writerow(record)
    return output.getvalue()


def ub_scope_markdown(result):
    lines=['# UB 协作范围：当代 Qwen 教学计算','',
           '此结果是声明容量与串行通信路径预算，不是历史UB负载复原或端到端性能预测。','',
           '输入：`'+json.dumps(result['scenario'],ensure_ascii=False,sort_keys=True)+'`','',
           '| 候选 | 每机卡数×服务器 | 末步KV位置 | 最大逐卡bytes | 全卡容量通过 | 通信预算每前向ms | 全部前向ms |',
           '|---|---|---:|---:|---|---:|---:|']
    for c in result['scope_candidates']:
        s=c['summary'];lines.append(f"| {c['name']} | {c['cards_per_server']}×{c['servers']} | {s['final_cache_positions']} | {s['maximum_card_resident_bytes']} | {s['all_cards_fit']} | {float(Fraction(s['serial_communication_seconds_per_forward_exact']))*1000:.9f} | {float(Fraction(s['serial_communication_seconds_all_forwards_exact']))*1000:.9f} |")
    lines+=['','## 容量先于选择','',
            '比较标签只针对通信；任何逐卡容量不通过的候选不得据此选择。工作区是声明预留，尚非完整运行时峰值。','',
            '| 量 | 精确值 |','|---|---|']
    for k,v in result['scope_crossover'].items():lines.append(f'| {k} | `{v}` |')
    for c in result['scope_candidates']:
        lines+=['',f"## {c['name']}：逐卡与循环",'',
                '| server/card | PP/TP | 权重bytes | KV bytes | workspace bytes | resident bytes | fit |',
                '|---|---|---:|---:|---:|---:|---|']
        for d in c['placement_cards']:
            lines.append(f"| {d['server']}/{d['physical_card']} | {d['stage']}/{d['tp_rank']} | {d['weight_bytes']} | {d['kv_bytes']} | {d['workspace_bytes']} | {d['resident_bytes']} | {d['fits_declared_budget']} |")
        lines+=['','| 操作 | 层/阶段 | 服务接口 | 前向次数 | 每次启动轮 | 每次计费bytes | 所有前向秒（精确） |',
                '|---|---|---|---:|---:|---:|---|']
        for o in c['handoff_operations']:
            lines.append(f"| {o['name']} | {o['layer']}/{o['stage']} | {o['interface']} | {o['forward_evaluations']} | {o['startup_rounds_per_forward']} | {o['charged_resource_bytes_per_forward']} | {o['modeled_seconds_all_forwards_exact']} |")
    lines+=['','## 条件与来源','']+[f'- {s}' for s in result['assumptions']]
    lines+=['','历史材料仅证明时间线：']+[f"- [{s['file']}]({s['url']}) SHA-256 `{s['sha256']}`" for s in result['historical_sources']]
    lines+=['','模型固定来源：']+[f"- [{s['file']}]({s['url']}) SHA-256 `{s['sha256']}`" for s in result['sources']]
    return '\n'.join(lines)+'\n'
