# 固定源码与观测边界

安装路径为 `/home/ubuntu/vllm023-venv/lib/python3.10/site-packages/vllm`；本目录 source 保存只读快照，raw/*/original-functions.json 保存实际启动时 inspect 得到的函数原文、文件路径及 SHA256。scripts/instrument.py 是进程内 wrapper：绑定原参数，进入 NVTX/record_function 范围，调用原函数一次并原样返回，只额外读取元数据。scripts/runner.diff 给出相对封存 runner 的完整差异。共享安装文件没有改写。

|真实 API|记录内容与边界解释|
|---|---|
|GPUModelRunner.execute_model|scheduler 的每请求 scheduled rows、实际 scheduled_spec_decode_tokens；不是每个请求的独立 GPU 时间|
|GPUModelRunner._model_forward|target 实际输入 shape、positions、input_batch.req_ids；prefill 与 verify 共用边界，按 scheduler 行和 spec metadata 区分|
|GPUModelRunner._sample|普通采样或拒绝采样的外层真实分支|
|RejectionSampler.forward|SpecDecodeMetadata 的实际 draft IDs、累积行偏移、logits/bonus索引，以及验证 logits batch shape、最终 sampler tensor|
|rejection_sample|真实输入 draft 与 target_logits argmax 的观测读回，以及返回 token tensor；内部 greedy kernel 在首个不相等位置写 target token，后续保持 -1；全接受则写 bonus|
|SpecDecodeBaseProposer.prepare_inputs_padded|GPU kernel 得到的 num_rejected、token_indices、valid_sampled_tokens_count|
|DFlashProposer.set_inputs_first_pass|seq_lens_before、拒绝数量、实际 query rows 与 new_cad.seq_lens；有效 context 为返回 seq_lens 减 K+1，即原 seq_lens 减拒绝数|
|SpecDecodeBaseProposer.propose|实际 draft tensor、next token 与上下文元数据；包括最后一次未必被下一步调度使用的草稿|
|GPUModelRunner._bookkeeping_sync|官方 CPU 侧同步/有效 token 处理范围；不等同 GPU KV 删除|

设备值读取（含用于核验的额外 argmax）放在 obs.readback.before/after 范围，明确会同步。这是观测批。CPU阶段 inclusive 时间仍可能包含嵌套观测与等待，绝不可称 GPU 阶段耗时。GPU 时间来自 Torch/CUPTI trace 中 kernel / gpu_memcpy / gpu_memset 的实际 duration，经 correlation 关联 CUDA runtime/driver 调用，再选最内层 wrapper；任何落在 readback 范围内的 GPU 活动单列，不冒充原模型计算。未落在已包装边界的活动保留 unattributed，不分摊。

本实现没有一个独立命名的“rollback kernel”。greedy 首拒绝索引来自同一真实输入 logits 的 argmax 与 draft 首个不匹配，另以 sampler 有效前缀、-1尾部独立核验；实际 rejected tensor 与 DFlash effective seq_lens 是后续执行证据。物理KV字节清零/页释放索引为 unknown：这些 API 实现的是有效前缀与槽位可见范围修正，没有提供一个物理撤销清单。不能把索引修正时间表述成物理 KV 清理时间。

内部 request ID 与外部 request ID 的映射遵从安装的 InputProcessor.assign_request_id（source/v1_engine_input_processor.py:223）：外部ID附加连字符和8位随机串；保留内部原值并移去固定9字符得到外部ID，核验外部 submit 集合。input_batch 顺序直接为 tensor 的请求行顺序；调度轮聚合统计只保留原始粒度，不按比例分配给请求。

未下载模型，target/drafter 读取固定原路径。Torch profiler 不需要额外安装或改共享依赖。热请求前有同形状完整预热；日志中 JIT 警告保留，不能因 profiler 批得到耗时而据此重做性能排名。

检查发现并保留：execute_model wrapper 进入时 input_batch 还没有经过原函数内 `_update_states`，其 boundary.request_ids 是更新前快照，首个观测 step 可包含最后一个 warmup ID。schedule.scheduled 则取自当轮 scheduler，_model_forward / sampler / proposer 的 IDs 已更新。所有逐行归因使用后者，不使用 execute_model 的旧快照。独立校验首次因这3个旧ID失败（results/independent-checks-attempt-01.json），按源码语义修正校验后保留完整最终结果，没有修改任何原始记录或重跑。
