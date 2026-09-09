# MICRO 2024 第六批摘要筛读

首次检查时正式 coverage 为 63 篇；锁定后复制输入时，根任务已集成第五批，快照变为 67 篇。按保存的 **67 篇正式记录**与前五批封存包重新去重，排除已明确受阻的 13、19、51、97，最早六篇仍是锁定的 **26、28、32、35、36、37**。选取过程由 `verify.py` 重算，不假设共享文件在审读后保持不变。

本批完成 **4 篇可用原始一手字节复核的完整摘要**。3 份匹配作者 PDF 共 **42 个物理页**，实际看了三张首页，**正文阅读 0 页，新增正文候选 0 篇**。另有两条一手归档路径未完成：26 UFC 的完整形态摘要已在搜索工具的 IEEE 索引文本中观察到，但原始出版网页取不到；32 尚无完整一手摘要。二者不会混入正式完成数。

| 序号、DOI 尾号 | 身份与来源 | 当前处理 |
| --- | --- | --- |
| 26 UFC，.00034 | 第一作者发表目录与独立论文页匹配十名作者、MICRO 2024；直接 IEEE 请求均为空响应 | 原始一手摘要归档未完成。搜索工具所见摘要单独保存为观察记录，不能冒充 HTTP 原文。 |
| 28 GPU 大整数 IMCompiler，.00036 | PolyU Scholars Hub 机构完整摘要，六名作者、会议、380–392 页、DOI 匹配 | 完整摘要已读；备查。没有增加编译器章节内容。 |
| 32 HLS FPGA 动态内存管理，.00040 | 第一作者主页脚本中的书目对象与共同作者 UNSW 目录匹配身份；IEEE 202，DBLP 发现请求得到验证页 | 完整一手摘要未读，无公开 PDF。保留受阻路径。 |
| 35 EntropyIndex，.00041 | 作者 Texas A&M 目录 PDF 13 页；NSF 记录核对出版身份和作者顺序 | 完整摘要已读；备查。 |
| 36 Last-Level Branch Predictor，.00042 | 第一作者 MICRO 2024 PDF 16 页，首页 DOI 和印刷页 464 | 完整摘要已读；排除本轮正文补读。 |
| 37 TEA 分支预计算，.00043 | UT Austin HPS 实验室 PDF 13 页，首页 DOI 和印刷页 480 | 完整摘要已读；排除本轮正文补读。 |

## 有限的教学价值

IMCompiler 用领域 IR 分开整数乘法的高层参数与设备优化，backend 为设备微调代表 kernel 后生成代码。这可以作为第 5 章“抽象保留什么信息、设备特化解决什么”的备查，但工作负载是密码学大整数乘法。本书已有模型算子和编译实例，无需为了新论文增加密码算法细节。摘要中的 4.47× 和 1.42× 是作者比较口径，本轮未读基线、整数规模与设备评估，不拿它支持 AI kernel 的性能结论。

EntropyIndex 关注 cache index 函数对冲突失效的影响，并用地址位变化来动态选择索引位，兼顾分布与计算时延。它可以留作第 4 章缓存的背景；摘要覆盖 SPEC、PARSEC、GAP、CVP，且分别比较有无 prefetch，不能只摘出某个最高 IPC 提升，再将其外推为 GPU 或 KV cache 的收益。本轮不扩展缓存设计正文。

LLBP 通过后备预测状态与小型核内缓冲分开容量和访问时延约束；TEA 则将分支预计算用于提前触发错误预测清空，放松必须在 Fetch 时覆盖预测器结果的时限。两者有明确的 CPU 设计问题，但与 AI Infra 的贯穿模型推算距离较远。特别是它们的 branch speculation 不是 LLM 推测解码，本轮停止于摘要。

## 身份和证据边界

**35 的作者顺序存在输入差异。** program 记录是 Weston、Janfaza、Johnson、Mahmud、Muzahid；publisher 元数据、作者 PDF 首页与 [NSF 记录](https://par.nsf.gov/biblio/10577371-customizing-cache-indexing-through-entropy-estimation) 则是 Weston、Johnson、Janfaza、Mahmud、Muzahid。两个顺序都保存在本包，未改共享 manifest。共同作者目录的 PDF 元数据为 2024-09-16；NSF 标记其所挂材料为 accepted manuscript，但本批未下载 NSF PDF，不能据此宣布两个文件字节或稿件版本相同。

**36 没有混用后续论文。** [第一作者主页](https://dhschall.github.io/) 同时列出 MICRO 2024 的 LLBP 与 HPCA 2026 的 *The Last-Level Branch Predictor Revisited*。本次下载 `LLBP_MICRO24.pdf`，没有下载后者、代码、artifact 或 slides。作者页附近条目用于版本排除，不算新增正文阅读。

**37 保留题名与名字写法差异。** program 的 `Branch Pre-computation` 与出版元数据、作者稿的 `Branch Precomputation` 指向同一 DOI；`Chester(Lingzhe)`、`Lingzhe(Chester)` 等作者写法没有被用于制造另一篇文献。PDF 的 2024-10-29 生成日期不替代会议日期。

**26 UFC 的索引文本与原始网页分开。** 搜索工具对 [IEEE 页面](https://ieeexplore.ieee.org/document/10764649/) 返回连续的完整形态摘要；已实际观察并保存为 `ufc-search-tool-output.txt`。但两个直接 GET 都是 HTTP 202、0 字节，随后 web open 返回需要机器人验证的页面。`tool-observations.json` 记录了精确观察范围和不计入正式一手归档的原因；工具返回文本不是网页原始字节，也没有可核验的 HTTP 状态，未添加到 `sources.json` 冒充下载成功。没有根据该摘要提出正文或数值结论。

**32 的动态网页只读了书目数据。** 作者首页 HTML 是应用入口；静态 JS 文件中包含该论文的题名、十名作者、MICRO 2024 与 DOI。只将这个对象作为文本读取，字符范围见 `reading.json`，没有执行 JS、React、实验工件或框架代码。共同作者 UNSW 目录同样没有摘要或 PDF 链接。DBLP 的发现请求虽然状态为 200，响应实际是机器人验证 HTML，已改用符合内容的归档文件名并保留原请求名，不当作 XML 或成功书目证据。

## 文件和核验

- `abstracts.json`、`abstract-028/035/036/037.txt`：四篇完整一手摘要、身份版本、精确提取范围、筛选理由；26/32 单列未完成。
- `sources.json`：16 个新 HTTP 原始响应及 URL、状态、抓取时间、字节长度和 SHA256。12 个 200 中包含一个验证页；另有 3 个 202 空响应、1 个 504。
- `tool-observations.json`：UFC 索引摘要观察与 web open 验证页，明确与原始 HTTP 响应区分。
- `reused-sources.json`：正式 manifest、coverage 和前五批记录共七个输入快照的复制来源、时间、长度和 SHA。
- `reading.json`、`extraction-log.json`：实际看图、摘要与辅助资料字符/行范围、提取和渲染记录。
- `verify.py`、`verification.json`：独立重算最早未读条目，核对原始字节、身份差异、PDF 页数、摘要提取、工具观察与失败响应的计数边界。

运行 `python references/proceedings/MICRO/2024/parallel-abstracts-sixth/verify.py` 可离线复核。它只调用本机 Poppler 读取归档 PDF，不访问网络或执行下载代码。本批未修改共享索引、大纲、skeleton 或 Git。
