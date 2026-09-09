# 11-9：真实 Agent 工具退出语义对照

已完成冻结的四次同服务 ABBA：baseline 和 proper-exit 各一次合格、一次失败，**没有观察到两臂合格次数差异，不能据此认定退出码干预改善质量**。这是一个任务上的四次尝试；全部正式轨迹保留，未追加样本或重跑挑结果。主 agent 尚需独立复核。

| 顺序 / 臂 | 模型轮数 | 非 JSON 输出 | 实际 run_tests | Agent finish | 原六例 | holdout 值且输入不变 | 追加 alias 失败 | holdout 严格通过 | 合格修复 |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| 0 baseline | 12 | 12 | 0 | 否 | 2/6 | 283/1013 | 0 | 283/1013 | 否 |
| 1 proper-exit | 12 | 4 | 5 | 否 | 2/6 | 283/1013 | 0 | 283/1013 | 否 |
| 2 proper-exit | 9 | 0 | 3 | 是 | 6/6 | 1013/1013 | 0 | 1013/1013 | 是 |
| 3 baseline | 9 | 0 | 3 | 是 | 6/6 | 1013/1013 | 0 | 1013/1013 | 是 |

合格修复门槛为 finish 且原六例全通过；holdout 单独报告。42 次真实 HTTP 模型请求均 HTTP 200，无 length 输出。首次 baseline 每轮输出多个并列 JSON 对象，严格 json.loads 报 Extra data，未执行其中任何工具。第一次 proper-exit 在五次真实失败退出码1之间，四次输出解释性非 JSON 文本，未写入修复。后两次各两次合法写入，第二次写入后六例全通过并 finish。非 JSON 是正式模型结果，不是接口启动故障，未被清理或宽松抽取。

**相同初始请求在任何工具反馈前已经产生不同输出。** 固定 greedy/seed 不保证此共享服务逐 token 重现；未获得服务器 token IDs、内核或调度轨迹，无法确定差异原因。首个 baseline 甚至没有到达干预工具，不能将其失败归因于退出码。此次 ABBA 不建立可靠因果效应、总体成功率或性能结论。

## 来源与真实退出

先只读检查 quality-feedback 的原源码和四份 rounds.jsonl：46 次模型请求，22 次 run_tests 全部 passed=false 且真实 returncode=0，见 [source-audit.json](source-audit.json)。该旧实验四次最终2/6的结论保持不变。旧 fixture/check_code.py/initial-messages.json 逐字复制并核对 SHA，见 [sources.lock.json](sources.lock.json)。本批前两次保留原 INITIAL，故其 holdout 283/1013，与旧模型已写入代码的1/1013不是同一文件或同一次检查。

[PROTOCOL.md](PROTOCOL.md)与执行源码在首个模型请求前冻结于 [run.lock.json](run.lock.json)，远端 worker 开始时验证全部哈希。两个臂均运行 [wrapper.py](wrapper.py)，在受限子进程内执行未改变的 test_intervals.py，使用原 CHECKER 的 results 和同一 all(passed) 表达式，proper-exit 在 false 时显式 sys.exit(1)，baseline sys.exit(0)。工具 returncode 直接取 subprocess.CompletedProcess.returncode，没有合成退出字段。stdout/stderr 原样交给模型，无附加诊断、修复提示或 holdout。

[raw/wrapper-proof.json](raw/wrapper-proof.json)保存首个请求前对同 INITIAL 的真实对子进程证明：stdout/stderr 完全相同，baseline退出0、proper-exit退出1。正式 proper-exit 的七次失败检查真实退出1、一次通过退出0；正式 baseline 的两次失败检查与一次通过检查均真实退出0。模型外末尾六例复验统一 baseline，仅用于判定质量，没有再发送模型。原 AST 白名单、read/write/finish 规则保持。

## 服务、预算与资源

只复用 RTX OpenRealtime `127.0.0.1:8000`，请求 `/v1/chat/completions`，服务名 `qwen-fast`。运行前后 GET `/v1/models`、服务器启动命令与现有 engine 启动 tick 核对一致：Qwen3-VL-30B-A3B-Instruct-FP8 revision `d9748a51ae66354c4dad665aab2c71f26cf2c8cd`；API PID3613078，engine PID3614304。启动参数包含 gpu-memory-utilization=0.50、max-model-len=40960、hermes parser；模型 config 一并只读封存于 service-before/after.json。

请求参数全臂相同：temperature0、top_p1、seed304、max_tokens1200、stream=false、enable_thinking=false；原始 system/user 完全相同，每次独立 workspace。没有启动新引擎、修改服务或共享环境、重置APC、模型预热或外部付费 API。共享 APC/内核暖态和后台竞争未隔离，只能称本次同服务 ABBA，不能当旧 Qwen3-8B 独立部署时间复现。

| 顺序 / 臂 | prompt tokens（累计历史） | completion tokens | 客户端请求区间和 s |
|---|---:|---:|---:|
| 0 baseline | 7290 | 438 | 2.818042 |
| 1 proper-exit | 20101 | 1536 | 8.608409 |
| 2 proper-exit | 9475 | 468 | 2.765058 |
| 3 baseline | 9439 | 448 | 2.605838 |

全部模型尝试阶段17.229603秒，小于20分钟；请求区间无重叠。上述时间仅客户端 HTTP 开始至完整响应读取，不是内核执行时间、服务排队时间或成功速度改善。无货币报价，cost=null；服务器未提供 token IDs，prompt/output_token_ids=null，不反推或伪造。usage 原样保存，含服务器实际提供的其他字段。

监督器只采样本任务CPU进程树，71次、最大间隔0.253495秒，RSS求和峰值68,947,968 bytes（65.754MiB）；采样不是瞬时峰值保证。CPU亲和8–11，OMP/MKL/OpenBLAS/NUMEXPR线程环境均1；stdlib控制器单计算线程，控制器地址空间上限2GiB，监督器以树RSS2GiB门槛只处理自有组。所有生成代码仅在受限Linux子进程执行：CPU2秒、AS512MiB、wall5秒、file1MiB，不执行生成shell；AST不是通用沙箱。

GPU显存只读作为共享背景记录：原五个服务PID均存在，其中3614304的49,664MiB属于已有共享引擎，不能算本任务独占显存；gpu_exclusive_bytes=null。模型CPU控制器退出0且无所属残留，未停止任何服务。未改 calculations、正文、inventory 或 PROGRESS。

## 独立检查与复核

原 [check_code.py](check_code.py) SHA256 `0979061b9100a0b887108e17122646cb89daa26b55e7dd73c89278dba1f85a3a`，1013例由1空+28单区间+784双区间+200固定seed随机构成。四次模型尝试全部结束后才在同限制Linux子进程运行，各保存原stdout/stderr/实际进程码及argv/时间/限制；模型未收到任何holdout结果。额外alias检查与原六例资格分列。

[analysis.json](analysis.json)提供逐次汇总，[checks.json](checks.json)提供663项通过的离线断言。运行 `python3 -B analyze.py` 只读原始数据并更新这两个独占目录输出，不调用模型、不执行生成代码、不依赖相邻实验。核对冻结SHA、原消息/请求参数、逐轮完整消息链、实际HTTP字节SHA、JSON严格拒绝、工具字段/子进程调用、代码前后/每轮快照、finish/六例分离、holdout时序与计数、资源/前后服务及正常退出。

`raw/`完整保留42组请求/响应原始字节、全部轮次messages/usage/finish_reason、工具原始结果、代码快照及最终文件、四份holdout、服务前后和资源记录；未有模型启动/接口调试失败被替代。最终完整数据通过离线审计后生成manifest。

独立运行可将 run.lock 所列文件及 run.lock.json 放入 RTX 新空目录，执行 `python3 -B run.py`；拒绝已存在raw，需同一匹配服务可用，不会自动启动引擎。封存目录不得直接重跑。模型端数值非确定性与共享环境限制仍适用。

远端：`/home/ubuntu/ai-infra-book-experiments/ch11/11-09/exit-status/`。交付仅此子实验，不宣布11-9/11-10整体完成；不声称退出语义改善质量或速度，主agent随后独立复核。
