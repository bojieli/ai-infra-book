# 预登记：真实 Agent 诊断反馈干预（2026-09-09，模型执行前冻结）

仅回答：此单一区间修复任务上，透明增强 run_tests 可观测反馈，能否在固定预算产生原六例全通过且 finish 的修复。固定四次，baseline → feedback → feedback → baseline；每次独立初始代码、原 system/user、SPEC、原六例和工具 schema。不得按结果追加、换提示、选种子。旧 11-01 2/6 未 finish、旧续修 4/6 和 alias 失败保持为失败。

从封存 11-01 源码静态提取 fixture，初始消息逐字取原第0轮。固定 Qwen3-8B revision b968826d9c46dd6066d109eabc6255188de91218；路径取远端封存 environment.json，不下载。/home/ubuntu/vllm023-venv/bin/python；vLLM0.23.0、Torch2.11cu130，当前 Transformers5.12.1，return_dict=False；thinking=false、greedy temperature0、seed304、每轮1200、最多12轮。原工具解析/错误反馈/finish终止规则保留；提前finish但六例不通过仍失败。

两臂仅反馈不同：baseline 原 run_tests 的 returncode/stdout/stderr；feedback 保留这三个字段，仅当原六例 passed=false 时增加 diagnostics_process 和 diagnostics。诊断在独立受限子进程重执行同六例，从实际执行保存 input_before、expected、actual（深拷贝快照）、input_after、unchanged、passed、返回对象/嵌套对象和入参对象的身份别名关系；仅返回失败例。对象身份检验不改变输入，不提供修复代码或提示答案。不新增测试输入，不向模型传独立holdout。所有实际反馈、代码及请求输入输出 SHA 另存日志，不向baseline添加字段。原六例文件不改。额外诊断是干预成本，轨迹分支改变属于干预结果；并非严格复现旧token轨迹。

一次引擎服务四次尝试，并发1；APC=true，每次（含第一次）调用已核验受支持 async reset_prefix_cache()，必须返回true，保留重置记录；无预热请求。第一尝试是本引擎首请求，后三次已有内核暖态，但APC冷；共享主机和文件页缓存冷暖不可隔离，不做性能排名。KV明确2GiB，max_model_len8192，max_num_batched_tokens512，eager、chunked prefill、async_scheduling=false、gpu_memory_utilization=.24，其余固定；相较旧6GiB池是双方一致的资源安全适配。

模型前重新检查GPU余量至少26GiB并保存原五服务PID。全作业墙钟含启动限1200秒。独立supervisor创建唯一模型进程组，所有子进程绑核8–11，OMP/MKL/OpenBLAS/NUMEXPR均1，torch线程1/inter-op1；不改共享环境。每0.25秒读取所属进程树/proc RSS/匿名/文件页/CPU，每约1秒nvidia-smi按所属PID累加显存；采样GPU超过24GiB或RSS超过10GiB则停止自己的进程组。权重mmap加载阶段（engine-ready前）允许文件映射RSS暂超10GiB，但匿名RSS总和必须≤10GiB；同时记录原始总RSS及文件页，不能称全生命周期RSS硬限10GiB。engine-ready以后总RSS≤10GiB。采样可能漏瞬态，非cgroup硬保证。初始余量/驱动/服务、退出后五服务和自有PID清理证据全部保存。仅kill自建组，绝不处理其他PID。

代码仅原schema的read/write/run_tests/finish，写入路径固定intervals.py，原AST白名单拒绝import/属性/任意调用；无shell执行模型内容。原CPU2秒、地址空间512MiB、墙钟4秒边界复用，诊断/holdout最多5秒，加文件输出1MiB限制；工具子进程继承核绑定。AST不是通用沙箱；只有受控合成数据，不读秘密或调用外部程序。holdout在GPU组结束、raw传输后本地离线执行，复用原check_code.py连通分量oracle：1空+28单区间+784双区间+200固定seed随机=1013，分别报告value_and_input_passed、additional_alias_failures、严格passed；退出0不等于通过。

完整保留所有四次输入、消息、请求token IDs/输出token IDs、stream事件、每轮代码及哈希、工具原字段/新增字段、原stdout/stderr/returncode、资源、失败和最终代码；新本地raw≤100MiB，超预算停止自己的作业并保留已有证据。所有源码/协议hash在运行前封存。最终离线分析校验消息链、原文件hash、诊断与原六例对应、成功门槛、原始流/用量及资源边界。只交中文README/表/manifest/status，不作总体模型质量、多任务成功率、正式扩容收益、全部实验完成或最终跨session论文审计。matched资源比较、SLO/价格/预算仍未执行。
