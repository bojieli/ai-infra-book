# 自动优化的成绩与部署收益

2026-09-08。接第 5.3.5 的性能反馈、实验 5-6 的候选验证，以及 5.5.2／实验 5-9 的实际请求。不增加优化工具介绍节。原件、固定提交和阅读范围见[归档](../references/framework-history/2026-09-08/optimization-validation/README.md)。以下计算是教学输入，未执行论文代码、模型调用或 GPU 实验。

## 从循环优化论文读出适用条件

LOOPRAG 从合成 C 循环及 PLuTo 优化结果中检索示例，再用编译错误、测试结果和性能排序指导生成。它给第 5 章的启发是如何组织候选和反馈。实际评估对象是 CPU SCoP：服务器列有 RTX 4090，但被优化的循环在 AMD EPYC 上运行；历史生成模型为 DeepSeek-V3-0324 和 GPT-4o-2024-08-06，不代表它们是本书当前模型案例。[公开 v1，§4–6](https://arxiv.org/pdf/2512.15766v1)

读结果时先看比较对象。表 3 中，LOOPRAG 相对 PLuTo 的汇总在 PolyBench 上为 0.45×，在另外两套基准上较好。§6.1 使用各程序加速比的算术平均，失败项记零，排除大于 600× 等离群项；LOOPRAG 的执行超时为 120 秒，基线为 600 秒。附录 F 也指出极大值会拉高均值。这些数值不能改写成“Agent 普遍胜过多面体编译”，更不能直接用于 GPU 服务预算。

正确性也要单独看。论文采用输入变异、分支覆盖和差分测试；附录 H 承认尚无语义正确性保证，并指出温度为零仍有输出变化。附录 C 说明函数副作用及别名检查的差异。`pure` 是程序语义承诺，会影响优化器能够删除哪些调用；不是为提高分数随意添加的提示。[GCC 15.2 的 `pure` 定义](https://gcc.gnu.org/onlinedocs/gcc-15.2.0/gcc/Common-Function-Attributes.html#index-pure-function-attribute)

公开稿 Listing 8 的 GEMM 索引与 Listing 6 不一致：结果列循环由 NK 划分，内层却按 NJ 访问 `A[t3][j]` 和 `B[t4][j]`。本书不把该印刷代码当作可执行 GEMM 参考；论文链接的数据集本次返回 HTTP 401，尚不能用作者工件复核。这是公开材料的证据缺口，不据此推断全部实验实现。

## 从论文方法到实际评测工具

FlashInfer-Bench 的固定实现与 MLSys 2026 比赛文档提供了更直接的 GPU 练习入口。两种基线分开：正确性对照 Definition 的参考实现；比赛速度对照已优化的 FlashInfer solution。通用 evaluator 内 `speedup_factor` 使用参考实现时间，比赛 `get_solution_score(..., baseline_author="flashinfer")` 则重新按指定基线求比，不能混用两个字段。[比赛规则](../references/framework-history/2026-09-08/optimization-validation/starter-evaluation.md)、[评估器](../references/framework-history/2026-09-08/optimization-validation/fib-default.py)、[评分实现选读](../references/framework-history/2026-09-08/optimization-validation/fib-scores.py)

比赛固定 B200／sm_100a，题目是指定形状与格式的 FP8 MoE、DSA、GDN；它们不是任意 Qwen3、V4、K3 算子的通用定义。比赛 MoE 指定 `atol=1, rtol=0.3, required_matched_ratio=0.9`，而本次固定框架 YAML 的 MoE 匹配比例是 0.95；配置解析允许 CLI 覆盖。默认 evaluator 还检查输出形状、dtype 和非有限值，专用 evaluator 另有语义。记录的是这次指定配置，不能把某一容差称作整个框架的唯一正确性标准。[配置与范围](../references/framework-history/2026-09-08/optimization-validation/reading.json)

用相同容差作一个独立小例子：20 个参考元素均为零，候选有两个元素为 2，其余正确。匹配比例为 0.9，满足 0.9 而不满足 0.95；这只解释测试判定，不证明对完整模型质量的影响。练习中的容差、参考实现和输入集合应由实验规定，Agent 负责提出候选。

## 加速比平均与总时间

假设同一资源上两个形状的基线都需 100 μs，下表两种候选均已通过相同验证：

| 形状 | 基线 | 候选 A | 候选 B |
| --- | ---: | ---: | ---: |
| x | 100 μs | 10 μs | 50 μs |
| y | 100 μs | 200 μs | 50 μs |

按形状加速比取平均，A 得到 `(10+0.5)/2=5.25`，B 得到 2。但各调用一次时，A 共需 210 μs，比原来的 200 μs 更慢；B 只需 100 μs。若 x 占调用的 90%，A 的平均执行时间为 29 μs，又优于 B 的 50 μs。A 优于 B 的条件为 `200−190p < 50`，即 `p > 15/19`。分数与部署选择回答的是不同问题。

按真实频数计量 `Σ n_i t_i`，失败时记录原路径回退的实际时间，不能把论文中的“失败项得零分”当成执行耗时。若使用逐形状分派，A 用于 x、B 用于 y，等频平均为 30 μs；再把每次查表／调用开销 d 加回去，与统一使用 B 的 50 μs 比较，本例要求 `d < 20 μs`。额外准备花费若为 600 秒，且 d=0，每次省 20 μs，需 3,000 万次调用才摊平；这是串行时间的简化预算，CPU、GPU、API 费用应按各自资源另算。

## 接回真正执行的路径

固定 `apply()` 实现需要启用运行时、匹配 Definition 与调用参数，并在找不到候选时按配置选择回退或 `use_def_best`。运行时有安装 FlashInfer 集成的入口，但本次未审计所有集成、匹配表与硬件筛选，也没有确认任意 vLLM／SGLang 路径都经过该入口。生成一个快 kernel、评测通过、实际被引擎调用和完整请求受益，分别留证据。[API](../references/framework-history/2026-09-08/optimization-validation/fib-apply-api.py)、[运行时](../references/framework-history/2026-09-08/optimization-validation/fib-runtime.py)

实验 5-6 使用真实 trace 的形状和调用频数，保留比赛式分数作为比较，同时计算含回退的部署预算。实验 5-9 再记录选中了哪个实现、是否走图路径、准备与分派花费、并发干扰及请求时间。单次 kernel 时间求和是诊断量，有重叠时由实际关键路径决定请求延迟。图 5-5 继续使用自绘 SVG，分开显示候选分数与按频数汇总的时间；本例没有 GPU 实测曲线。
