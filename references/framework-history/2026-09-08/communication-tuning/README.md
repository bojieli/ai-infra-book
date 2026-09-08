# 通信反馈、配置接口与执行资源

获取与阅读日期：2026-09-08。[12 份响应](sources.json)包含 3 份失败／空响应、2 份身份元数据、1 份正式 release 和 6 份文章／文档／头文件／README。没有把错误页当成正文，没有运行下载的代码。

| 原件 | 阅读范围与采用 |
| --- | --- |
| [2025-07-22 调优文章](nccl-2025-tuning-blog-retry.html) | 正文、代码及图注文；成本模型、动态资源分配、局部覆盖和并发争用。另存[正文文本](nccl-2025-tuning-blog-retry.txt)，排除网页的 AI 摘要，未独立量化曲线。 |
| [2025-11-10 的 2.28 公告](nccl-2025-device-blog.html) | 正文、代码与图注文；设备 API、CE、窗口、profiling 和插件；图中峰值不作本书测量。另存[文本](nccl-2025-device-blog.txt)。 |
| [AutoCCL README](autoccl-fixed-readme.md) | 全文件；需要修改后的 NCCL 库与 tuner，未审构建或实验脚本。固定 `63acb15c124400f94f1201127c1d06b35f90e757`，由 [HEAD 元数据](autoccl-head-commit.json)定位；其提交日期不是论文发表日。 |
| [2.31.2 注册文档](nccl-2312-bufferreg.rst) | 全文件；采用窗口、NVLink／网络零 CTA 的操作、驱动与策略条件；不把注册后所有操作都视作 CE。 |
| [tuner 定义](nccl-2312-tuner.h)与 [v6 接口](nccl-2312-tuner-v6.h) | 两个完整头文件；操作／协议成本、通道、chunk 回调、缓冲约束与回退声明；没有审全部 dispatch 实现。 |
| [2.31.2-1 release](nccl-2312-release.json) | 2026-08-11 发布元数据与全部说明／已知问题；本轮采用逐操作配置的版本边界，其他功能不是因此全部进入大纲。 |
| [NCCL tag](nccl-2312-tag.json) | 固定 `v2.31.2-1` 指向 `7b83616df3ae082a1f32bb74c27458bfe8153a13`；上述源码均从该提交获取。 |

保留三项取回失败：初次调优文章 HTTP 200 但为零字节，加入查询参数后取得正文；AutoCCL `main` 查询返回 422，改查 `HEAD`；猜测的 CE 独立文档路径返回 404，随后沿公告找到 buffer registration 文档并获取固定版本源文件。原响应各有哈希，不能算作三份已读内容。

对应 [AutoCCL 正式论文](../../../proceedings/NSDI/2025/selected/nsdi25-xu-guanbin.pdf)和[采用笔记](../../../../case-studies/communication-tuning.md)，只深化第 6 章已有两小节、实验 6-5 与第 11 章交叉引用。底层 NCCL、研究 fork 和 vLLM／SGLang 实际选择的路径分别核对；没有新增框架介绍章。
