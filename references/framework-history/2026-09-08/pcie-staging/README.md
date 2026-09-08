# PCIe 中转路径：TCCL 与 NCCL

本批归档 16 份成功响应，记录在 [sources.json](sources.json)。读取范围与原件 SHA-256 见 [reading-proof.json](reading-proof.json)。只静态阅读文档和源码，没有编译、导入或执行下载内容，没有 GPU／模型测试。

TCCL 固定提交为 `351d064856e322ec6e4546808e7d1e433d24f941`（2025-07-08）；它是 ASPLOS 2024 的研究系统，此提交时间不代表论文或特性的首次发布时间。NCCL 当前比较固定 `7b83616df3ae082a1f32bb74c27458bfe8153a13`、2.31.2-1，release 响应标明 2026-08-11。历史基线只使用标签 2.18.3-1，不从当前 release 列表中不存在旧版本推断日期。

| 原件 | 本次实际读取与用途 |
| --- | --- |
| [TCCL README](tccl-README.md)、[AE](tccl-AE.md) | 完整文件；路径搜索与历史依赖。NCCL 2.18.3、PyTorch 2.0.1 等条件不能代表当前安装 |
| [作者文章](tccl-author.html)、[提取正文](tccl-author-body.txt) | 完整文章文本；缓冲放置与并发测量。未数字化图中测点，未采用性能数字或最优性证明 |
| [TCCL SHM](tccl-shm.cc)、[分配入口](tccl-shmutils.cc) | 声明行段；所选 NUMA 编号传到分配调用。未追读 `tcclSetNuma` 全部实现 |
| [搜索入口](tccl-search.cpp)、[benchmark](tccl-benchmark.cpp) | 声明行段；默认数据量、迭代、候选开关、计时与搜索。未通读所有候选生成和调用链 |
| [kernel wrapper](tccl-kernels.cu) | 完整文件；复制启动和完成同步。名为 single_channel 的 wrapper 实际启动 10 个 block，不能凭函数名推断资源量 |
| [NCCL 2.18.3 SHM](nccl-2.18.3-shm.cc) | 声明行段；历史 sender／receiver memcpy 选项、Simple 协议路径 |
| [NCCL 2.31.2 SHM](nccl-2.31.2-shm.cc)、[allocator](nccl-2.31.2-alloc.h) | 声明行段；SHM/direct、cuMem／传统路径条件、当前 GPU 的 HOST_NUMA_ID 分配 |
| [NCCL 2.31.2 runtime guide](nccl-2.31.2-runtime.rst) | 第 1–112 行；包括完整 shared memory／cuMem 小节。2.23、2.24、2.26.5 的边界保留 driver／runtime 条件 |
| [NCCL shmutils 候选](nccl-2.31.2-shmutils.cc) | 仅检索定位，未采用；此文件是 bootstrap shared allgather，目标 allocator 在另一文件 |
| [TCCL commit](tccl-commit.json)、[tree](tccl-tree.json)、[NCCL releases](nccl-releases.json) | 身份、日期与路径定位；不把整个 JSON 归为正文阅读 |

TCCL 正式 [PDF 入口](https://dl.acm.org/doi/pdf/10.1145/3620666.3651362)本次返回 403，[失败响应清单](../../../proceedings/ASPLOS/2024/selected-sources.json)和原始响应均保留。作者文章、仓库与静态源码读取不计入“论文正文重点阅读”。没有采用作者报告的加速比，也未审计搜索最优性或完整 AE 可复现性。

TCCL 源码的 `nbytes / us_avg` 采用一次传输的数据量与完成时钟，不是并发链路带宽之和。同步能约束完成时刻，不能由此断言所有 GPU 的起始瞬间完全相同。历史 SHM memcpy 选项与当前文件差异也不能直接推广成“当前 NCCL 没有任何 CE 路径”。

采用到第 6.5、7.3 及原有实验 6-6／图 6-6：[推算和取舍](../../../../case-studies/pcie-staging-and-numa.md)。四卡环的数字是明确假设的物理流量下界，不能替代实测，也不是 TCCL 论文中的实验数据。
