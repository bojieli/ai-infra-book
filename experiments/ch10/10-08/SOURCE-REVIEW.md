# 固定官方实现与复现边界

verl commit：`d040717b21af2e23e8e789a3e354cff2394ae2de`。实验范围以用户限定的小模型真实闭环为准；inventory/SCOPE-REVIEW、原实验及历史版本线索只读，正文、inventory、PROGRESS与calculations不由本worker修改。

以下为实际选择版本的官方原始来源：

- [pyproject.toml](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/pyproject.toml) 和 [uv.lock](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/uv.lock)：vLLM0.24.0、Torch2.11cu130、Transformers5.9等冻结依赖。原件在environment/。
- [官方quickstart](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/docs/start/quickstart.rst)：Qwen2.5-0.5B-Instruct单GPU示例；其至少24GB HBM的文档前提，与本实验共享GPU进程预算不同，实测预算另列。
- [main_ppo](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/trainer/main_ppo.py)：use_v1=false仍走官方保留的main_ppo_v0，带deprecated警告。
- [FSDP engine](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/workers/engine/fsdp/transformer_impl.py)：官方forward_backward_batch、optimizer_step、单GPU状态字典处理。单卡NO_SHARD不是跨卡分片收益。
- [模型配置](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/workers/config/model.py)：支持HF attention override；本批SDPA、不去padding。
- [算法](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/trainer/ppo/core_algos.py) 和 [masked_whiten](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/utils/torch_functional.py)：GRPO组标准差及REINFORCE++回报/Bessel校正后的样本方差归一化，由实际verl执行；离线标准库按公式独立核验输出。
- [vLLM发送](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/workers/rollout/vllm_rollout/vllm_rollout.py)、[接收](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/workers/rollout/vllm_rollout/utils.py)、[bucket传输](https://github.com/verl-project/verl/blob/d040717b21af2e23e8e789a3e354cff2394ae2de/verl/workers/rollout/vllm_rollout/bucketed_weight_transfer.py)：官方CUDA IPC/direct-send、实际model.load_weights、KV清理和版本设置。观测读取真正接收模型的embedding。
- [Qwen原始模型固定revision](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/tree/7ae557604adf67be50417f59c2c2f167def9a775)：model-manifest.json固定全部文件SHA，初始embedding独立读取与两次正式启动的版本0一致。
- [NumPy2.3.5官方发布元数据](https://pypi.org/pypi/numpy/2.3.5/json)：唯一显式依赖覆盖，满足mistral-common要求的NumPy<2.4。numpy-override.json固定wheel SHA；上游锁保留原样，实际环境freeze和全依赖检查均提供。

私有观测patch保存原SHA、修改后SHA和diff；不改advantage/loss/backward/optimizer。Ray2.55.1的私有Node/RayParams启动adapter仅指定独立端口和短session，避免UNIX socket路径长度限制，不替代训练调度计算。复现不能任意切换主线、其他vLLM版本或SHM传输配置。本批不涉及SGLang实跑。
