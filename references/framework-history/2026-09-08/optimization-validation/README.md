# 自动优化：评测条件与部署入口

2026-09-08。与 [LOOPRAG 正文选读](../../../proceedings/ASPLOS/2026/looprag-reading.json)对照，回答第 5.3.5／实验 5-6 的问题：候选怎样验证，成绩怎样汇总，结果怎样接回实际执行。教学推算见[案例](../../../../case-studies/optimization-evaluation-and-deployment.md)。

本目录归档 20 份 HTTP 响应，其中 19 份成功，一份论文所链数据集的 HTTP 401。五份 GitHub 响应只读仓库、提交身份及指定路径；其余成功来源按 [reading.json](reading.json)中的 22 个完整／选定范围登记。未执行下载代码或付费模型调用。

固定版本：

- FlashInfer-Bench：`40e6ca7844b514eb4b1c7edba6d6a7377df57870`，提交时间 2026-05-01；日期是本次固定提交时间，不是所有功能引入日期。
- 比赛 starter kit：`75ccd05cafceb0fd1f86be4cd0f2117249463c66`，提交时间 2026-04-26。FAQ 自注 4 月 16 日；其中“软件版本待公布”的历史说明与后来 Evaluation 中的具体环境分别保留。
- [LOOPRAG v1](https://arxiv.org/abs/2512.15766v1)：2025-12-12，arXiv 注明接受于 ASPLOS 2026；没有用其他同名 RAG 项目作源码。
- [GCC 15.2 文档](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Common-Function-Attributes.html#index-pure-function-attribute)：只读 `pure` 属性条目。

主要结论：

1. 正确性参考、框架 trace 中相对参考的速度字段，以及比赛相对 FlashInfer 的分数，使用的分母不同。评分源码按共同 workload UUID 取记录中的最快通过时间；任何已记录失败会使该 solution 得零分。它不验证数据库是否覆盖了应测的全部 workload，完整评测仍需规定输入集合。
2. 比赛按形状加速比取算术平均，实际部署按调用次数和时间计算，并单列失败回退。候选排名可能随输入分布翻转。
3. 比赛绑定 B200 和特定 MoE／DSA／GDN 定义。通用配置、按 op_type 的 YAML、按 Definition 的覆盖与 CLI 有优先次序；本次 MoE 默认匹配比例 0.95，比赛 CLI 为 0.9。专用 evaluator 不在本次源码选读范围内。
4. `apply()` 是一个实际分派入口，但尚未审计完整引擎集成、匹配键、表和硬件过滤。没有把 benchmark 工具写成 vLLM、SGLang 或 Ollama 的共同默认功能，也没有根据比赛内核推断全模型加速。

完整字节、URL、状态、哈希保存在 [sources.json](sources.json)。本次没有新下载代表论文；LOOPRAG 的 22 页原件在会议目录复用，选读 15 个物理页并查看四张页面图。复核命令：`python research/2026-infra-survey/verify_optimization_evaluation.py`。
