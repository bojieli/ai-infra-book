# 实验 10-5 worker 状态

状态：本有界任务已完成交付；实验真实训练为 BLOCKED_CPU_ONLY，GPU交接未经执行，不标为实验完成。

边界：仅写 experiments/ch10/10-05/ 和本状态文件。正文、inventory、PROGRESS、skeleton、research、references、其他实验只读；未操作calculations。未提交git、启动agents/Codex或联系其他session。

结果：固定 Megatron Core core_v0.16.0 / 3bec9aa97dda898d16ff5a89bac0ed2b6682b172，保存完整8.44MB源码归档及十份关键文件/散列。三种官方调度都无条件分配CUDA张量，P2P接收直接使用CUDA current_device。CPU初始化选项不提供CPU执行路径。

实际环境：Mac arm64 / Python3.14.7 / Torch2.14.0 CPU，CUDA/NCCL不可用。真实预检退出2；GPU脚本CPU保护检查退出1。stdout/stderr/退出码、共存进程和RSS已保存。CPU库线程限制1，intraop/interop各1，预检峰值207601664 bytes；未用GPU/MPS/SSH/远端，未安装或修改venv；下载8911853 bytes，低于500MB。

交付：experiments/ch10/10-05/README.md、PROTOCOL.md、gpu_handoff.py、run_gpu_handoff.sh、probe_cpu.py、run_cpu_probe.sh、validate.py、validation.json、sources/、results/。GPU候选用官方1F1B调度器和36个小型真实残差块，含逐元素参考、梯度/更新检查、profiler、真实saved-tensor生命周期和allocator snapshot；不是Qwen3，也不是自制CPU调度。

验证：Python AST、bash -n、十份源码与完整固定归档字节/SHA256一致性通过；CPU阻断保护检查通过，负例保留。无图、无模拟结果、无GPU训练trace或性能排名。

未完成：GPU候选依赖/API实机验证、四rank真实执行/数值/trace和激活寿命QA、Qwen3-8B及微批扫描、其他10-5扩展。详见README和事前协议。此次交付不改变全书或其他session状态。
