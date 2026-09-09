# Mac／RTX配对投影：时间费用与功率条件候选

复用实验4-6锁定的原始projection.py及MPS/CUDA results.json，与原manifest交叉校验。两端使用相同BF16输入和权重夹具；矩阵形状来自官方Qwen3-8B Q投影4096×4096，数值夹具不是Qwen checkpoint权重。

时间字段必须按原runner解释：11组试验，每组连续16次调用加提交/同步，用总墙钟除16。下面是11个批平均时间的中位数，不是单次延迟的中位数或p95。两端仅同M、同reused/rotating模式配对；rotation不证明冷DRAM。

| 行数M | 权重模式 | MPS墙钟代理 μs | CUDA墙钟代理 μs | RTX/Mac费用率或平均功率持平比 |
|---:|---|---:|---:|---:|
| 1 | reused | 165.986999 | 42.918124 | 3.867527 |
| 1 | rotating | 182.650998 | 51.866067 | 3.521590 |
| 256 | reused | 1835.374998 | 32.648997 | 56.215356 |
| 256 | rotating | 1835.223935 | 33.477700 | 54.819296 |

定义两台整机在同一服务时间窗口的声明费用率c（抽象费用单位/小时），每次调用代理为t×c/3600。RTX/Mac费用率低于表中门槛时，RTX代理更低；等号持平，高于门槛则Mac更低。平均整机功率p采用同一窗口时，t×p可作条件焦耳代理，门槛相同。

默认费用和功率输入缺失，费用、焦耳及排名均为null。两个另列场景给定1:2、1:10的费用率，以及80/400W、80/800W的整机功率假设，仅展示代入与翻转；它们不是价格、测量或厂商TDP。未获取同期功率轨迹，实测能耗始终未知。

这是一次投影的active-time代理，未计闲置/利用率、启动、全生命周期、完整模型质量和所有权成本。MPS内部累加精度未独立验证；原始参考检查只保留报告，不在这里升级为整模型等质量。记录中Mac设备为M2 Max、RTX为PRO6000 Blackwell的实验上下文，不把不同日期和后端差异归结为芯片架构单一因素。

复现：

```sh
python3 calculations/research/paired-projection-cost/calculate.py --output calculations/research/paired-projection-cost/result.json
python3 calculations/research/paired-projection-cost/check.py
python3 -m unittest discover -s calculations/research/paired-projection-cost -p 'test_*.py'
```

独立从原始11组样本按秩找中位数并重算136项时间/费用/功率/未知值检查通过；3专项tests覆盖精确持平与两侧翻转、未知不等于零及非法输入。三场景已完成[公共CLI/固定输入/正文接入验收](../paired-projection-integration/acceptance.json)，研究候选保留为独立核对记录；C24面积、封装、互联与其余成本要求仍待，不勾整项。
