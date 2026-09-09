你是主实验 session 启动的独立 Codex CLI worker。任务：推进实验 10-5 的真实流水训练执行记录，优先检查固定 Megatron Core 的受支持路径；阅读 outlines/extensions/10-训练系统.md 的 10-5 要求和已有相关固定源码。不要实现计算模拟来替代真实执行。

唯一可写实验目录 experiments/ch10/10-05/，以及本任务状态 experiments/parallel-workers/pipeline/status.md。其他文件只读。不要修改正文、inventory、PROGRESS、skeleton、research、references、其他实验，更不要操作 calculations/（其全部计算由另一个 session 正在做）。不要提交 git、启动新的 agents/Codex、联系其他 session。

先保存 status.md 说明已开始及具体实验边界。选择在实际可用硬件上受支持的最小真实模型/执行路径；本 worker 仅可用 Mac CPU，禁止 GPU/MPS/SSH/远端任务，CPU 总线程不超过4、内存不超过8GiB。已有 experiments/tools/collective-cpu-venv 是 Python3.14.7/Torch2.14 CPU（无numpy），experiments/.venv 有绘图。不可修改共享venv，可以本目录独立venv安装小依赖，下载上限500MB。如果 Megatron 确实需要 CUDA 且无CPU支持，保存固定源码和实际环境依据、完整可运行GPU脚本及所需资源作为交接，不冒充完成；不要自制CPU调度替代并宣称Megatron实跑。

如可真实执行，事前协议固定相同全局batch、模型、seed、微批和数值门槛，保存原始trace/输出/退出码，逐元素比较参考。实际激活生命周期需真实张量/分配观测，不用公式计算替代，不将可见张量bytes当RSS峰。记录资源共存，不能用共享CPU时延做因果性能排名。所有结果负例失败也保留，目录独立可运行，中文README清楚限定范围，图需要QA。完成后汇报交付目录、验证、未完成项。只做这一项有界任务，不追全书，不做最终跨session审计。
