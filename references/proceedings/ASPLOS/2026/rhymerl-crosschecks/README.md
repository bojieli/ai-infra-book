# RhymeRL 与历史草稿的交叉核对

2026-09-08。[来源清单](sources.json)保存十二份响应，十一份成功及一次出版商 PDF 403；另复用四处既有文本／目录范围。[阅读记录](../rhymerl-reading.json)逐项保存哈希、页码、选读行段、HTML 选择范围和实际查看的页面。

## 论文版本和范围

已读原件是 [paper-101.pdf](../paper-101.pdf)，2025-08-26 的 arXiv v1，共 15 页。作者出版条目确认 ASPLOS 2026 的另一题名、相同作者和 DOI，正式版为 17 页；未取得正式正文，不能称两版相同。实际阅读公开稿物理页 2–11 的相关正文及第 12 页参考文献前的比较／结论。第 4 页仅读取大型 trace 图后的正文，第 13 页只有抽取，不计阅读。

上级目录 `rhymerl-view-05.png` 至 `rhymerl-view-11.png` 七张页面图已实际查看，核对系统流程、历史匹配、窗口、分配和评估；未独立数字化曲线。离线匹配与在线草稿接受分别解释。verl v0.4.1、AReaL v0.3.0 和未披露 GPU 型号的历史评估不代表当前框架或 V4／K3 的结果。

## 固定框架与阅读边界

vLLM 提交 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`：完整读取 suffix proposer 与指南；rejection sampler 仅读第 92–185、394–566、774–851、873–953 行。v0.19.0 的 proposer 与当前文件作完整差异比较，release 仅核身份与 2026-04-03 发布日期，不声称是首次支持。2025-05 RFC 完整正文已读，提议不当作合入证明。

Arctic 提交 `aca5d9a8a62474035c15d114d40a01abc8c94b51`：完整读取 357 行 `cache.py` 和 166 行指南，C++ 仅读第 593–621、745–775、825–852 行。局部／全局缓存寿命、请求数 FIFO、经验分数与确定性路径分别核对。其他树更新、绑定、完整引擎链及全部采样／RNG 路径没有审计，也未证明 RhymeRL 使用相同实现。

复用已有 vLLM 2024 文章的 prompt lookup 段，读取 SGLang 固定指南第 725–789 行 NGRAM 说明；SGLang revision 为 `c99d906effa8bd05573995127f0d4a0984c5a96a`。后端、DP attention、重叠和混合 prefill 限制随实验保留。旧文章和两份目录元数据不重复下载或增加论文阅读数量。

## 推算与采用

[案例](../../../../../case-studies/history-drafts-and-rollout.md)用于当前 8.3.1／10.5.3、既有实验 8-5／10-8 与图 8-4／10-7。[独立计算](../../../../../research/2026-infra-survey/calculate_history_speculation.py)用有理数完成 40 组分布检查，核对每轮产出、查询和启动成本，并另算主机索引容量；[结果](../../../../../research/2026-infra-survey/history-speculation-arithmetic.json)全部注明教学假设。

[离线校验](../../../../../research/2026-infra-survey/verify_history_speculation.py)检查所声明范围和算术。没有导入或执行下载源码，没有运行模型、GPU 或 RL 训练。这个阶段完成一项有范围声明的正文选读，不表示整份正式论文、完整框架历史或长期调研已经完成。
