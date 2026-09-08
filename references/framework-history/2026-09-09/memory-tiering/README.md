# PACT、Camp 与推理框架的内存管理

围绕当前 6.6→9.3／9.5，核对访问频率、停顿归因、内存交错与真实缓冲路径。读取范围见 [reading.json](reading.json)：17 份响应中 15 份成功，两份 Linux 原始文本请求返回 429，随后改用官方同版本 HTML；失败正文原样保留。七份文档／代码全文已读，六个 HTML 节点及 Intel 手册两个物理页面选读，五份 GitHub 响应只读声明元数据。另重读三段既有 vLLM 固定快照。下载代码未执行，也没有安装内核或运行 GPU。

## 正文中的判断与适用范围

- **PACT**：选读物理页 4–10、13–14，实际查看页 4、6、14，共九页正文文本／三张图页。[页级记录](../../../proceedings/ASPLOS/2026/pact-reading.json)区分其余未读页面。20 ms 窗口用 `k × LLC misses / MLP` 估计停顿，再按采样比例归到页；同窗口同层内仍按频率排序，混合访问流的因果归因是已声明限制。实验用 Skylake 远端 NUMA 和 uncore 限频模拟 CXL 延迟，不能称为真实 CXL 扩展器验证。
- **Camp**：选读物理页 4–13，实际查看页 7、9、10、12、13，共十页文本／五张图页。[页级记录](../../../proceedings/ASPLOS/2026/camp-reading.json)没有包含页 14–15 的应用评估。未饱和时的 demand-read 预测与带宽受限时的加权交错需要不同输入；后者通常需要 DRAM、CXL 两端运行和负载延迟曲线。内存活动周期包含隐藏的工作，不能直接换成程序停顿。其 SKX／SPR／EMR 与三种 ASIC CXL 扩展器的条件，不外推为所有 CPU 或 GPU。

两者并不推出“所有访问越本地越好”。PACT 调整页面位置和迁移时机；Camp 的交错分配还可能增加供数通道、缓解排队。模型负载、带宽饱和度与请求分布不同，DRAM 基线是否可被超过也可能不同，不能把两个实验的结论判成互相否定。

PACT 只采慢层 load 的理由，不足以排除有限写缓冲带来的反压。Camp 对 store 的讨论补了这层约束，但“每次 store 都发 RFO”也不宜原样教给读者。[Intel 优化手册 248966-050US，2024-04](intel-optimization-v050.pdf)的物理页 328／印刷页 9-5 明确给出 non-temporal store 的例外；这不是 GPU 存储协议的说明。

## 论文与可下载实现的差别

| 证据 | 论文／历史条件 | 固定实现中已核的变化或限制 |
| --- | --- | --- |
| [PACT README](pact-readme.md)、[PMU 平台表](pact-pmu-platform.c) | 定制 Linux 5.15、双线程、Skylake 校准 | `b6b5920`（2026-08-22）已改为 Linux 6.3、协程和批量迁移，仍依赖两个额外内核模块；SPR／EMR 的事件描述新增，但延迟系数沿用 SKX、待校准。README 的性能改善没有在本轮重测。 |
| [Camp 交错说明](camp-interleave-readme.md)、[完整补丁](camp-interleave.patch) | 按比例分配，拟合负载延迟／停顿 | `01009d5`（2026-05-31）补丁把普通 `MPOL_INTERLEAVE` 分配改成加权，使用 `/sys/devices/system/node/node*/access0/il_weight`；不能直接换成主线内核运行同样命令。 |
| [Linux 6.9 NUMA 文档](https://docs.kernel.org/6.9/admin-guide/mm/numa_memory_policy.html) | 应用指定内存分配策略 | 主线 `MPOL_WEIGHTED_INTERLEAVE` 使用 `/sys/kernel/mm/mempolicy/weighted_interleave/`。分配策略本身不自动迁移已经存在的所有页。 |
| [Camp 预测程序](camp-interleave-pred.py) | 论文中的 x 为本地请求比例 | 程序 x 为远端比例，推导时取互补；默认流程读取两端运行，另有显式 `--c2-csv` 外部估计模式。默认常数及计数器解析的单位换算未完整核对，不能拿来预测新模型。 |

五份元数据读取分别是两个仓库身份、两个提交身份与一份树查找；提交日期不是框架功能发布日。PACT 未知 CPU 路径返回错误，但本轮没有读调用者，未把 README 中的退出行为当作已审计事实。Camp 只核预测程序与交错补丁，没有核完所有 profiler、校准微基准和模型脚本。

## vLLM 的对象与搬移边界

复用固定提交 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e` 的 [UVA 页内存路径](../../2026-09-08/offload-execution/vllm-current-uva.py)第 72–145 行、[prefetch 缓冲](../../2026-09-08/offload-execution/vllm-current-prefetch.py)第 646–714 行与[多级 KV 文档](../../2026-09-08/cache-routing/vllm-current-kv-guide.md)第 1–40 行。权重存储可固定页，外部 KV 层先取到 CPU pinned buffer 再送 GPU；这些代码／文档不证明引擎采用了 PACT 或 Camp。

[Linux 6.9 页迁移](linux-v69-page-migration.rst)描述映射、引用、写回等条件；[pin_user_pages 文档](https://docs.kernel.org/6.9/core-api/pin_user_pages.html)的所选四节另说明 DMA 注册、长期 RDMA 与 MMU 通知／可重放缺页的区别。必须核对设备与缓冲生命周期，不能仅由虚拟地址不变推断迁移对 DMA 透明。

书中采用[同一份 Qwen3 权重的时间推算](../../../../case-studies/memory-criticality-and-tiering.md)，把容量、预取提前量和迁移成本接到已有案例。没有采用论文加速比、拟合常数或直接迁移 CPU 算法到 GPU 的结论。

## 保留但不采用的原文问题

PACT 页 6 的 Little 定律表述需将字节带宽换成请求速率；同页图注有 cache-line 换算，不能照搬省略单位的式子。页 14 的改善百分比与 slowdown 柱值、图 11 的 promotions 图注与 slowdown 坐标分别保留，未推导速度结论。

Camp 表 5 的 P8 标签与描述不一致，页 7 与页 10 的拟合系数写法也不能直接按名称互换；原件不改。论文报告的某些预测误差是 slowdown 的绝对差，不能称为相对运行时间误差。请求比例近似容量比例、固定并行度及二次负载曲线都是模型条件；没有把它们提升为通用系统定律。
