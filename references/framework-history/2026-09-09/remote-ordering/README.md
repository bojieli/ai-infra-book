# 远端排序：论文、API 与实现条件

本批围绕当前 7.3.2／7.4.2 的两个问题选读：在途窗口足够以后，为何仍不能推进；保留正确顺序时，等待可以移到哪里。[采用案例](../../../../case-studies/remote-ordering-and-completion.md)接第 6 章内存池与第 9 章 KV 交接，没有新增编号。

[sources.json](sources.json)保存十一份成功响应；另有一次作者项目页 TLS 主机名不匹配、没有响应正文，存入[连接失败记录](connection-failures.json)。没有关闭 TLS 检查。[reading.json](reading.json)声明十三处阅读范围：完整作者 README、指定文档章节、固定源码中 quiet／fence 两个函数，以及仓库身份／路径查询。请求时的 `reading_status` 是下载阶段记录，当前实际阅读以范围文件为准。

作者仓库固定于 `e46840e779495d0d81ace5b199b3a14c7b7a5f5d`（2026-03-27），NVSHMEM 固定于 `b0d9d3dc08fc3ee0840fdb6f3a2c11932d85a2e2`（2026-08-27）。`latest` 文档另按取得时间归档，不视为某个正式版本。论文使用已有的 [ASPLOS 2026 原件](../../../proceedings/ASPLOS/2026/paper-116.pdf)，[阅读记录](../../../proceedings/ASPLOS/2026/remote-ordering-reading.json)登记物理页 2–13 和三张实际查看的页面。

论文的 PCIe／ISA／Root Complex 新机制、无写冲突时的真实网卡性能参照、NVSHMEM 的 API 保证、公共 IB 实现的条件分支分别保留。作者 README 不是模拟器实现审计；局部 IB 函数不是所有 GPU 通信或推理引擎的调用链。实时文档的概述与 quiet 详细说明在可见性表述上有差别，案例按具体操作与消费者同步解释，没有从概述推导全局同步保证。

没有运行作者模拟器、下载代码或硬件实验。配套检查只验证来源完整性、声明范围和教学算术／事件反例。
