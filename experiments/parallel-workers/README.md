# 独立 Codex CLI 实验进程

2026-09-09：用户明确授权在 subagents 不可用时启动多个独立 Codex 进程。原三个 subagents 因使用额度退出；本机 codex-cli 0.153.4 的独立 `codex exec` 已实际收到模型响应，不能据此推断账户额度或进程并发无限。

| worker | 独占写入实验目录 | 资源 | 控制器会话 | CLI thread |
|---|---|---|---|---|
| pipeline | ch10/10-05 | Mac CPU ≤4线程、8GiB；受支持Megatron路径检查及执行/交接 | 16976 | 01a08412-8e5a-7100-b699-22127b0602e2 |
| dualpath | ch12/12-06 | Mac CPU ≤2线程、2GiB；真实双路径socket与故障 | 33658 | 01a08413-bd32-76d1-9ae7-a0e60c840efc |
| speculative | ch08/08-05 | RTX ≤24GiB、仅一个实验进程；受支持推测解码 | 56268 | 01a08413-bd39-7c02-b533-d6f9f54ea6d4 |

各子目录保存精确任务 task.md、事件 events.jsonl、stderr.log、worker状态 status.md 和完成后 final.md。主agent必须核对真实进程退出、原始记录与结果后再统一回填正文；启动/模型响应不等于实验完成。主agent继续10-1卸载工作，GPU预算<3GiB；共享设备时延不可解释为隔离性能。

所有worker禁止操作 calculations、共享正文/总进展/既有封存实验，不得再派生worker或终止现有服务。最终跨session审计仍须等第一轮全部实验完成后再进行。

pipeline会话16976已观测exit0；worker交付CPU环境真实预检exit2、固定Megatron0.16源码与未执行GPU交接脚本。主agent已读README，结论为所选官方路径需要CUDA，10-5实跑仍未完成；脚本语法/源码hash验证不能代替四GPU训练验证。

dualpath会话33658已观测exit0；主agent重跑smoke/formal离线验收、178文件SHA和图QA通过，已部分回填正文/inventory。完整12-6无线/WAN/电量范围仍未完成。

cachebranch新CLI会话50670已启动，独占ch09/09-10/branch-observation，补实际prefetch/调度分支事件关联；先准备代码，必须等待GPU-RELEASE.json且复验旧PID退出后再运行。它不会修改或单纯重复已封存storage-only实验。

最近主验收：10-1卸载57文件SHA与独立CPU参考通过，12-6 178文件SHA通过；整书5130本地链接/229参考hash/77快照通过，仅结构验证。speculative PID18649继续同V1 runner补测；cachebranch PID38898已响应并读取实际prefetch分支，仍未获GPU释放。

speculative CLI56268已观测exit0，主复核75文件SHA/41检查/独立质量与草稿计数和图通过。原GPU服务五PID重验一致、旧实验PID无，已发GPU-RELEASE.json供cachebranch运行；它仍须自己重验。8-5正文/inventory部分回填，kernel/动态/论文公开记录等完整范围仍待。

vision CLI23833/thread01a08429-2006-73d1-9c43-46f5b2261640已启动，独占ch12/12-03，使用已有VL8B视觉参数，仅远端CPU4线程/<12GiB与真实socket，不得使用GPU/改共享环境。主agent发现worker实际选用/home/ubuntu/sglang-venv（Torch2.10cu128），与任务所列tools/sglang0513-venv（实查2.11cu130）不同；已用codex queue发更正，允许保留所选CPU环境但准确归档路径，不为版本重跑。

本轮V4运行预检：已有Flash权重48分片/72317索引张量的header、offset与文件长度实际检查通过，未全payload SHA或推理。记录在ch02/02-05/runtime-preflight；完整模型与检索任务仍待。DFlash回填后最新结构校验5145链接/229参考hash/77快照通过。

cachebranch CLI50670 exit0，121文件SHA、独立分析和图主复核通过，9-10正文/inventory部分回填。GPU已实际恢复原五服务；新drafttrace CLI47828已启动，仅写ch08/08-05/kernel-trace并重验GPU后运行，补阶段/验证/回退观测，不改变已封存DFlash性能结果。

vision CLI23833 exit0，66文件SHA与独立std原始字节/双端日志验收主复核通过，12-3部分回填。ENVIRONMENT-NOTE澄清两个不同SG解释器，封存原件未改；完整语言KV/答案/WAN/功耗仍待。drafttrace47828继续准备/执行GPU阶段观测。

最新：drafttrace PID51888/thread01a08431-7b3c-7963-b668-132d3bc82cb3/会话47828已实查活跃；CPU视觉/分支观测均收尾完成。最新render/verify通过5155本地链接、229参考hash、77快照，仅结构验证。V4后续要核对SM120 FP4 MoE与OffloaderV1/量化加载组合，未启动全模型；用户显存不足时停止已有任务的授权保留，但本轮未用。

主复核更新：drafttrace47828与v4expert64928均实际exit0，分别64/52文件SHA通过；DFlash逐请求观测复核1182检查通过，V4预设数值未全通过（M8 10/32768），不能按执行exit0记作数值通过。新v4stages CLI8612独占ch02/02-05/expert-stages，≤3GiB GPU/4CPU/8GiB RSS，定位原始失败阶段，原实验全部只读。GPU仍为原五服务，不停止服务。

v4stages CLI8612已观测exit0：27文件SHA、原始输出与无观测控制、四FP32激活边界、十失败关联均主复核一致，正文/inventory已部分回填。原FP64门槛仍失败，只定位旧十个失败；完整模型未放行。当前主agent原生四层attempt-02远端92412在加载，第一次内存池配置失败独立保留。最近整书结构校验5172链接/229参考hash/77快照通过；第一轮及最终跨session审计仍未全部完成。

新pooldecision CLI38953独占ch11/11-10，只读现有已封存Agent/资源原始记录，形成资源池扩容选择的一页证据与验证计划；≤2CPU/RSS2GiB/新增30MiB，不运行新模型，不复算calculations预算，不将计划写成已完成扩容。主agent继续原生四层attempt-03，显式SWA/full1.0，前两次失败保留。

pooldecision38953已观测exit0，77分组/8文件SHA/228源SHA/7053检查主复核通过，11-10一页选择计划部分回填；新增ERRATA仅澄清分析器开销不同起点，原封存不变。主agent原生四层第五次33025 exit0，51raw SHA核验/87文件封存、两短请求返回；不是完整V4质量，原四次失败保留。最终GPU只有原五服务，无本批GPU残留。

新agentquality CLI65689独占ch11/11-09/quality-feedback，严格四次ABBA真实Agent原反馈/诊断反馈质量对照；原六例与独立holdout保留、不追加选结果。≤24GiB GPU/4CPU核8-11/RSS10GiB/20分钟，新作业重验原服务与余量；原所有GPU实验已退出。native87文件远端最终SHA全通过，最新结构校验5192链接/229参考hash/77快照通过。
