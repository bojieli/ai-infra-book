# V4 六专家阶段诊断状态

- 状态：完成，待主 agent 统一审核；未执行全书跨 session 审计。
- 交付：experiments/ch02/02-05/expert-stages/README.md、standalone run/launch/analyze、原始阶段/输出、SHA 来源、逐元素和逐失败分析、环境/资源/退出与 manifest。
- 原输出已逐位复现；同输入无观测控制亦逐位相同。原 FP64 门槛仍为 10/32768 失败，relative-L2=0.0003924070767719118；运行 exit 0 不代表数值通过。
- 定位：GPU 实际上一阶段的 CPU FP64 重算显示 GEMV1 新差异11、activation 新差异4、GEMV2 新差异11，masked/product/reduce/final 新差异0。原10个失败的全部误差在实际 activation 边界接续时重现；三个单激活坐标干预分别重现 token 2/6/7 对应失败。另一个激活差异在 token0，不对应旧失败。
- FP32 NumPy 激活对照四点均匹配 GPU BF16，支持精度边界机制；未采集 GPU SiLU 内部 FP32 运算或 GEMV accumulator，不能断言指令级根因或内核全面正确。旧 autotune config 未保存；本次两 GEMV 均 N64/K64/4warps/2stages，未出现输出漂移。
- 资源：指定 Python/Torch2.11cu130/SG.5.13.post1；PID2812495 exit0，GPU sampled1038MiB，RSS1387700224bytes，4CPU线程，启动空闲36294MiB。原始传输退出0后才分析。本地 raw约4.65MiB，全部约22.1MiB。
- 严守范围：旧目录只读，未改共享源码/环境、未执行/复制/修改 calculations、未下载模型、未跑完整模型/旧15用例、未派生 worker、未联系 owner、未提交 git。
