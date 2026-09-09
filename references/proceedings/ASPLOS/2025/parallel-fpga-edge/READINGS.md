# ASPLOS 2025：节目 19、25、29、30、31、32

本批锁定最早六个没有既有明确失败记录的未读条目。17 的旧 URL 已有 HTTP 200 重定向非论文记录、24 已有 HTTP 404，因此跳过。实际阅读 19、25、29、30、31 的原始完整摘要；29、30、31 的三份 PDF 共 46 页只是机械归档，三张首页图均已查看，**正文阅读 0 页**。32 保留 ASPLOS 原始摘要缺口。没有运行下载代码、增加大纲或修改共享覆盖。

## 19：Pirate

[Penn State 机构原始成果页](https://pure.psu.edu/en/publications/pirate-no-compromise-low-bandwidth-vr-streaming-for-edge-devices/)中 `.rendering_researchoutput_abstractportal .textblock > p` 为完整摘要。题名、DOI 10.1145/3676641.3716268、页码 882–896 一致；十名作者按顺序对应，机构元数据的 Mahmut Kandemir、Chitaranjan Das 分别对应正式记录的 Mahmut T. Kandemir、Chita R. Das，明确记录该来源写法差别。

摘要围绕 VR 双眼视图的相似性展开，以单眼视图及 disparity、optical flow 反复生成目标眼视图、交替传输左右眼；摘要报告低至 0.1 bpp、90 FPS 与 20%–40% 带宽节约。这里的工作负载是立体 VR 视频，不是 computer-use 截图或模型 reasoning。可作为压缩与端侧重建计算之间取舍的背景，但不移植其收益至第 12 章现有 AI 案例，也不新增正文候选。

[作者 Kiwan Maeng 的出版页](https://kiwanmaeng.com/)列出了该文，但该条目的 PDF 链接为 `https://todo.pdf` 占位符，没有请求这个地址；ACM PDF HTTP 403。此项仅原始 HTML 摘要，没有代表 PDF。

## 25：RANGE-BLOCKS / RBlox

[SFU 教师成果页](https://www.sfu.ca/research/expertise-engine/profile/709feea8-933d-44c0-b8f5-455897edbb45)的静态 HTML 是应用壳，不含原始摘要。仅静态阅读它引用的 JS 中公开 API 路由，没有执行 JS。随后从[该页面调用的机构 API](https://www.sfu.ca/research/expertise-engine/api/public/v2/publications/?page=1&ordering=-date&sfu_authors__random_id=709feea8-933d-44c0-b8f5-455897edbb45)取得完整原始 `abstract` 字段。选择 `results` 中 DOI 精确为 10.1145/3669940.3707225 的唯一对象，不使用搜索页的截断预览。机构成果引擎此栏为 Scopus Publications；此处依据作者所属机构托管的完整成果记录，未声称作者个人重新上传了一份 PDF。

完整摘要说明 DSA 缺少支持动态数据结构的同步设施，地址原子操作或主机批量更新又会带来开销；RBlox 用 key range 描述互斥边界，并利用数据结构布局中的并行性。摘要写的是小表 `2kb` 对大缓存 `256kb`，以及 128-tile DSA 上 15× 性能、4× DRAM 带宽减少、70% 片上流量节省、片上能量需求为对照的 6.6%。本批保持原文单位大小写，不自行解释为 kB，也不把“require 6.6%”改成“减少 6.6%”。这些是动态结构同步实验，不是 paged KV cache 或稀疏 attention 的量化证据，仅背景备查。

正式题名、DOI、三位作者的缩写列表 `Kumar A.M.A., Prasanna A., Shriraman A.` 与 Crossref 的三位全名相对应；机构 API 同时标出 Arrvindh Shriraman 和固定教师 UUID。首次使用错误过滤参数 `sfu_authors` 得到 HTTP 200 的全校列表，没有目标 DOI，完整保存但排除；按源 JS 使用 `sfu_authors__random_id` 后才定位到目标。未读 API 返回的其他论文。ACM 落地页和 PDF 均 HTTP 403，没有代表 PDF。

## 29：Salus

[作者 camera-ready PDF](https://yu-zou.github.io/assets/salus-camera-ready-final.pdf)共 15 页，首页题名、11 位作者、正式 DOI 10.1145/3622781.3674169 一致。此文属于 ASPLOS 2024 Volume 4，编入 ASPLOS 2025 正式节目；没有将原出版身份改为 2025。公开作者稿与正式页码 252–266 页数一致，但没有出版商字节等同声明。

摘要讨论商用 CPU–FPGA 云平台上的可信执行环境：使用主机 CPU enclave 保护并证明 FPGA 的 bitstream，结合现有 bitstream 工具和安全增强 FPGA IP。摘要没有提供性能数字，因此没有引用作者 CV 或搜索结果中的其他速度声明。它是异构 TEE 的背景，不能将保护机密数据的威胁模型直接等同于 Agent 工具 sandbox，也不选正文。

摘要跨双栏。默认首页文本将右栏末句 `IP, Salus presents ... minor efforts required.` 提到左栏全文前；实际看图确认后，先取左栏 `CPU-FPGA heterogeneous architectures` 到 `ACM Reference Format:` 前的主体，再追加右栏首句的两行。没有混入作者通讯脚注、版权或右栏引言。

## 30：Harmonia

[作者成果页](https://liluyang.com.cn/publication/harmonia/)直接链接[公开 PDF](https://liluyang.com.cn/uploads/2025/harmonia-asplos25.pdf)。17 页，首页 DOI 10.1145/3676641.3716259、12 位作者、题名核对一致，正式页码 498–514。作者页面标注 August 2024；PDF 明确 ASPLOS 2025，保留该页面时间与正式出版时间差别，不将网页标注当作正式会议时间。

摘要说明异构 FPGA 让 shell、role 和主机软件的迁移同时变复杂，Harmonia 以平台相关适配和平台无关 shell 分工，用模块化组成与命令接口减少重复开发。摘要给出 69%–93% shell 开发量减少、低于 0.63% 开销、3.5%–14.9% 资源消耗减少、15–23× 软件配置简化；各自口径不同，不能当成统一的模型执行速度比。可作为异构加速器软件适配背景，不据摘要改写本书芯片对比，也不新增正文候选。

采用 PDF 摘要作为标准文本，分两段提取：`Abstract` 后到 `Permission to make digital` 前；再从 `hardware differences and a platform-independent layer` 到 `CCS Concepts:`。版权段恰好插在两栏间，明确排除。作者 HTML 完整摘要也已阅读，其结尾 `15-23x` 与 PDF 的 `15-23×` 及少量版面空白不同，保留两种原始来源，未擅自合并字节。

## 31：PhasePrint

[Virginia Tech 机构仓库 PDF](https://vtechworks.lib.vt.edu/bitstreams/535636be-8259-4b16-ad9d-06f2e799cadd/download)共 14 页，首页题名、两位作者和 DOI 10.1145/3676641.3716012 一致，正式页码 831–844。已查看首页图。默认提取在 `Abstract` 后插入右栏 `CCS Concepts:`，因此用完整摘要第一句与末句为锚，排除整个右栏和脚注。

完整摘要是 FPGA 器件身份识别研究：在功能正确电路中诱发时序故障，构成制造差异指纹，并报告在 AWS 四个地区的 300 片 FPGA 上的分类结果。其大于 99% 准确率、13× 速度与 92% 成本减少属于这项器件识别任务，与 LLM serving 或资源调度的目标不同；仅存档排除，不开展攻击复现，也不设正文候选。

## 32：Hassert 的原始摘要缺口

正式 DOI 10.1145/3622781.3698899，ASPLOS 2024 Volume 4、页码 142–154，编入 2025 节目。[作者发表清单](https://shilicon.github.io/publications/)有精确题名与八位作者，但该项没有论文链接或原始摘要；已归档的 Crossref 元数据也无摘要，ACM 落地页/PDF HTTP 403。

[RISC-V Summit Europe 的另一场会议记录](https://riscv-europe.org/summit/2025/posters)有 Hassert 扩展摘要，但题名多出 **Agile**，只有 Ziqing Zhang、Weijie Weng、Yungang Bao、Kan Shi 四位作者，不能替代 ASPLOS 八作者原始论文。归档 HTML 并记录区别，未下载其 poster/扩展 PDF、未计代表 PDF或完整 ASPLOS 摘要。搜索结果和第三方机器翻译也不作摘要依据。

所有五篇判断只依据完整摘要，不把摘要内的数字表述成已经核对过正文评估。本批静态资料的 URL、HTTP 状态、时间、字节数和哈希见 `reading-records.json`；本地复用的一手 Crossref 原始响应另记 provenance，不计新增网络请求。
