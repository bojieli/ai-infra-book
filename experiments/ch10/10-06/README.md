# 10-6 检查点重分片与继续训练（部分交付）

实际执行 PyTorch 2.10.0+cu128 DCP 保存／加载，验证改变保存进程数和张量切分方向后能否继续同一次小模型训练。运行在 RTX 主机的 CPU／Gloo 多进程上，未使用 GPU；**不是多机训练、Qwen3 全参数训练或存储吞吐基准**。题目的输入带宽与大模型状态预算继续由计算任务 C56 负责。

## 实际结果

模型为 `Linear(129,257) → tanh → Dropout(0.2) → Linear(257,17)`，FP32、AdamW、固定合成数据。先更新四步，保存19项参数／优化器／随机数和数据位置张量；原始检查点包含两个数据文件及元数据，共518,512字节。所有输出文件保留在 `results/checkpoint/`。

| 路径 | 第一层权重各rank局部形状 | 最大rank的API耗时 |
|---|---|---:|
| 2进程按行保存 | `[129,129]`、`[128,129]` | 296.78 ms |
| 2进程原布局恢复 | `[129,129]`、`[128,129]` | 48.60 ms |
| 3进程按列恢复 | 三份`[257,43]` | 64.58 ms |
| 1进程合并恢复 | `[257,129]` | 49.61 ms |

三个恢复路径的完整状态哈希均与保存点一致；恢复后第五步loss均为1.3159840106964111，参数、Adam状态、CPU随机状态和数据随机状态与未中断第五步逐位一致。负对照保留恢复权重和随机状态、清空Adam动量，验证器在所有恢复rank上检出下一状态不一致。

加载前所有目标张量置零，因此不能靠重新初始化出相同训练状态来掩盖漏载字段。行分片特意使用257行，使两份大小不等；验证器逐坐标检查保存分片的完整覆盖和无重叠，而非仅比较文件大小。数据用独立Generator产生，保存其状态及样本步游标；Dropout使用的CPU全局随机状态另存。

## 独立运行

需要Linux上的PyTorch 2.10.0与Gloo，已有torch安装即可。每次实验使用一个新的结果目录；没有外部数据下载，也不需要相邻实验文件。

```bash
python -m torch.distributed.run --standalone --nproc-per-node=2 run.py save --root results
python -m torch.distributed.run --standalone --nproc-per-node=2 run.py load --root results --axis 0
python -m torch.distributed.run --standalone --nproc-per-node=3 run.py load --root results --axis 1
python -m torch.distributed.run --standalone --nproc-per-node=1 run.py load --root results --axis 0
python inspect_checkpoint.py results
python verify.py
```

`run.py` 各rank只用一个CPU计算线程。保存点的完整逻辑状态转成DTensor，交给真实DCP写入和重分片；恢复后通过collective重组完整张量，再用相同单进程数学路径执行下一步。因此这里证明的是**检查点布局转换和状态恢复**，没有证明不同分布式训练归约路径也能逐位一致。

`inspect_checkpoint.py`读取DCP实际元数据，保留每个逻辑张量的全局形状、保存片段坐标和文件SHA256。`verify.py`只需标准Python即可离线检查文件、坐标覆盖、各rank恢复结果和下一步状态。`reference.json`来自真实未中断训练；各rank记录绑定本次`run.py`的SHA256。

## 计时边界与未完成项

API计时在进程barrier后开始，包含DCP调用及其内部协调，不包含torchrun启动、模型训练、DTensor构造和恢复后的完整张量聚合。采用该版本默认FileSystemWriter，`sync_files=True`；API完成不等于已经证明断电后的硬件持久性。每条路径只运行一次，文件很小、共享本机文件系统，不能用这些时间排名布局性能或外推大模型带宽。

本组覆盖参数、Adam、Dropout RNG和可再生成合成输入的位置。尚未覆盖真实DataLoader预取队列、packing残留buffer、异步后台持久化、受控故障、输入与检查点竞争、672 MiB Qwen gate状态及完整大模型训练。10-6仍为部分交付；10-7的异步恢复点要求也没有被此处同步save代替。

全书第一轮完成后仍需按实验进展文件执行论文增补复核。
