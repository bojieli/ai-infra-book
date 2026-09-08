# 系统抽象边界上移：原始材料

获取／导出日期：2026-09-08。配套[独立调研报告](../../../../research/system-abstraction-boundary/report.md)，用于第一章的开篇主线与第 12 章的运行环境衔接。

本组共 8 条来源记录：3 份仓库历史原件和 5 份官方网页。原件保持获取时内容，`text/` 是派生的可搜索文本；[sources.json](sources.json)记录来源、提交号、时间、文件大小、SHA-256 与阅读范围。网页的外链资产没有递归镜像，本轮采用其文字说明。

## 仓库历史原件

| 版本 | 原件 | 用途 |
|---|---|---|
| 草案 11，2026-08-22，`12fc723` | [完整 skeleton](skeleton-draft11-12fc723.html) | 第 482 行包含“从 ISA/OS 上移至 token 层”与可编程性、多租户迁移 |
| 草案 14，2026-08-31，`d9199ca` | [完整 skeleton](skeleton-draft14-d9199ca.html) | 第 483 行仍保留同一论证 |
| 草案 16，2026-09-05，`e524afe` | [完整 skeleton](skeleton-draft16-e524afe.html) | 对照章节蓝图重写后该论证的缺失 |

历史文件保留旧数字和旧章节安排以便追溯，不将这些内容全部作为本轮的技术结论。

## 外部一手资料

| 来源 | 在线与原件 | 本轮核对范围 |
|---|---|---|
| OSDI 官方网站 | [在线](https://www.usenix.org/conference/osdi26) · [原件](osdi26.html) | Operating Systems Design and Implementation 名称及系统软件研究范围 |
| SOSP 官方网站 | [在线](https://sigops.org/s/conferences/sosp/2026/) · [原件](sosp26.html) | Symposium on Operating Systems Principles 名称及范围 |
| Stanford CRFM 基础模型报告介绍 | [在线](https://crfm.stanford.edu/report.html) · [原件](foundation-models.html) | 摘要、引言中的广泛下游任务、提示适配和模型基础趋同；未将链接长报告列为全文已读 |
| NVIDIA MIG 用户指南引言 | [在线](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html) · [原件](mig-introduction.html) | GPU 资源分区、多用户／多租户与隔离用途；不据此推断全部设备支持相同配置 |
| Firecracker 官方网站 | [在线](https://firecracker-microvm.github.io/) · [原件](firecracker.html) | 多租户函数／容器服务、microVM 与 KVM；不采用未经同条件核对的性能宣传数字 |
