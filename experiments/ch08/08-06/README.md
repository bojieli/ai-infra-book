# 实验8-6：公开输出速度与实际Agent边界

完成公开条件快照和一组既有真实Agent记录的口径核验；没有调用MiMo服务或重复运行Agent。**公开“超过1000 tokens/s”不能直接换算成完整任务加速。** 该快照缺少本轮可核验的完整并发/计时窗口，现有Agent记录也没有可拆分的prefill/decode时间。

## 公开结果与未知条件

采用[小米MiMo与TileRT公告](https://mimo.mi.com/docs/en-US/news/latest/1000tps)于2026-09-07保存的历史HTML快照；SHA和原始URL见`sources/public-source.json`。这不是当前产品可用性、报价或最新页面核验。

| 条件 | 本轮能核对的内容 |
|---|---|
| 模型 | MiMo-V2.5-Pro-UltraSpeed，作者称1T规模；不当作1T Dense |
| 速度 | 作者报告输出速度超过1000 tokens/s；未取得逐请求原始数据 |
| 部署 | 一个8卡通用GPU节点 |
| 量化 | MoE专家做MXFP4 QAT，其他模块保留原精度；不称全模型FP4 |
| 推测生成 | DFlash，SWA草稿，mask block size 8 |
| 运行时 | TileRT |
| 未知 | GPU具体型号/容量、并发、输入/输出长度、精确计时起止、TTFT、逐请求trace |

未知项表示没有从本轮可核验正文取得，不声称其他页面或嵌入图中也没有披露。没有推断八卡型号，也没有将mask长度当作实际接受长度、固定加速倍数或并发容量。宣传数值仅作为待校准的作者报告。

## 实际Agent记录

完整复用11-9退出语义实验的四次ABBA原件，共42次HTTP200非流式请求；四次均保留，未按成功挑选或重跑。前两次没有合格修复，后两次各完成原6/6和严格holdout1013/1013。这是同一人工修复任务的四次尝试，不是总体成功率估计，也不是MiMo/Qwen配对。

| 原运行 | 模型轮数 | 合格修复 | HTTP区间和 s | 已审计工具次数 | 已审计工具区间和 s | 首请求至末次验证结束 s |
|---|---:|---|---:|---:|---:|---:|
| 0-baseline | 12 | 否 | 2.818042 | 0 | 0 | 2.848968 |
| 1-proper-exit | 12 | 否 | 8.608409 | 5 | 0.114010 | 8.752769 |
| 2-proper-exit | 9 | 是 | 2.765058 | 3 | 0.082691 | 2.904694 |
| 3-baseline | 9 | 是 | 2.605838 | 3 | 0.073100 | 2.720519 |

HTTP区间包含网络、服务调度、模型处理和完整响应读取，不能全部称decode。原记录`stream=false`且没有token IDs、首token或服务器阶段时间；按输出token数除以1000来替换整段HTTP时间，会混淆模型、质量和计时边界。

“已审计工具”只覆盖有独立起止的子进程；0表示零条此类审计，不是证明所有工具/控制器耗时为零。读写文件、解析等未完整定时，`all_tool_time_s`保持null。观察跨度从首个HTTP开始到末次验证结束，不含更早准备与后续holdout，不是部署生命周期。失败模型响应属于这次正式ABBA证据，不是启动失败，不删除。

`records/*/rounds.jsonl`含全部请求/响应/usage及消息、动作；`final.json`保留最终代码、验证输出与时间；`independent-checks.json`保留既有holdout原件。`origins.json`核对原始路径、字节和SHA。未运行其中生成代码，也未读取账号会话或访问付费服务。

## 独立复现与剩余任务

```sh
python3 analyze.py
python3 analyze.py /tmp/speed-boundary-review
```

仅依赖Python标准库，完全离线。脚本核对来源SHA、HTML及正文中的条件短语、每条HTTP/已审计工具/最终验证的时序、非流式与缺失token字段，并从原验证stdout重算资格标记。报告中的prefill、decode、服务器排队、首token及MiMo匹配质量均明确为null，不补造阶段图。

接下来需同一合格Agent任务的流式首token/末token与服务器阶段记录，才能校准只改变decode/prefill/工具的收益；草稿挤占batch和CPU专家验证流量也需匹配部署数据。C44的情景计算由另一任务负责，本目录不重复其算式、速度收益或费用计算。8-6保持部分完成，calculations未修改。
