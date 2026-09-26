# 《深入理解 AI Infra》配套 Skills

这 12 个 Skill 将书中的量化分析方法组织为可按任务加载的操作指南。它们服务于估算、定位瓶颈和比较设计方案；数字与结论应随模型、硬件、负载和书稿版本重新核算。每个 Skill 都指向简体中文正文的相应章节。正文仍是事实与推导的来源。

| Skill | 适用任务 | 原书 |
| --- | --- | --- |
| [resource-budget](resource-budget/SKILL.md) | 对一次模型执行作容量、计算、访存初估 | 第 1 章 |
| [model-footprint](model-footprint/SKILL.md) | 比较模型架构带来的权重、KV 和计算变化 | 第 2 章 |
| [workload-modeling](workload-modeling/SKILL.md) | 把请求或 Agent 轨迹转成随时间变化的负载 | 第 3 章 |
| [accelerator-selection](accelerator-selection/SKILL.md) | 按容量、带宽、算力、功耗选择加速器 | 第 4 章 |
| [kernel-runtime-analysis](kernel-runtime-analysis/SKILL.md) | 分析算子、融合、编译和运行时瓶颈 | 第 5 章 |
| [parallelism-planning](parallelism-planning/SKILL.md) | 比较多卡切分和超节点规模 | 第 6 章 |
| [cluster-network-analysis](cluster-network-analysis/SKILL.md) | 估算跨节点通信和等待 | 第 7 章 |
| [inference-serving](inference-serving/SKILL.md) | 调整批处理、KV、卸载和推测解码 | 第 8 章 |
| [distributed-inference](distributed-inference/SKILL.md) | 比较推理阶段分离、状态路由与恢复 | 第 9 章 |
| [training-system-planning](training-system-planning/SKILL.md) | 估算训练状态、步时、检查点和完成期限 | 第 10 章 |
| [agent-runtime-capacity](agent-runtime-capacity/SKILL.md) | 安排 Agent 的模型服务和工具环境资源 | 第 11 章 |
| [edge-cloud-placement](edge-cloud-placement/SKILL.md) | 比较端、边、云的交互延迟与成本 | 第 12 章 |

## 使用

将需要的目录复制或链接到 Agent 的 Skills 目录。例如 Codex 使用 `~/.codex/skills/`，Claude Code 使用 `~/.claude/skills/`。这些 Skill 的书稿和计算工具路径相对本仓库根目录；单独复制 Skill 时，请保留本仓库作为参考资料。

先阅读对应 `SKILL.md` 的适用条件。需要具体数值时，从书中公式和 `calculations/` 的模型配置出发，代入当前输入，不要把原书算例当作当前硬件基准。缺少关键输入时，明确列出假设、给出范围，并指出哪项测量最能改变结论。
