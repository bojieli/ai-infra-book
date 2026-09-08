# PipeLLM 的提前准备与 vLLM 的状态恢复

2026-09-09，围绕第五章的“增加一次复制，为什么仍可能减少等待”阅读。[九份原始响应](sources.json)、[十六个实际读取范围](reading.json)与[论文页级记录](../../../proceedings/ASPLOS/2025/pipellm-reading.json)分别留档；五份已有输入复用原件，没有重新下载。只做静态阅读和独立算式，没有执行下载的代码、二进制库、模型或 GPU 实验。

## 论文解决的路径

作者托管的正式格式 PDF 共十五页，物理页 1–13 已读，六页图表已查看；14–15 页参考文献未读。早期 arXiv v1 的十四页原件仍保留，新增版本不重复计算论文或摘要。正式 DOI 为 [10.1145/3669940.3707224](https://doi.org/10.1145/3669940.3707224)。

论文将主机—GPU 机密传输中的加密提前进行，使用前再确认数据与 nonce 顺序。准备结果先留在受保护的私有内存，之后复制到共享传输缓冲；这次额外复制与提前准备的收益一起计价。允许重排的复制仍受批次依赖限制，不能任意越过同步。提前解密也要保证 CPU 首次读取时内容已就绪。正文采用的页面保护与 nonce 处理是设计条件，不是本轮完成的安全验证。

测量平台为单 H100-SXM、双路 Xeon 8462Y+ 主机上的 16 vCPU／250 GB VM。正文明确 CPU 不支持 TDX，实验只保护 CPU—GPU I/O；不能把它写成完整机密虚拟机的实测。FlexGen／PEFT 的权重卸载与 vLLM 的 KV 换出分开：前者包含 OPT-66B、4 bit OPT-175B 等旧配置；后者用 OPT-13B／30B、并行采样 2／4／6 及 Alpaca／ShareGPT 请求。论文没有给出可锁定的 vLLM 提交或版本，本目录的历史版本仅作机制对照。

图 2 的 API 延迟止于调用返回，不是 DMA 完成；PCIe 的双向标称不能代入单向传输式。正文“顺序预测成功率为零”的消融仍通过重排／NOP 使用已准备密文，不等于有用准备比例为零。摘要、引言与后文的 52.8% 口径仍有歧义，未采用为性能结论。图 6 最后一步图内为 data3、图注写 data1；原件保留，不照抄为可执行算法。

## 公开工件的实现边界

固定作者提交为 `d7d01dde2acb72554ac197439739593bc37122e2`，提交时间 2024-12-22。完整读过 [README](artifact-README.md)、[Makefile](artifact-Makefile)、[头文件](artifact-pipellm.h)、[CUDA 调用拦截](artifact-pipellm.cpp)、[工作线程](artifact-worker.cpp)与 [OpenSSL 拦截](artifact-openssl.cpp)；目录树仅核对文件和 blob 身份，其余辅助文件与二进制库未审计。

README 要求按机器修改参数／路径、采集 IV 顺序、替换 CUDA 静态库后重建 PyTorch，并更换 OpenSSL 集成。这是研究工件的运行条件，不能写成安装当前 vLLM 即可启用。所读 `EVP_EncryptUpdate` 路径确实将预备密文复制到目标缓冲，支持“额外主机复制”的分析。

工件用历史地址／大小识别重复传输，`pipellm.cpp` 第 245 行的已学习序列失配进入 `assert(0)`；Makefile 没有关闭断言。工作线程还选择 device 0，传输大小阈值及工作线程配置固定在特定路径。这些范围不能证明论文所述全部失配都已实现透明回退，也不能推广为任意多卡后端。已读核心文件未找到论文所述页面写保护的对应调用；辅助文件及链接库未全面检查，因此只记录未完成的一一对应，不据此宣布整套实现缺少保护或存在确定漏洞。

## 框架改变了什么

| 代表快照 | 实际读取 | 对本书预算的影响 |
| --- | --- | --- |
| vLLM v0.4.2，`c7f2cf2…` | [历史 scheduler](../../2026-09-08/chunk-scheduling/vllm-v042-scheduler.py)，1036–1115 行 | 未指定模式时，单序列采用重计算，多序列采用换出。不能写成旧 vLLM 一律交换 KV，也不能将该版本冒充论文测量版本。 |
| vLLM v0.8.0 V1，`966f933…` | [V1 scheduler](../../2026-09-08/chunk-scheduling/vllm-v080-scheduler.py)，135–200 行 | KV 分配失败可释放被抢占请求，重置已计算 token 后放回等待队列；恢复工作不能继续只算 PCIe 换入字节。 |
| 当前固定 V1，`537af2c…` | [scheduler](../lora-admission/vllm-current-scheduler.py.txt) 的抢占、缓存查询、分配与释放范围；[同提交指南](vllm-current-v1-guide.md) | 旧式 swapping 已移出核心；重置后仍可能取得本地或 connector 的 KV 命中，异步执行还影响块何时能真正回收。不等于所有抢占都从零算完，也不等于 CPU 缓存被取消。 |
| vLLM 2026-01-08 作者文章 | [原文](https://vllm.ai/blog/2026-01-08-kv-offloading-connector)与[已归档正文](../../2026-09-08/cache-routing/vllm-kv-offload-2026.txt) | 文章回顾 v0.9 异步接口、v0.11 offload、v0.12 布局改变，评估包含另列补丁。CPU KV tier 能服务共享前缀，也可帮助恢复被抢占请求；不能把文章测试直接归给某个未经补丁的正式版。 |

这里对照的是机制变化，没有证据证明当前引擎直接集成 PipeLLM。权重预取、前缀缓存与抢占恢复的预测对象不同，还要核对模型的 KV 表示、块布局、CPU 资源和硬件保护路径。指南其他支持表不作为跨后端的完整能力结论。

## 采用与保留

采用[现有 64 MiB 张量案例](../../../../case-studies/host-transfer-and-buffer-lifetime.md#提前准备的工作是否有用)的第二组教学时间，核算总工作、三类缓冲寿命及有用准备比例；第五章 5.2.3／实验 5-2／图 5-2 只补选做变体。第八章辨认抢占，第九章沿已有 KV 层次计算取回与重算。完整加密实现、论文总加速比和旧模型配置留作研究依据，不扩展新主小节。

验证入口为 `python research/2026-infra-survey/verify_pipellm_preparation.py`，结果见[检查记录](../../../../research/2026-infra-survey/pipellm-preparation-audit.json)。页级哈希另由会议校验器核对；这不代替真实系统测量或全书一致性验收。
