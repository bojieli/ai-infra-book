# 执行前诊断约束
仅读取旧 main_m8 保存输入、路由与 assembled 真实六专家权重；clamp=10、factor=1.5。一次原函数观测调用及一次同输入无观测控制，不运行其他用例。源 SHA 必须匹配旧快照。trace 在 GEMV2 down 被覆盖前及 return 同步 CPU 复制；TorchDispatchMode 只记录原 aten mul 和 sum 的输出，不替换算法。保存两次实际 autotune 选择，不固定/强制配置。
原逐元素门槛 abs(y-ref)<=.02*abs(ref)+.002*RMS(ref)，relative-L2<=.01，有限性要求均不变。阶段差异用于定位，不构成新验收标准。执行及传输退出后方可 CPU 分析；独立 FP64 oracle 读取旧 raw，逐阶段重算，并从 GPU 实际上一边界重算下一阶段。旧输出逐位对比，未复现时不得把新阶段归因直接视为旧阶段实证。
资源：单进程 GPU<=3GiB，启动前空闲>=4GiB，allocator 2GiB，四核/四线程，进程树 RSS<=8GiB；watchdog 仅终止自身会话，另设15分钟截止。全部 cache/tmp 在独立目录。新增本地 raw<=350MiB。旧目录只读，不接触 calculations，不改共享环境，不提交 git。
