# 实验 10-5：固定 Megatron Core 流水执行交接

**结果：四阶段流水尚未执行；已新增[官方无流水GPU基线](single-gpu-pipeline/README.md)。** 真实36层小模型、8微批完成前向/反向/SGD，输出和梯度逐位一致、参数更新通过门槛；保存实际生命周期、allocator和profiler。以下保留原四卡交接说明，10-5整体仍未完成。

## 已核对的范围

已读 `outlines/extensions/10-训练系统.md` 的10-5：Qwen3-8B的36层、四阶段各9层，以及固定Megatron受支持流水trace和真实激活寿命要求。现有 `references/framework-history/2026-09-09/spindle-wavefront/NOTES.md` 记录固定Galvatron研究分支；已读其 `sources/spindle-hybrid-model.py` 前105行，调用的是Galvatron gpipe/pipedream_flush。另读 `references/framework-history/2026-09-08/rollout-tail/rollpacker-megatron.py` 前110行，其官方调度import被注释，实际从ROLL `mcore_sched` 导入。这两者不能证明官方Megatron流水已运行。限定检索中没有找到本地Megatron官方调度源码快照，因此新增固定 `core_v0.16.0`，不是声称它是最新版本。

本目录 `sources/tag.json` 固定tag指向提交 `3bec9aa97dda898d16ff5a89bac0ed2b6682b172`；`sources/manifest.json` 保存十份官方源码URL和SHA256，完整源码归档也保存在sources。官方[0.16.0安装说明](https://docs.nvidia.com/megatron-core/developer-guide/0.16.0/get-started/install.html)要求CUDA/cuDNN/NCCL，HTML已保存。

关键源码依据：

- `sources/megatron/core/pipeline_parallel/schedules.py` 第596、983、2138行：无流水、交错流水、非交错1F1B均无条件 `torch.zeros(..., device="cuda")`。
- `sources/megatron/core/pipeline_parallel/p2p_communication.py` 第308–323行：前后接收张量的device直接取 `torch.cuda.current_device()`。
- 官方 `sources/examples/run_simple_mcore_train_loop.py` 的分布式初始化使用CUDA设备和NCCL，模型随后 `.to(cuda)`；`use_cpu_initialization=True` 不是CPU训练支持。

以上只证明该固定版本所选官方路径不适用于本机CPU，不能扩大为所有历史版本或第三方移植永远不能在CPU运行。未安装Megatron或numpy是额外环境缺项，并非仅凭import失败推出CUDA必要性；本轮不安装无助于解除设备阻断的依赖。

## 本机原始记录与复跑

在仓库根目录执行 `bash experiments/ch10/10-05/run_cpu_probe.sh`。也可设置 `PYTHON` 为已有CPU Torch解释器的绝对路径；不修改共享venv。每次结果新建在 `results/cpu-时间-PID/`，保留命令、stdout、stderr、退出码及 `ps` 共存快照。

本轮实际环境 macOS 26.6.2 arm64、Python3.14.7、Torch2.14.0，CUDA构建为null，CUDA/NCCL不可用，Gloo可用；numpy/Megatron未安装。真实预检退出2（预期阻断，不是训练异常）。仅使用1个intraop和1个interop线程，库线程环境限制为1；峰值RSS约198MiB，低于8GiB。共用CPU，不能做因果性能排名。未使用GPU/MPS/SSH/远端，未安装依赖，下载量记录于validation.json。

## GPU交接执行方法

本worker未执行以下命令，也未申请或启动设备。需要另一个获授权的 Linux x86_64、Python3.12、四张支持CUDA的NVIDIA GPU和NCCL点对点通信环境。为小模型建议预留每卡2GiB空闲显存、主机8GiB内存、四个计算CPU线程；这是待测资源建议，不是实测峰值或保证。安装/运行时Python及NCCL还可能创建辅助线程，宿主资源管理应另行限制。Qwen3-8B需要重新配置资源，不在本交接小模型范围。

在独立GPU环境中从本目录执行（依赖下载属于未来GPU交接，不属于本CPU worker已下载量）：

```bash
python3.12 -m venv .gpu-venv
source .gpu-venv/bin/activate
python -m pip install 'torch==2.9.1' --index-url https://download.pytorch.org/whl/cu128
python -m pip install 'numpy==2.2.6' 'packaging==25.0' 'einops==0.8.1' 'PyYAML==6.0.2'
python -m pip install --no-deps sources/megatron-core-3bec9aa.tar.gz
bash run_gpu_handoff.sh
```

此依赖组合是完整候选命令，尚未经GPU环境验证；若安装/import/API失败，保留失败日志并以新run目录修复，不能声称已验证兼容。Torch2.9.1与本机2.14.0不是同一构建。

`gpu_handoff.py` 使用官方 `get_forward_backward_func()` 和官方P2P，不实现自制调度器；36个宽度16的真实残差块只是最小接口模型，并非GPT或Qwen。固定batch、seed、数值门槛、参考及观测口径见 [PROTOCOL.md](PROTOCOL.md)。脚本包含一次真实前向/反向/SGD、逐元素对照、profiler、真实保存张量事件和分配器快照，torchrun stdout/stderr/退出码均保留。首次GPU执行前必须阅读协议。

## 验证与尚未完成

本轮通过Python语法、shell语法、固定源码散列/归档一致性检查，以及GPU程序在CPU环境下明确拒绝的检查。见 `validation.json`；这些检查不等于GPU运行通过。没有图，因此没有可冒充QA完成的图表。

未完成：四rank真实执行与数值通过、实际激活生命周期和分配器分析、trace视觉QA、Qwen3-8B模型、微批扫描、填满排空对照、不均衡修正、MoE梯度桶及多模态分支选做。未修改正文、inventory、PROGRESS、其他实验或calculations，也未提交git或启动其他agent。
