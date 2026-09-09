# ASPLOS 清单 111–123：运行时与测试论文的下一批筛选

2026-09-09。完成其中 112、118、120、121、122 的作者 PDF 完整摘要阅读，五张首页均实际查看，五份 PDF 共 76 页已归档。首次筛选只读摘要；后续 Ratte 选读范围见下文，不把归档页数当阅读页数；也尚未并入会议总清单。七份成功原始响应见 [sources.json](sources.json)，摘要、DOI、完整作者、年份和筛选决定见 [screening.json](screening.json)。没有执行下载代码、模型或测试工具。

| 清单序号 | 原始资料 | 与本书的关系及决定 |
| --- | --- | --- |
| 112 | [Golf 作者页](https://cs.au.dk/~amoeller/papers/golf/)、[PDF](112-author.pdf) | 利用 Go GC 标记阶段检测局部死锁，关注长期运行服务的泄漏。摘要不足以支持 AI 请求关键路径案例，归档即可。 |
| 118 | [MetaMut 作者 PDF](https://cs.nju.edu.cn/changxu/1_publications/24/ASPLOS24.pdf) | LLM 生成编译器模糊测试的变异器，专家提供提示、结构和验证。与 GPU 算子性能调优不同，暂不补正文。 |
| 120 | [Ratte 作者 PDF](https://www.doc.ic.ac.uk/~afd/papers/2025/ASPLOS-Ratte.pdf) | 为 MLIR 方言及其组合构造语义和测试，检测误编译。保留正文候选，后续核对支持方言、未定义行为和参照解释器；最多补现有优化实验的正确性讨论。 |
| 121 | [Snowplow 机构页](https://deepmind.google/research/publications/127036/)、[作者 PDF](121-author.pdf) | 学习式变异器用于 Linux 系统调用参数测试，kernel 指操作系统内核；不列为 GPU 计算内核优化。 |
| 122 | [KernelGPT 作者 PDF](https://yangchenyuan.github.io/files/ASPLOS25-KernelGPT.pdf) | LLM 生成并迭代修复 syscall 规格，增强 Linux 内核 fuzzing；不列为 Agent 自动 profile／加速算子的证据。 |

两处元数据差异已经保留：118 的 DOI 与当前程序清单吻合，但 PDF 引用、版权和会议标注均为 ASPLOS 2024、Volume 4；本目录记录清单位置，不改写论文发表年份，也不再新增一篇重复论文。121 的 PDF 为 Rui Wang，Crossref／机构页为 Wang Rui；PDF 的 Altınbüken 与 Crossref 的 Altinbüken 拼写也不同。核验完整作者集合并保留来源原文，不静默删除或替换作者。

本轮未增加正文节、核心实验或配图。对于“用 AI 做软件测试”的论文，只有能帮助读者检验算子变换或模型执行的具体内容才考虑进入扩写资料，不能只按 LLM、kernel 等关键词采纳。

此子范围的 111、123 尚未取得并阅读原始摘要；113 的取得困难和 114／116／117 的阅读另见[服务系统批次](../serving-113-117/README.md)。115、119 已在原有清单筛选，不重复计数。后续合并需要同时检查 DOI 去重和 118 的年份差异。

校验命令：`python research/2026-infra-survey/verify_asplos_testing_batch.py`。它重新从原 PDF 提取摘要、核对 DOI／题名／作者、页数与原始字节，不证明论文正文或实验已经复现。

后续已选读 Ratte 物理页 2–4、7–12，查看页 12 的表与例子，见 [Ratte 阅读记录](RATTE-READING.md)。只在现有实验 5-6 增加候选有效率与验证成本的计数要求；没有新增正文节。43 个支持操作、无环生成与 CPU LLVM 目标的限制均保留，不声称 GPU 模型算子已被全面验证。
