# 13-1 retrieval-generation 独立只读核验

结论：通过。未发现需要重跑模型或修改已封存结果的实质问题。本次仅使用 Python 标准库读取记录和在临时副本重放离线分析；未启动模型、GPU 或计算任务，未修改实验目录。

- 封存 68 个文件、19,591,943 bytes 全部逐文件大小及 SHA256 一致。执行时四份原脚本逐一匹配 environment.json 的 SHA。
- BASE 评分器与管线分析器分别在新临时输出/运行副本执行，均 exit 0，输出与封存 quality.json、pipeline-analysis.json 逐字节一致。临时副本已删除。
- 独立对齐 288 个唯一请求、冻结 query/config/split、实际检索文档和 prompt IDs。96 条 calibration 完成后才有 192 条 evaluation；全部串行且前请求结束不晚于下一请求开始。281 条严格正确；7 条真实 UNKNOWN 均缺少目标证据，保留为科学结果。
- calibration 选参确实只按 8/8 后最小 k：Flat、ef16、ef64 均选 k1，heldout 各 15/16；ef4 无可选项。没有任何 family 的预选配置通过 heldout。另一条固定 cell 门槛要求 calibration 8/8 且 evaluation 16/16，只有 [1,2,7,8,10,11] 六格通过；README 没有把这些事后完整 cell 结果称为预选成功。
- 执行源码实际向常驻 CPU 编码/Faiss 进程发送请求，收到 live token IDs 后才调用生成；CPU 服务执行编码、索引搜索、拼装及模板分词，并断言文档/ID 与冻结计划一致。外层 start→end 是实际顺序管线的应用墙钟，包含 IPC 与观测开销。逐条验证 CPU 起止→generation_start→返回顺序以及流输出时戳。assembly_after_encoding 包含 search，分析没有再次相加。
- 原生 scheduler observer 委托原调度与更新后记录 KV 状态，没有实现替代调度。3,220 个含请求的事件全部唯一映射到冻结请求，且落在该请求 generation_start→end 内。离线重放验证 scheduled token 总计 162,740，每条为 input+output−1；288 条最终 stop、输出末尾 EOS 151645、ID 为整数。此次未重新加载 tokenizer，decode 验证由 root 既有独立核验覆盖。
- reserved pool 910 blocks、2,146,959,360 bytes，每池块 backing storage 2,359,296 bytes。固定合格格 k4/k16 最大分配分别 23/77 blocks，即 54,263,808/181,665,792 bytes；这是请求占用块的实际存储对应量，不能称为总池缩小或 KV 流量。README 六行 heldout E2E 中位数、输入中位数、最大分配字节与原始分析一致（详见 verification.json）。纯 prefill kernel 时间保留 null。

资源范围限制仍然有效：旧 guard 漏掉未继承自定义 token 的 engine，原 GPU=0 与 tagged RSS 不能解释成完整任务峰值，supervisor leftovers 只覆盖该筛选集合。ROOT-RESOURCE-NOTE.md 与 README 已明确说明，worker CUDA allocator 峰不能替代全卡使用峰，BASE 后续 guard 修改及 CPU 控制检查不追溯证明本次 GPU 监控完整。该限制不否定逐请求回答、外层墙钟或原生 KV 事件。本次没有将 supervisor 的成功退出扩大解释为完整进程树资源证明。

复跑本核验：`python3 experiments/parallel-workers/full_v4_score_review/retrieval-review/verify.py`。结果在 verification.json，离线重放标准输出在 replay.log。图形不重复审查，采用 root 已完成的两图目视核验；本报告范围是评分、时间关联和关键 README 数字。
