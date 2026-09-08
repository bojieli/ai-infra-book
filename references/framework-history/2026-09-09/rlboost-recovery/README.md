# RLBoost：权重就绪、恢复进度与实现范围

本批围绕当前 11.3.2 和实验 11-4，接第 7 章共享出口、第 8 章前缀重建和第 10 章同步训练。采用内容见[推算案例](../../../../case-studies/preemptible-rollout-and-weight-readiness.md)，主文只补一段计算，不增加编号。

[sources.json](sources.json)保存二十一份成功响应；[reading.json](reading.json)登记十八项实际阅读范围。安装说明、启动脚本、配置、官方模型配置、补丁启动文件和补丁管理文件完整阅读；较大源码只读取列明的行段。`polyrl-balance.rs`、`polyrl-instances.rs`、`polyrl-models.rs` 下载作为后续定位材料，尚未阅读正文，不计入本轮实现结论。此前 PolyRL README／USAGE／ROADMAP 及提交身份复用[上一批原件](../rollout-resources/README.md)，不重复计数。

作者代码固定于 `44ce6fdcd30ecf2d55037513ddddd51076325a2b`，verl 子模块 gitlink 为 `0eb50ec4a33cda97e05ed8caab9c7f17a30c05a9`；后者只核对引用身份，没有在本轮阅读其实现。安装说明指定 SGLang 0.5.5，作者通过 `rlboost.sglang` 补丁扩展接口。配置沿用 Mooncake 命名，但固定发送／接收路径构造 `TCPTransferEngine`；不能据名称推定 RDMA、GPU 直传或当前标准框架支持。

Qwen3-14B 官方配置固定于 `40c069824f4251a91eefaf281ebe4c544efd3e18`（模型 API 记录最近修改为 2025-07-26）。其 40 层／40 个 Q 头与论文 Table 4 的 48／48 不同。实际查看了论文原表图像；采用官方配置进行本书容量计算，保留论文原件，不据差异反推论文实际运行模型。

论文复用已有 [RLBoost 原件](../../../outline-checks/2026-09-07/platform-routing/rlboost-nsdi26.pdf)，本轮读物理页 9–13、17–18，实际查看页面 9、12、17、18。七页与整卷相应页逐一比较规范化文本，见[论文记录](../../../proceedings/NSDI/2026/rlboost-reading.json)。此前 §3–6 方法阅读另记在 platform-routing 案例中，本批不是首次发现或全文阅读。真实轨迹经过抽样并在按需实例上回放；价格含跨供应商、地区和大小实例折算，不表示今日可购买规格。

本批没有执行归档代码、加载模型或运行云端／GPU 实验。校验范围是来源、行段、物理页对应和教学算术；错误分类、恢复分支和版本准入的静态检查不证明全部故障下的运行正确性。
