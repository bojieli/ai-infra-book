你是授权的独立Codex CLI worker，负责9-10 HiCache分支观测缺口。已有 experiments/ch09/09-10/cache-mechanism 与 native-storage-observation 已封存，禁止修改或无目的复跑。阅读其README/代码/实际sources，明确：单请求first cached_tokens1008；8请求同prefix波first completed cached0但get256/64key均成功；scheduler max_running_requests1，storage token pool实际4096。旧native缺日志已另补完成。现在只为定位真实prefetch/scheduler分支追加必要观测，不重复旧storage-only计数。

唯一可写本地 experiments/ch09/09-10/branch-observation/、本任务状态 experiments/parallel-workers/cachebranch/status.md；远端同名实验目录。其余所有实验/正文/inventory/PROGRESS/references/research只读，calculations不执行不改不复制，不联系其他session，不再派生agents/Codex，不git提交。

先准备协议/观察代码。GPU必须等待主agent写入 experiments/parallel-workers/cachebranch/GPU-RELEASE.json 且确认其中8-5 PID已实际退出后才可启动。不要根据状态文件自行推断旧进程已死；GPU暂未释放时可以核对源码、写观察脚本。允许ssh只读准备，不停止任何已有服务。最终GPU预算24GiB单worker，使用既有SG环境 /home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv（SG0.5.13.post1），CUDA和模型/缓存配置照native-storage-observation，不修改共享环境。只清理自己按/proc证实拥有的子进程，等待显存释放，不匹配名字乱杀。服务端口18190/18191。数据上限1GiB本地，CPU4线程。

独立保存新observer/source。优先模块顶层安装钩子以进入spawn子进程；记录安装PID和实际事件PID。针对cache_controller的prefetch rate-limit占用/容量判断、ongoing_prefetch是否存在、check_prefetch_progress分支、请求进入prefill前实际可用prefetched长度/匹配长度和首完成request_id建立实际事件链。必须从固定已安装源码核实精确方法名/返回语义，不能从成功get反推有效命中。若需私有代码插桩，记录前后源hash/差异，只增加观测，不改变分支或修复逻辑。保存单调时钟、请求ID/共享prefix key与进程身份，可关联事件；不要声称已定位仅凭源码候选。

复用相同输入1024tokens、16强制greedy输出、模型revision、全缓存fixture、实际pool4096、mem_fraction_static.75、max_running_requests1、wait_complete，1请求与8请求波各2trial。先事前协议说明唯一变化为观测，保留原输出对照；没有精确request关联则明确未知，不强行归因。保留全部原始事件、实际解析ServerInfo、输出token与原9-8参考比较、worker/controller/transfer退出、失败、来源hash，standalone运行/分析/README/必要图QA。只做此有界原始事件证据实验，不做最终跨session审计，不宣称全9-10完成。完成后交主agent统一复核回填。
