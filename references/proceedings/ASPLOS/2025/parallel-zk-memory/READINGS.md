# ASPLOS 2025：165–168、183–184 摘要筛选

阅读日期：2026-09-09。锁定时六篇均未读完整摘要，见 `selection-snapshot.json`。本包完成 165、167、168、183、184 的一手完整摘要，归档 5 份 PDF、89 页，实际查看 5 张第一页图像以核对摘要栏序、作者和版本。正文阅读为 **0 页**，全文文本仅机械提取。本包不新增大纲、实验或正文候选。

| 序号 | 一手来源与版本 | 摘要后的编辑判断 |
| --- | --- | --- |
| 165 MDPeek | [作者公开 PDF](https://www.comp.nus.edu.sg/~tcarlson/pdfs/liu2025mbbbiswmdusc.pdf)，17 页，首页含正式 DOI 10.1145/3676641.3716004 | SGX 的 memory disambiguation 侧信道与防护，属于安全背景，不进入 AI Infra 性能主线。 |
| 166 UniNTT | [正式 DOI](https://doi.org/10.1145/3669940.3707241)、Crossref 和作者出版列表可核身份，未取得原始摘要或公开稿 | 保留缺口，不能把搜索结果里的摘要当成读过正式原文，也不据标题选正文。 |
| 167 BatchZK | [IACR ePrint 2024/1862](https://eprint.iacr.org/2024/1862)，版本历史唯一 PDF 更新为 20241114:104207；公开稿 15 页，正式版 100–115 页共 16 页 | 可备查 GPU 流水线与吞吐/延迟口径；验证 ML 的密码证明不等于模型本身推理加速。不选正文。 |
| 168 UniZK | [作者公开 PDF](https://nas.iiis.tsinghua.edu.cn/~gaomy/pubs/unizk.asplos25.pdf)，17 页，首页含正式 DOI 10.1145/3669940.3707228 | 统一硬件映射多类 ZKP 内核的设计背景；不能因使用 systolic array 就等同神经网络 Tensor Core 负载。不选正文。 |
| 183 Virtuoso | [arXiv 2403.04635v2 PDF](https://arxiv.org/pdf/2403.04635v2)，2025-03-27，22 页；正式 DOI 10.1145/3676641.3716027 由 Crossref 与十位作者、完整标题对应 | 虚拟内存硬件/OS 仿真工具；这里的 VM 是 virtual memory，MimicOS 不是 Agent sandbox。复杂仿真工具仅备查，不替代本书先算瓶颈的主线。 |
| 184 Instruction-Aware TLB/cache replacement | [作者公开 PDF](https://gvavou5.github.io/Documents/Vavouliotis_ASPLOS25.pdf)，18 页，首页明确为 author’s version，含正式 DOI 10.1145/3669940.3707247 | CPU 指令地址翻译和 L2 替换合作，不能直接说明 GPU KV cache 容量、命中率或 LLM 服务吞吐。不选正文。 |

## 已读摘要的具体取舍

**165 MDPeek。** 摘要指出已有 SGX 控制流防护仍可能遗漏侧信道；作者逆向 MDU 的 enable/update 逻辑，利用它识别 secret-dependent branch 的泄漏，并在 Libjpeg、MbedTLS、WolfSSL 上演示。提出的 store-to-load coupling 与 serialization/load aligning 相比降低防护延迟。这里的 7× 是特定缓解办法的延迟比较，不是 AI 工作负载的性能收益。当前书需要执行环境隔离的工作机制，但不因此展开 SGX 攻击细节。

**167 BatchZK。** 摘要的出发点是把批量证明吞吐与单个证明延迟分开；让 GPU 线程连续执行任务，支持 sum-check、Merkle tree、linear-time encoder，并以 dynamic loading 和多 stream 重叠主机/设备传输。摘要报告相对既有 GPU 系统超过 259.5× 吞吐、一个 verifiable ML 应用 9.52 proofs/s；不能将 proofs/s 的倒数直接解释为单请求延迟，也不能把证明生成吞吐写成 LLM 推理吞吐。保存这一量纲提醒即可，暂不增加正文阅读。

**168 UniZK。** 摘要区分旧的椭圆曲线协议与新 hash-based 协议：后者算法复杂度较低，但计算内核更多样。因此用增加局部连接和 vector mode 的 systolic array 统一支持 NTT、hash、一般多项式计算，通过 mapping 提高利用率。摘要中 97× CPU、46× GPU 是相同协议实现的比较，840× 则是相对使用不同协议的既有加速器；两个比较条件不能合并成硬件本身带来的收益。此时尚未读实现或评估正文，不推测精度、实际芯片吞吐或 AI 算子适用性。

**183 Virtuoso。** 已读 PDF 摘要：通过 userspace MimicOS 仅模仿所需 OS 功能，在硬件模拟器中研究虚拟内存。集成五种模拟器并覆盖多种 VM 方案；在 Sniper 上分别验证 MMU 与 page-fault latency，再报告 IPC 建模准确度及仿真开销。这些量是模型的准确度/开销，不是真实业务 IPC 提升，也不是 VM 冷启动时间。这里只确定工具用途，不根据摘要判断精度定义、误差分布或训练系统适用性。

**184 iTP+xPTP。** iTP 提高 STLB 中 instruction translation 的命中，但会增加 data page walk；xPTP 通过 L2 替换策略减少后者代价，并在 xPTP/LRU 间自适应切换。摘要的 single-core 几何平均 18.9% 和 SMT 共置 11.4% 来自其 server workloads，比较基线是 STLB/L2 均用 LRU。仅作 CPU 内存层次的背景材料，不能挪作多级 KV cache 的实验结果。

## 版本、身份与失败

- 165、168 的首页标题、全体作者、DOI 和正式页数均一致；只声明作者网站上的 publication-layout 公开稿，不声称字节与 ACM 下载相同。
- BatchZK IACR 页面列六位作者、同题目，并注明 ASPLOS 2025 minor revision；Crossref 的六位作者、完整标题与 DOI 相同。IACR 版本历史只列 20241114:104207。预印本 15 页不等于正式版 16 页；未取得并比较正式全文。HTML 的完整摘要与 PDF 左栏内容逐词对应，保留 HTML 为原始摘要文本来源。
- Virtuoso v2 PDF 左栏摘要接到右栏顶部三行，采用两段明确边界拼接。arXiv HTML 摘要是不同且缺损的版本：出现 `VM this http URL`，MMU/CPU/page-fault 句缺词，并少了部分评估信息。保留 HTML 原文作为版本证据，不修补 HTML，不把它冒充 PDF 的同一摘要。v2 PDF 十位作者、完整标题对应正式 Crossref DOI，PDF 本身没有正式 DOI 标识；不宣称两版逐字相同。
- 184 PDF 首页明确写 author’s version。作者个人网页把两名共同一作顺序写成 Vavouliotis、Chasapis；PDF、正式 manifest 和另一作者 BSC 列表均为 Chasapis、Vavouliotis。本包保留正式顺序，同时记录页面差异；不增减作者。
- 166 的 Crossref HTTP 200 不含摘要；ACM landing、PDF 返回 HTTP 403，`web.run.open` 也 403；作者个人页只列作者/标题/会议，SDU 新闻 URL 返回 HTTP 200 的 error 页面（“你访问的主页不存在或没有上线发布”），不能算成功来源。上述原始失败正文与元数据均保留。没有重试已失败的同一 URL。
- 165、168、184 Crossref 请求 HTTP 429，响应确为 0 字节，照实保留。165、168、184 身份改由公开 PDF 首页核对；没有补造返回文本。

完整原始摘要及提取规则在 `reading-records.json`，失败请求见各 `*-jobs.json.results.json`；独立核验入口为 `python references/proceedings/ASPLOS/2025/parallel-zk-memory/verify.py`。
