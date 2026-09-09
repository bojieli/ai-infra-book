已完成本地及 RTX 指定目录的清理、传输和封存核验。

- **native-layer-probe**：删除根目录旧 `results/`、`run.log`、`run.py`、`launch.py`、旧字节码，以及 `attempt-02/03/04`；移除失败历史汇总，重新生成仅核验最终成功的分析。远端同步删除对应内容及根目录旧缓存、临时文件。
- **完整保留 attempt-05**：确认真实 `exit_code=0`，两次请求完成，256／512 个输入各生成 4 个 token。保留完整日志、原始响应（含负质量输出）、脚本、源码快照、成功 JIT preflights，并补齐远端成功运行的编译缓存。README 和复现入口已更新。
- **full-model-readiness**：本地删除 `probe-attempt01.py`、`first-failure.txt`；远端这两项已不存在。两端保留最终 `probe.py` 和四个实际资源记录，补齐 README，明确 **110 GiB CPU offload 仅是候选，不是最低需求证明**。

| 目录 | manifest 文件项数¹ | raw 清单项数 | 核验结果 |
|---|---:|---:|---|
| native-layer-probe | 407 | 401 | 两端 SHA256 全部通过 |
| full-model-readiness | 7 | 5 | 两端 SHA256 全部通过 |

¹ 不含 manifest 自身；两端 manifest 自身的 SHA256 也一致。远端清理前已核对规范路径、内容身份，并在删除前再次检查文件 SHA。

截断四层成功仍仅表示运行兼容性检查完成，`full_model_or_quality_pass=false`。本次未运行 GPU／模型任务、未操作进程，未修改正文、inventory、PROGRESS、calculations 或其他 worker 范围。

核验记录：[verification.json](/Users/boj/book/ai-infra-book/experiments/parallel-workers/cleanup/verification.json)。