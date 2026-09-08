# E2B：模板读取与虚拟机内存安装

2026-09-09 选读。固定 `e2b-dev/infra` 提交 **`a586d1e859ecfcaf68df393e9e81a890a5c9d4a1`**，提交时间 2026-09-08 17:05:16 UTC；这是源码取样，不是特性首发日期或云服务部署证明。六份原始响应、十个声明范围见 [sources.json](sources.json) 与 [reading.json](reading.json)。

| 原件与读取范围 | 本轮采用的判断 |
| --- | --- |
| [架构说明](ARCHITECTURE.md)，11–28、156–209、321–350、416–430、502–534 行 | 普通模板恢复预启动 Firecracker；内存按需读取、rootfs 写时复制；创建响应等待 envd 初始化；模板优化记录访问页以指导预取。暂停／后台上传仅按所读文档说明，不声称完整持久化审计。 |
| [Uffd.handle](uffd.go.txt)，146–257 行 | 从 Firecracker 接收描述符和映射，将模板 memfile 作为源传给 userfaultfd 处理器，再进入服务循环。 |
| [faultPage](userfaultfd.go.txt)，932–1091 行 | 有数据源时先 `ReadAt`，再 `Fd.copy` 安装；空页另分支。读来源失败、重复安装和需要延迟重试分别处理，不能按每次故障都成功计数。 |
| [Fd.copy](fd.go.txt)，152–193 行 | 调用 `UFFDIO_COPY`；检查 errno 和实际复制长度，部分复制也可能需要后续处理。 |
| [提交](e2b-commit.json)／[tree](e2b-tree.json) | 只核提交身份和四个文件的 Git blob SHA-1；不把整棵目录下载标成全代码阅读。 |

CXLfork 的 CPU 进程恢复直接映射共享只读页；上述 E2B 缺页路径安装独立的虚拟机内存。两者都复用初始化状态，但模板缓存命中与运行页共享不是同一件事。论文的 Linux／CXL 原型与 E2B 的部署边界、依赖及读写方式分别说明，不建立未验证的实现继承关系。

源码中存在预取、写保护和 CoW 导出接口；本轮只采用上述路径，不推断所有可选开关都已在云服务开启，不对 Firecracker、内核零页或文件页去重作完整结论。没有运行下载的 Go 文件、microVM、云 API 或 GPU 程序。

进入当前 11.2 和既有实验 11-2：[快照恢复与首次访问预算](../../../../case-studies/snapshot-residency-and-first-use.md)。原件字节保留，页级论文记录另见 [CXLfork](../../../proceedings/ASPLOS/2025/cxlfork-reading.json)。
