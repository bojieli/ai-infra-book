# Morphlux：分配形状、物理路径与恢复

围绕当前 6.4→7.5／7.6→11.3，选读 Morphlux 公开 v3 的物理页 2–11、14–16，共十三页；实际查看页 5、9、10、15、16。[正文范围](../../../proceedings/ASPLOS/2026/morphlux-reading.json)与[实现读取范围](reading.json)分别保存。没有读完正式出版全文，也没有执行作者代码、Gurobi、模型或硬件控制命令。

本批十八份响应中十七份成功，一份出版商 PDF 请求返回 403。十份说明／代码／脚本全文已读，`scheduler-block.py` 只读 89–200、353–543 行；三个 GitHub 响应只读身份、提交与路径元数据。另读六处官方 HTML 范围。搜索得到的第三方摘要不作为技术依据。

## 版本与平台

[Cornell 2026-03-20 的正式题名讲座](https://www.cs.cornell.edu/events/systems-research-seminar/reconfigurable-torus-fabrics-multi-tenant-ml)明确把 *Reconfigurable Torus Fabrics for Multi-tenant ML* 与 Morphlux 联系起来，比仅凭旧题名与作者对应更直接。不过，归档正文仍是 2025-10-03 的 arXiv v3、16 页；正式出版条目为 19 页，不能推定内容完全一致或将旧稿加速比移给最终版本。

论文中的三个验证层次分别记录：

| 层次 | 实际条件 | 能支持的判断 |
| --- | --- | --- |
| 设计 | 芯片堆叠在可编程光子 interposer 上，靠近 SerDes 改变连接 | 重定向端口可能改变分配能力；生产封装、热与光损耗仍有条件 |
| 硬件原型 | 四台 RTX 6000 Ada 48 GB 服务器，经 PCIe、NIC、光模块接 iPronics；每台使用两个 10 Gbps 端口 | 检查重连、端口利用与该路径上的 NCCL／小模型微调；不是芯片直接键合的生产系统 |
| 大规模模拟 | 64 块、每块 64 TPU 的分配模型；按样本分配／释放，结合 FlexNet 与设定的 ICI 争用折损 | 比较给定需求分布和通信假设下的分配、吞吐；端口利用率不等于 MFU |

稿件页 4 先说租用 TPU v3，后又称测量 TPU v4；页 3 还将 64-chip rack 称为 Pod。它们不作为硬件规格。[Google TPU v4 官方文档](https://cloud.google.com/tpu/docs/v4)所读段落说明 Pod 为 4096 芯片，配置由芯片维度决定，并区分 mesh／torus 条件。书中不能把所有小切片都画成自带闭合环的 torus。

模拟设置只明确 transformer 的 hidden size 为 4096，图例又使用 BERT 名称，不能称为完整 Llama。ICI-30／50／75% 是模型中的带宽折损假设，不是普遍实测。小原型用两卡 DDP、Llama-3.2-1B、Wikitext-103 的 128 个样本；没有据此推断 Qwen3、V4 或 K3 的质量和性能。

## 从资源分配到可执行路径

作者仓库固定在 `36d308bb539394918e303d4bd8c329932f36108a`，提交时间为 2025-01-31，早于所读 v3。[README](morphlux-readme.md)给的是研究工件环境，不能当作完整推理框架集成。

[`scheduler-block.py`](scheduler-block.py)所读部分先找连续资源，再把空闲服务器映射到逻辑拓扑。分配求解器最小化最忙边的电路数；该求解器和调用路径没有把它同一个物理纤维数硬上限比较。[候选路径函数](scheduler-graph-utils.py)虽然名为 `without_overlap`，实际按已有边占用排序候选，并不排除所有共用边。得到一个数学解后，仍需验证每条实际链路的容量及硬件可实现性。这里没有声称所有工件路径都缺少检查。

[普通带宽分配器](bandwidth-allocator.py)将注入能力分给各通信组，并取组内最小值，还受 `link_bw` 上限和整数分配影响；[另一个 ILP 分配器](bandwidth-allocator-ilp.py)表达了物理边与注入约束。两者不能与机架碎片分配器的目标混为一谈。图构建器也保留 wrap-around 表示的 TODO，因而未用下载工件作为教材的精确拓扑模拟器。[cost-model.py](cost-model.py)仅有形状相关系数，alpha／beta 的代入仍是 TODO，不等于完整 FlexNet 的执行预测。

## 重连、重启和恢复训练进度

图 8c 标出重新连线完成／启动作业为 1.1 s，NCCL 同步为 4.5 s，第一步完成为 25.6 s。摘要和讲座中约 1.2 s 的替换不能改写为完整训练恢复时间；表 1 与图 8a 是平均 epoch 时间，正文有时写 iteration，引用时保留分母。

固定 [fault-worker.py](fault-worker.py)使用预设两套光路、重写 hostfile、复制 `checkpoint_epoch_0.pt` 后重新启动 MPI。它显式设置 `NCCL_IB_DISABLE=1` 和两个 socket 接口名。[NCCL 2.31.2 文档](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-ib-disable)所读范围确认这会关闭 IB／RoCE transport；接口筛选本身不保证指定带宽。该文档版本也不是原型安装版本的证据。

[训练入口](ml-run.sh)仍含 `train_<>.py` 占位符。[公开 Llama 文件](train-llama3.py)从原始模型创建新 optimizer，按 epoch 保存 `model.state_dict()`，没有读取恢复状态的路径。因此这些工件不足以验证参数、optimizer、数据位置与随机状态的完整续接。也不能因为 worker 复制了 checkpoint，就宣称所示训练已经从它恢复。模型脚本以 padded input 元素计 token，实验吞吐不能未经检查就当作有效训练 token 吞吐。

故障备用量还依赖 SRG 的范围、独立性和时间可用率。稿件按 `Pr(F≥K)` 选 K 个备用，作为覆盖最多 K 个同时故障的条件是保守的；精确溢出事件是 `F>K`。没有采用“四个备用芯片适用于任何集群”的说法。

## 书中采用的内容

在[现有集合通信案例](../../../../case-studies/network-planning-and-collectives.md)中，用同一 Qwen3 激活的 prefill／decode 载荷比较启动与带宽项，再用十六个位置、八个空闲单元说明分配形状。增加光路之后仍检查最窄割集；把一次准备成本除以每次调用的收益，决定是否值得重构。独立计算见[算例输出](../../../../research/2026-infra-survey/torus-allocation-arithmetic.json)，不移用论文加速比。实验沿用 6-4、7-8、11-3，图沿用 11-4。
