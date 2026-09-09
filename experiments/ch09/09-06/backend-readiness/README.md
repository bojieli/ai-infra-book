# RTX上MoE候选的实际配置检查

实际调用安装环境的`EngineArgs.create_engine_config()`，没有创建Engine或读取权重张量，没有GPU推理、路由或性能结果。正常结束句柄90062、exit0。配置拒绝是此检查的有效结果，不能当作被成功模型运行替代的调试失败删除。

环境固定为vLLM0.23.0、Torch2.11.0、Transformers5.12.1。缓存候选为Qwen3-VL-30B-A3B-Instruct-FP8 revision `d9748a51ae66354c4dad665aab2c71f26cf2c8cd`，架构Qwen3VLMoeForConditionalGeneration；四个safetensors文件的元数据总字节数32,251,954,920，未进行完整权重SHA或加载验证。模型config原件另存。

| 配置 | 实际结果 |
|---|---|
| 基线：TP1/PP1，eager，4096上下文，单请求，关闭APC及图像/视频输入 | 配置创建成功；运行尚未验证 |
| 基线加EP和EPLB | 拒绝：EPLB要求TP或DP大于1 |
| 基线加EP和DBO | 拒绝：默认allgather_reducescatter不受微批支持，要求deepep_low_latency或deepep_high_throughput及DeepEP kernels |
| 基线加EP、EPLB和DBO | 先被EPLB的TP/DP检查拒绝，未证明后续检查通过 |

`sources/vllm.config.parallel.py`和`vllm.config.vllm.py`保存对应检查源码，原始异常完整保存在`readiness.json`。并未尝试所有DeepEP后端或图模式；不能由这四个候选推导全部后端不支持。TP/DP大于1的配置也不代表本机具备对应物理多GPU资源。Qwen3-VL候选与题设纯文本MoE分开标注。

复现需要RTX现有固定运行环境和缓存。脚本独立，不依赖其他实验代码；在新目录复制check.py运行以保留当前快照：

```sh
/home/ubuntu/vllm023-venv/bin/python -B check.py
```

路径固定在check.py中；迁移需更新模型缓存路径并记录新版本。脚本只做配置检查，`model_requests`始终为0。`readiness.json`记录实际版本、源码SHA、四组输入及返回、模型configSHA和权重文件身份；`manifest.json`封存本目录。尚无dispatch/GEMM/combine、专家映射/复制、额外内存和请求尾延迟数据，不补造性能图。
