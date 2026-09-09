# drafttrace 状态

2026-09-09：用户限定的第一轮 draft/verify/有效上下文回退观测批与本worker QA已完成，交主agent统一回填；不代表全8-5完成，不做最终跨session审计。

仅写 experiments/ch08/08-05/kernel-trace/ 与本status及远端同名目录。原75文件、正文/总进展/inventory/research/references/其他实验保持只读；未执行/修改/复制calculations、未联系owner；未git提交、未派生agent、未改共享依赖、未停止原服务。

执行：启动nvidia-smi与/proc重验仅原五PID，空闲36294MiB。指定vLLM0.23 Python、固定target缓存及已有DFlash revision，无下载。独立runner所有写路径改到kernel-trace，保存runner.diff；进程内NVTX/record_function/元数据wrapper，保存原函数源码/hash与wrapper.diff。CPU限制4核/线程池4，Torch22GiB、24GiB监控。K7短lookup单并发smoke exit0，完整token与原4条参考一致，Torch profiler采到真实CUDA kernel/copy。

随后AR-V1/K7/K15各原四输入、两并发，同形状预热一轮+观测一轮，全部exit0；传输exit0之后分析，24 raw文件远端/本地hash一致。12观测请求逐token/text/stop与原参考一致，质量仍各2/4，math失败保留，不声称错误答案加速成功。

结果：35条带request ID的spec sampler请求行（K7 20含2零draft，K15 15含1零draft），实际验证logits行146/225；draft126/210、accepted92/94，官方聚合独立守恒；首拒绝10/12条。实际fallback token、-1尾部、设备拒绝数与有效context修正均可核验；如K7首math step2接受1、拒绝6、context61→55，K15拒绝14、69→55。

真实GPU trace保留CPU范围、kernel/copy/memset及CUDA correlation，单列观测readback。物理KV清零/页释放索引unknown，无独立rollback kernel API；K7/K15有104/92个未归因GPU活动原样保留，不强分摊。CPU submit不冒充GPU时长，并发GPU仅batch粒度，profiler扰动时间不重排性能。

QA：主分析283/283、独立raw复核1182/1182、源码11/11、传输24/24；首次独立复核3个旧ID失败完整保留，源码证明execute_model入口尚未更新input_batch，实际逐行归因用forward/sampler当轮ID，无重跑/改原始记录。两张图已视觉检查并修正图例空间，中文README/BOUNDARIES/未完成范围齐备。

显存采样峰值AR17718/K7 19924/K15 20814MiB，均低24GiB；0.5秒采样不排除瞬时峰。退出复核仅原五服务，60956MiB，无worker残留。raw精确377446575字节（约360MiB），所有本地产物约403MiB有效数据，低1GiB。远端保留同名raw与私有缓存；最终产物同步exit0，远端按manifest逐一复核64/64文件hash及大小通过，worker本有界任务已结束。
