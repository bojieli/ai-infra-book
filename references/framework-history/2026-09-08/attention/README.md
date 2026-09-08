# 注意力内核与框架后端的固定对照

获取日期 2026-09-08（Asia/Singapore）。URL、响应字节、提交和 SHA-256 见 [sources.json](sources.json)。只下载和阅读源码，没有安装、导入或执行这些 GPU 栈。

| 项目 | 固定提交 | 已阅读范围 |
| --- | --- | --- |
| Dao-AILab/flash-attention | `ce088ab9ce0fc0434dcd8afa0a791da9fcc3a820` | [README](fa4-readme.md)全篇；[Softmax](fa4-softmax.py)第 244–403 行的最大值更新与指数分担；[SM100 前向](fa4-forward.py)第 300–328、340–362 行及 TMEM／warp 分工检索。其余实现仅归档。 |
| vllm-project/vllm | `51da0ca66c8065619c79e35dff97aa99aeaf5644` | [版本选择](vllm-fa-utils.py)第 1–265 行，含平台优先、覆盖与若干回退；[attention backend](vllm-fa.py)只检索支持条件及版本调用，未完整阅读。 |
| sgl-project/sglang | `c99d906effa8bd05573995127f0d4a0984c5a96a` | [阶段选择](sglang-hybrid.py)第 1–190 行；[FA wrapper](sglang-fa.py)第 271–313 行的版本导入及确定性设置，其余只归档。 |

[vLLM 支持文档](vllm-attention-doc.html)已读自动／手动选择和 CUDA 优先顺序；[SGLang 支持文档](sglang-attention-doc.html)已读 MHA／MLA 支持、hybrid attention、验证后端与示例。这两份是 current 获取日快照，不能反推特性首次发布日。正文不复制完整支持矩阵。

vLLM 的框架后端选择与 `FLASH_ATTN` 内部版本选择是两个步骤；某种硬件偏好 FA4 不等于服务默认就走 FA4。SGLang 的阶段选择同时影响验证、图初始化和元数据，不能只统计 prefill 的内核时间后推断整个请求。当前 SGLang 与 vLLM 对确定性相关开关处理不同，固定 wrapper 和依赖应随实验一起记录。

原论文与当前实现的关系、复算及大纲落点见[内核与训练效率笔记](../../../../case-studies/kernel-and-fleet-efficiency.md)。这是代表路径核对，不是完整版本历史或三套框架的全代码审计。
