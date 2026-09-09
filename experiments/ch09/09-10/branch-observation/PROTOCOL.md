# 9-10 分支观测：事前协议

状态：准备；GPU 必须等 cachebranch/GPU-RELEASE.json 并在远端 /proc 核实其 8-5 PID 全部退出。无释放证据不启动 worker。不停止现有服务。

封存对照：native-storage-observation 已补齐 spawn 存储观测。两次单请求均 cached_tokens=1008；两次 8 请求同前缀波首完成 cached_tokens=0，256 成功 get / 64 key。max_running_requests=1，runtime pool 双字段=4096。baseline.json 独立保留旧请求完整输出；这些结果不是本批分支证据。

本批唯一模型执行变量为附加观测：模块顶层 sys.settrace/threading.settrace 覆盖 spawn，记录实际行、返回、局部量及进程身份；不更改分支，不重复 storage-only 计数，不修复实现。观察会影响执行开销及调度时间，不能用本批延迟或“未出现旧现象”作因果否定。系统资源边界改为本任务 24GiB 单 worker、4 CPU 线程、端口18190/18191，保留资源状态。

固定 config/inputs/reference/cache-manifest 与旧 native 文件逐字节一致：Qwen3-8B revision b968826d9c46dd6066d109eabc6255188de91218；1024 输入、greedy temperature0、ignore_eos、16 输出；全65文件 fixture；mem_fraction_static=.75、max_total_tokens=4096、max_running_requests=1、wait_complete。每组独立新 engine 与校验缓存副本，1/8请求各两 trial，顺序沿用seed9102。native rid=native-{index} 保持旧语义，group/PID/输入 SHA 区分不同 trial。

源码核实（sources/ 为固定环境原件，source-manifest.json）：
- cache_controller.prefetch_rate_limited 返回 occupied >= capacity，capacity=max(0,int(.8*(host.size-device.size)))。记录实际返回及占用/容量。
- HiRadixCache.prefetch_from_storage 可因禁用、短于阈值、限额或 host 分配失败提前返回。记录实际行、ongoing 前后及 operation request_id。
- check_prefetch_progress：无 ongoing 直接 True；operation.host_indices is None 直接 True；can_terminate=False 返回 False；可终止时插入 host，loaded_from_storage=min_completed_tokens-matched_length 后返回 True。True 不能单独解释成有效命中。
- wait_complete 比较 operation.completed_tokens 与 hash 数*page_size，另允许 operation 已终止。记录 can_terminate 实际返回、completed、operation_terminated。
- scheduler 检查 False 时 continue；True 后 pop_prefetch_loaded_tokens（无记录默认0）、init_next_round_input、adder。记录实际执行行和请求ID。
- Req.init_next_round_input 的返回状态记录 device prefix 长度和 host_hit_length。ScheduleBatch.prepare_for_extend 入口/出口记录真实入选请求、prefix、storage_hit_length及 cached_tokens 分项。保持长度观察不读取 GPU tensor 内容、不额外调用有副作用的缓存方法。

原始 JSONL 按 PID 分文件，无事件抽样或覆盖；monotonic_ns、seq、PID/PPID/TID、request_id、输入 SHA 关联。line 事件发生在该行执行前；return 记录实际返回，不拿前一行快照假装后置状态。prefetch operation 的 hash_value 保存实际共享 key。请求发送/完成在同远端单调时钟上，API meta_info.id 必须精确对应 rid；无精确关联则报告 unknown，不强行归因。源码路径与 SHA 不符直接失败，不启动模型。

每组预算：worker600秒、请求波120秒；资源占用超过24576MiB停止自己的已核实进程，保留失败。仅按 /proc PPID 链记录子进程及 starttime；清理前重验 starttime，逐 PID 处理，不按名称或进程组盲杀。所有组之间及最后等待自己 PID 从 nvidia-smi 消失。保存 worker/controller/transfer exit 与失败。数据下载不含重复 cache fixture 副本；保留 manifest、准备验证，独立只读 fixture 已有来源。本地实验总量<1GiB。

分析预先判据：4组18输出ID及text逐项精确等于旧9-8参考；实际 ServerInfo max_total_num_tokens 与 internal_states.memory_usage.token_capacity 均4096，config逐项匹配；事件 PID 存在安装证据及 /proc 后代证据；首完成按 end_s 排序，再匹配 request ID。每请求展示 rate decision、ongoing、progress 分支/返回、pop loaded、init匹配、实际prefill入口与API结果。若缺证据或出现失败，保留原始记录，不重复盲跑。

仅交付此有界证据包给主agent复核；不做跨session审计、不回填正文、不宣称全9-10完成。calculations 不执行、不改、不复制。
