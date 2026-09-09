# 冻结协议：真实工具退出语义 ABBA

2026-09-09，任何模型 POST 前冻结。四次且仅四次：baseline / proper-exit / proper-exit / baseline。每次新空 workspace，填入逐字复制原 fixture.INITIAL、SPEC、CHECKER；initial-messages.json/system 与 quality-feedback 相同。原 AST 白名单与非 run_tests 工具执行逻辑保持。不是质量改善预测，不根据结果追加样本或修改提示。

只改变 run_tests 的真实 wrapper 进程退出码：两个臂均在子进程 runpy.run_path 执行原 test_intervals.py，stdout/stderr 原样保留；由原 results 按原 CHECKER 同一 all(passed) 表达式得到布尔。proper-exit 在 false 时显式 sys.exit(1)，baseline sys.exit(0)。不伪造 returncode，不附加诊断或修复提示。wrapper 放在控制器目录，不改变可读六例文件。异常自然传播。工具回复字段仅 returncode/stdout/stderr。

使用 RTX OpenRealtime 现有 127.0.0.1:8000 标准 HTTP /v1/chat/completions，model=qwen-fast；GET /v1/models 与 /proc 原 PID 3613078 启动命令必须共同确认 Qwen3-VL-30B-A3B-Instruct-FP8 revision d9748a51ae66354c4dad665aab2c71f26cf2c8cd，原 engine PID3614304。服务不符/不可用则停止并交状态，不新建引擎。请求固定 temperature=0、top_p=1、seed=304、max_tokens=1200、stream=false、chat_template_kwargs.enable_thinking=false。最多12轮，单请求在途，首次POST至全部模型尝试结束≤1200秒；每次HTTP超时=min(120秒,剩余预算)。不重试正式模型请求。

严格 json.loads 全文，不抽取代码围栏或局部JSON；length 终止标记并记录为无效工具输出，即使文本碰巧可解析也不执行。错误沿用原 Tool result error 消息形式；有效 finish 结束该尝试，但合格修复另要求原六例全通过。无额外模型预热，不改或 reset APC；暖态和背景竞争未知，只称本次同服务 ABBA，不能作为旧 Qwen3-8B 独立部署时间复现。

控制器及监督器核8–11，OMP/MKL/OPENBLAS/NUMEXPR线程1；控制器 RLIMIT_AS 2GiB；监督器每0.25秒仅采样自身及所建CPU子进程树，RSS求和>2GiB只终止本任务控制器组。采样非瞬时硬保证。生成代码仅受限 Linux 子进程：CPU2秒/AS512MiB/wall5秒/文件1MiB；不执行模型shell。AST边界非通用沙箱。GPU服务PID/显存仅在前后只读记录为共享背景，不计入本任务独占GPU资源。

完整保存请求原始字节、HTTP响应原始字节/状态/headers、messages、usage、finish_reason、全部工具进程stdout/stderr/returncode、每轮前后代码、最终代码及SHA。服务器未返回token IDs则null；kernel/scheduling时间null，仅客户端区间；费用null。四次结束后才在同限制Linux子进程运行原同SHA check_code.py，1013例，值且输入不变/追加alias失败/严格通过分列，永不反馈给模型。

运行前源码协议SHA锁与源文件锁；末尾离线校验全部轨迹、消息链、代码SHA、工具结果和wrapper真实退出、holdout、限制与服务前后记录，生成README、analysis、manifest。全部正式运行含负结果保留，不以重跑挑结果；被成功运行替代的启动/接口调试失败不封存。无需依赖其他实验文件运行。不改共享环境、服务、正文、inventory、PROGRESS或calculations。
