# 算子拆分与激活量化融合：读取范围

本批 14 份成功响应见 [sources.json](sources.json)，逐文件读取范围见 [reading-proof.json](reading-proof.json)。Korch 论文 PDF 另在 [ASPLOS 2024](../../../proceedings/ASPLOS/2024/README.md)归档。只静态阅读和计算，没有执行下载的代码、安装依赖或运行模型／GPU 测试。

Korch 固定 `b188b5296ed14510a46f36e21545d35e8741c9f2`（2025-03-27）；它是历史研究仓库，不以提交时间代替论文日期。vLLM 对照 v0.6.0 和固定当前 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`；这是两个时点的实现对照，尚未核定该融合 pass 的首次合入／发布时间。

| 文件 | 实际读取范围与用途 |
| --- | --- |
| [作者出版页](korch-author.html)、[arXiv landing](korch-arxiv-landing.html) | 书目信息、作者 PDF 链接、v1／related DOI／修正说明；页面与 PDF 作者列表差异单列在论文记录 |
| [commit](korch-commit.json)、[tree](korch-tree.json) | SHA、日期、路径与尺寸查找；不是全部 JSON 正文阅读 |
| [Korch README](korch-README.md)、[Segformer 配置](korch-segformer.toml) | 完整文件；手工 cut points、full_graph 设置、依赖和代码生成仅 Candy 实验支持的边界 |
| [calc.py](korch-calc.py) | 300–425 行；输入／输出约束、加和目标、1000 秒求解限时、候选构建和调用的 profiler 列表 |
| [profiler.py](korch-profiler.py) | 完整文件；TVM 记录与 cuDNN／cuBLAS 分派。存在 TensorRT profiler 不代表 main 实际把它加入选择列表 |
| [kernel_profiler.py](korch-kernel_profiler.py) | `profile_main` 至文件末尾的已读段；读取数据库、调优和返回 run_secs，默认正确性开关为 false。不能把存在校验代码当成已经验证 |
| [operator_fission.py](korch-operator_fission.py) | 仅函数／Softmax 检索定位；未读实现正文，不用于证明数值稳定或全部算子支持 |
| [vLLM v0.6.0 activation](vllm-2024-activation.py) | 1–58 行；SiluAndMul 原生表达与自定义调用 |
| [当前 activation quant pass](vllm-current-act-quant.py) | 完整文件；静态 FP8、动态 group 128／64、NVFP4 匹配及替换。没有审计完整 runner／CUDA 调用链 |
| [当前编译配置](vllm-current-compile-config.py) | 103–141、226–273 行；条件初始化、融合选项及形状消除的关系 |
| [当前融合文档](vllm-current-fusions.md) | 1–65、276–341 行；支持条件和 activation／RMSNorm quant 小节。未将文档性能范围当成本机测量 |

Korch 公开 main 的候选测量列表实际是 memory-bound、conv、gemm 三种 profiler；虽构建了 TensorRT profiler 对象，该对象没有加入此列表。MemBoundKernelProfiler 取返回记录中的一个时间项，不能一概称为多次测量均值。公开生成入口有实验性限制，故本书用它解释方法，Qwen3 实验使用真实服务框架的可运行路径。

vLLM 当前 pass 的存在、配置启用、模式匹配成功、生成内核执行和整请求受益分别核对。教学算例选择非 UE8M0、无 padding 的 FP32 scale 变体；没有证明所有 scale 布局、量化格式或硬件均有相同流量与数值行为。

采用位置为第 5.3 与既有实验 5-4／图 5-3：[计算和取舍](../../../../case-studies/kernel-orchestration-and-quantization.md)。
