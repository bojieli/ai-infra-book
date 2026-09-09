# 9-5：V4-Flash 与 Kimi K2 部署记录核对（部分完成）

本轮按题目允许的公开记录路径，固定KTransformers提交`31985f40bcc40da08107efdb1f81bf88cb38c6b2`的两份教程，核验源码文件哈希，并以只读解析脚本提取24个V4原生启动参数、9个Kimi参数和4组公开报告。没有启动这两个模型，也没有把教程配置当作实测容量扫描。

| 公开记录 | 平台范围 | 原文报告 | 尚未披露的关键条件 |
|---|---|---|---|
| V4-Flash-0731 单卡 | 1×5090 32GB，CPU型号未给 | decode 20+ tok/s；启动约4–5分钟 | 实际请求长度、测量并发、质量、逐请求记录、功耗 |
| V4 MTP | 8×5090，单请求decode | 26.5→32.74 tok/s，报告接受率90% | 完整八卡命令、接受率分母与原始输出、质量 |
| Kimi K2 Q4_K_M 单路 | 单路CPU＋一张消费GPU，具体型号未给 | 约10 TPS，约600GB主存 | 相同负载、CPU/GPU具体型号、质量、功耗 |
| Kimi K2 双路＋NUMA | 双路CPU，具体型号未给 | 约14 TPS | 除NUMA外其他条件是否一致、原始记录 |

V4的单卡20+记录不能与八卡MTP结果拼成同机加速或扩展曲线。Kimi的10/14 TPS也没有给出控制变量充分的NUMA消融，不能把差值全部归因于NUMA。教程同时宣布K2与0905支持，但示例下载指向原始Instruct GGUF，未固定权重提交；这些结果不代表Kimi K3。

公开配置已还原，但Docker默认值与原生命令并不相同：

| V4参数 | Docker默认 | 原生示例命令 |
|---|---:|---:|
| context length | 16384 | 16384 |
| max running requests | 2 | 2 |
| chunked prefill size | 4096 | 2048 |
| layerwise GPU prefill threshold | 2048 | 4096 |
| GPU memory fraction | 0.90 | 0.85 |

原生示例另设MXFP4、kt-num-gpu-experts=10、kt-cpuinfer=60、threadpool-count=2，并关闭radix cache。这些线程/线程池数不是CPU型号证明。Kimi示例cache_lens=32768、max_batch_size=4，也不等于已经实测32K上下文或4并发吞吐。示例curl的输出上限不是公开性能数字的完整负载说明。

版本方面，文档提交已固定，但运行环境未完整锁定：Docker只给`DSV4-specific`标签，没有镜像digest；源码安装没有固定所有子模块/引擎提交。教程另要求transformers=4.57.1、匹配版本的flashinfer≥0.6.9、测试过tilelang=0.1.8、tvm-ffi<0.1.12。不能把此前HiCache专用环境直接认作这份V4教程的可复现环境。本轮只解析命令，没有执行安装或服务命令。

当前RTX主机资源快照在available-resources.txt：可用内存低于教程的200GB主存要求，当前可用磁盘也低于约340GB权重存储要求。没有下载无法完整安置的权重，亦没有清理共享任务的数据。该资源观察只说明当前本机条件，不推断其他机器的部署能力。

独立复核（Python标准库即可）：

```sh
python3 experiments/ch09/09-05/extract.py
python3 experiments/ch09/09-05/verify_manifest.py
```

source-snapshots/封存两份完整文档；sources.json记录固定原链接、下载时间、哈希；records.json保存原命令文本、解析参数、原文限定词（20+、约）与缺失字段。未知条件使用null，不填成假设测量。程序只用shlex解析字符串，不执行公开命令。

固定来源：[V4-Flash教程](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/doc/en/DeepSeek-V4-Flash.md)、[Kimi K2教程](https://raw.githubusercontent.com/kvcache-ai/ktransformers/31985f40bcc40da08107efdb1f81bf88cb38c6b2/doc/en/Kimi-K2.md)。

9-5继续标为partial：同负载的上下文/并发增长、专家读取/CPU工作/PCIe记录、同质量全GPU候选、完整模型与环境锁定、整机功耗及费用输入仍待。并发与成本数量级推算由calculations独立任务负责，本轮未修改或执行。此为指定资料的首轮核对，不是全书实验完成后的最终跨session复核。
