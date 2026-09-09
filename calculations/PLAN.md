# 全书量化计算计划与验收清单

本项目把大纲中散落的推导、算例和实验中的计算部分收拢为可复现 Python 项目。范围包括十三章正文、逐章扩写资料及其案例笔记，不能以 39 项核心练习代替全部计算。正式 GPU 测量、质量评测和作者尚未提供的记录按原大纲保持独立；需要这些输入的计算先提供明确标记的情景扫描及数据导入，不能填造实测。

## 当前状态速览（2026-09-09，非全书完成率）

当前93个顶层工作包中25个已勾选、68个未勾选（新增C82 Qwen3.6-35B-A3B）。未勾选包含“部分实现”和“尚未逐原文验收”，不能解释为68项完全没做；脚本数、测试数也不能换算为完成百分比。

| 工作                  | 当前状态                  | 下一步                  |
| ------------------- | --------------------- | -------------------- |
| H01–H07 硬件基础表       | 已按有限官方来源范围验收          | 有新增型号/来源时复核受影响记录     |
| F02/F03 官方输入与公共计算基础 | 已验收所列契约               | 后续模型扩展继续独立验证         |
| C10/C11/C12 复杂模型    | 部分完成，已有完整基础逻辑账及多个执行子账 | 按各条明确缺口继续，不把子账当整个工作包 |
| C13 容量、深宽与专家颗粒度     | 14条已复核：11完成、3部分完成    | 继续S01/S06/S11质量与经济点证据   |
| C14 请求、MTP、缓存与模型选择  | 部分完成，近期成果已写回本条        | 缓存与图2-8已验收；补实际执行与质量选择证据  |
| C19 / C21–C24 近期章节工作 | C19已验收；C21–C24部分完成 | 已交子账保留证据，逐项处理原范围缺口 |
| C77–C81 多模态与生成模型 | 多个公共阶段账已接入，均未整体验收 | 补完整请求路径与逐条覆盖，见原条目 |
| F01/F04 全书覆盖与最终交付   | 未完成                   | 对全部原文要求与现有成果逐项核对     |

维护约定：新成果同时更新对应工作包的“已完成/仍缺”，PROGRESS只保留过程和验证记录。末尾历史追加说明不能替代本表及原条目。已回填C10/C13/C14及本轮C24、C77–C81的确定过时内容；其余条目仍须逐项复核，不能假称整份PLAN已全部核准。最新[状态复核与收口顺序](PLAN-STATUS-REVIEW.md)区分维护欠账和真实剩余工作。

## 执行顺序

1. 建立逐小节、逐练习、逐案例的原文清单，保存位置和内容摘要，追踪原文变动。下面的工作包是实现顺序，原文清单是防遗漏的复核入口。
2. 下载并集中保存官方配置和必要实现源码，固定 revision、URL、SHA256、下载时间。模型配置、硬件供给、业务假设、测量输入各自存放；公式只读取这些输入。
3. 先实现单位、矩阵／张量、计量口径和模型适配器，再实现各专题计算。每个适配器必须拒绝未覆盖的结构，不能把未知模型套进 Dense 公式。
4. 每项交付可读函数、CLI、完整输入、JSON 结果和面向读者的 Markdown 表；先完成精确算术，再完成有声明的分析模型与敏感性扫描。
5. 逐项用独立手算、守恒关系、小规模枚举或官方权重形状元数据检查。公式的单元测试不能代替真实性能证据。
6. 将结果及复现命令补入相应 outline，重新生成 skeleton.html，检查链接和原文覆盖。未完成项保持未勾选，不能仅因有脚本或有入口而标为完成。

## 当前优先级与验收状态（2026-09-09 调整）

此前实际执行在基础工作尚未验收时，穿插推进了章节专题和新增多模态要求；硬件栏虽标“优先”，却没有形成先收口的执行约束。后续按以下顺序推进，不能用新增脚本数量替代基础验收。

1. **P0：硬件基础表 H01–H07。** 并行审查 NVIDIA 数据中心／RTX、Apple、昇腾，主线统一字段和来源校验。先提交逐型号、逐字段状态表，再补官方证据、更新目录与读者表、验证计算选择规则，最后逐项验收。H01–H07现已按当前目录完成验收；后续硬件变更需重新绑定受影响记录。主线转入P1，已交付专题按依赖集成。
2. **P1：公共基础与模型输入 F01–F03。** 核对官方配置、源码、checkpoint 元数据的一致性和覆盖；先处理会改变矩阵形状、精度选择、容量或总量的错误，再补模型缺项。Kimi K3 的官方形状冲突保留明确限制。
3. **P2：模型与请求工作量。** 按依赖完成文本及 VL／Omni 的编码→语言 prefill→decode，以及生成模型的条件编码→迭代／码本生成→解码器；逐矩阵计算和阶段状态先于性能映射。用户新增的视觉编码要求继续保留在 C81，不因调整优先级删除。
4. **P3：章节计算。** 在输入和计量契约稳定后，按章节顺序收口；跨章共用模块先做。已有部分实现优先补到可验收，随后推进尚无实现的条目，避免持续只增加局部子账。
5. **P4：全书最终审计 F04。** 每批均完成必要测试、结果再生及正文同步；最终逐原文清单核对覆盖，不能以测试数或结果文件数表示全书完成率。

硬件字段使用四种审查状态：**已核实**（有可追溯官方证据）、**待核查**（工作未做完）、**所查官方材料未披露**（列明查过的材料及日期，值保持未知）、**来源冲突**（保留双方值和采用条件）。“未披露”不等于设备不支持，也不宣称厂商任何地方都从未公开。

复选框表示整个工作包验收；未勾选可能是部分实现，也可能尚未开始，必须在审查记录中分开。字段没有公开数值时，只要规定型号范围已查证、缺口有证据、未知输入会被计算器正确处理，可以完成相应的**资料审查**；不能为填满表格编值，也不能把未做的检索写成“未披露”。仍未查证的型号或来源冲突必须保留为具体待办，不缩小原计划范围来勾选。

当前已核对本地记录：151 个硬件配置、471 条峰值记录；H01–H07 已按当前目录完成官方资料、字段口径与计算准入验收。详见 [硬件审查记录](HARDWARE-AUDIT.md)。这些数量描述已收录内容，不代表字段完整性或当前官方规格重新核验完成。

## 目录与计量约定

- `src/infra_calc/`：CLI、公共模块、模型适配器与 `topics/` 专题计算。
- `configs/models/`：官方原始 JSON；`configs/sources.lock.json`：来源锁文件；`sources/`：只读参考源码，不执行下载的代码。
- `scenarios/`：读者可编辑的工作负载与格式假设；`results/`：确定性生成的结果。
- `inventory/`：正文、扩写资料、案例与旧脚本的待复核清单；`tests/`：有独立参照的算术及契约检查。
- FLOPs 中一次乘加计 2；一般算术、exp／rsqrt／比较／整数操作分列。字节为整数，GB=10^9、GiB=2^30；时长统一秒后显示。
- 权重常驻量、KV／递推状态容量、逐算子逻辑操作数、理想一次读取载荷、特定循环的接口流量、实测 HBM 字节分列。不同层级不得直接相加。
- 矩阵同时列数学右乘 `[in,out]` 与框架参数 `[out,in]`，GQA 的头共享和广播不制造额外参数。
- 硬件输入注明型号、精度、稀疏与方向；MFU、有效带宽、价格和服务能力必须注明是固定来源、测量还是情景假设。
- 全模型汇总必须包括词嵌入、输出头、归一化、门控与状态更新；近似或局部和必须用名称说明，不能称全模型精确 FLOPs。

## 工作包 checklist

每一项的完成证据应含 `源码 → 场景 → 结果 → 验证 → outline 落点`。目前所有未列完成证据的项目均待完成。多个工作包可以服务同一练习；某工作包完成不代表整项硬件／质量实验已经完成。

### 公共基础

- [ ] F01 原文清单：240 个正文小节、117 项练习、扩写资料与所有案例逐条纳入，审查计算范围及旧脚本迁移。
- [x] F02 必要官方输入已按原11类及用户新增6类验收：Qwen3四型、公开70B代表、V3/V4 Flash/Pro、Kimi K3、Qwen3.5/VL及Omni/音频/图像/视频组件。证据：[498根来源/48辅助记录验收](inventory/f02-source-review.json)、[有限最终审查](research/f02-final-review/REVIEW.md)、[Qwen3.5独立shape与Range检查](research/f02-qwen35-independent/REVIEW.md)。70B采用DeepSeek原发布者R1-Distill-Llama-70B，保留旧Meta401状态及身份；K3一次当前官方API核对仍同revision，69个A_log冲突保留。必要固定输入验收不等于完整forward、tokenizer、MTP/视觉执行或运行依赖闭包已完成。
- [x] F03 公共单位、形状、逻辑读写量、输出与配置校验、CLI、离线复现及有界来源重取已验收。证据：[契约验收](inventory/f03-contract-review.json)、[16项独立边界测试](tests/test_foundation_contract.py)、[有限复查](research/f03-foundation-review/FOLLOWUP.md)。560测试、1279产物及10图通过；拒绝非法计数/非finite JSON，锁定长度与SHA，严格Range及原子替换，复现绑定入口与明确产物。原文覆盖、场景完整性和实际后端流量继续由F01/F04及各专题验收。
第2章原文覆盖证据：[29条逐要求映射](research/chapter02-coverage/README.md)、[固定映射与文件绑定](research/chapter02-coverage/coverage.json)。该审计保留原实验整体partial与真实接口反例，不将441文件哈希等同覆盖完成。审计指出的02-08缺p95现由[workload-profiles](src/infra_calc/topics/workload_profiles.py)补9组44条封存记录；旧审计快照保留，其他原要求继续待办。

- [ ] F04 全部结果可再生、原文到工作包覆盖审计、outline 与网页同步、读者入口。

### 硬件基础表（按用户补充要求优先）

- [x] H01 NVIDIA 数据中心：A100/A800、H100/H200/H20、B200/B300、GB200/GB300、Vera Rubin原10家族及25条约定形态均完成官方来源审查。证据：[32条NVIDIA子集/37原件SHA验收](inventory/h01-source-review.json)、[可读表](results/hardware.md)、[审查记录](HARDWARE-AUDIT.md)、第4章H05-field-audit。H20/普通A800完整性能、B300单GPU功率、GB300Superchip GPU-only内存等有范围未知继续保留；不冒称所有数值已公开；H05逐精度/clock映射与H07全局来源工作已有各自正式验收，见下方对应条目。
- [x] H02 NVIDIA 游戏／工作站：4090、5090、RTX A6000、RTX 6000 Ada、RTX PRO 6000 Blackwell Workstation/Max-Q/Server；七个原定SKU均已核对，独立功率、六卡Boost和七卡互联来源已补入。证据：[逐SKU官方审查](research/hardware-nvidia-closure.md)、[公共表](results/hardware.md)、[字段/准入报告](results/hardware-audit.json)、[验收记录](inventory/h02-review.json)、第4章H05-field-audit。完成官方基础资料及明确未知状态审查；Server Tensor累加/稀疏、Boost和PRO所查材料缺失的NVLink项保持未知，未推断不支持，未声明实测性能；H05/H07全局来源与语义验收另有独立证据，见对应已完成条目。
- [x] H03 昇腾 NPU：910各代、950PR/950DT、Atlas板卡及A2/A3处理器/节点/整机已完成约定官方公开来源审查，共22配置181峰值。证据：[合入后子集与12来源验收](inventory/h03-source-review.json)、[800I白皮书及公开兼容查询](research/h03-final-public-review.md)、[可读表](results/hardware.md)、第4章H05-field-audit。Cube/Vector/宣传相加值与芯片/整机分别保留；800I正文07版明确dense与14.6kW整机最大输入功率。所查公开工具无精确B/C bin及950DT板卡映射，950稀疏/部分累加与执行单元、A3带宽范围及288.7数值解释仍保留有界未知或冲突，不猜测料号或将公开查询空结果写成不存在。H05/H07已另有正式验收记录，见对应条目。
- [x] H04 Apple M 系列：M1–M6已核官方GPU档位/内存97组合，覆盖六条Mac产品线，含M2 Max38核/96GB、历史M3Ultra512GB和M5Ultra未来供应窗口。证据：[97组合](research/hardware-apple-closure/integration.md)、[桌面交叉审查](research/hardware-apple-desktop-audit/review.md)、[Apple子集与36来源SHA验收](inventory/h04-source-review.json)、[可读表](results/hardware.md)、整机错配拒绝测试与第4章H05-field-audit。保持原官方规格范围；GPU/Neural Engine独立、统一内存共享，所查材料未披露的精度峰值/M1带宽/GPU TDP保持未知，不声明当前库存或实测性能。
- [x] H05 全471条峰值的输入/累加类型、执行单元、dense/结构化稀疏、时钟/功率条件、芯片/系统范围、原值/派生和来源脚注已完成逐字段审查。证据：[正式验收](inventory/h05-source-review.json)、[471行/5181字段覆盖](research/h05-final-coverage/coverage.json)、[独立回放](research/h05-independent-final/verification.json)、[可读表](results/hardware.md)、第4章H05-field-audit。3806字段在引用范围已核，1375字段经有限来源审查仍未知；不把未知写成不支持。补106峰值证据，数值/精度键不变；Blackwell BF16以官方SKU加明确指令组合联合确认，Hopper FP8特定wgmma内部精度限制单列，不把名义FP32累加类型等同全部内部单精度舍入。
- [x] H06 Roofline 按精度和执行单元选记录，拒绝未知 sparsity、将 INT TOPS 当 FLOPs、将 TF32 当 IEEE FP32、将 MoE 激活稀疏当 2:4 硬件稀疏；理论峰值和有效供给分开。证据：[匹配与校验](src/infra_calc/hardware.py)、[真实Q投影](src/infra_calc/topics/projection.py)、[27个场景与结果](results/README.md)、[拒绝与守恒检查](tests/test_accounting.py)、[第4章回填](../outlines/04-加速器架构.md)。这是计算契约完成；H01–H05／H07已有各自独立规格审查验收，C22有限逐层资源界也已接入，但完整负载映射与运行时仍未由本条闭合。
- [x] H07 官方原件与字段来源校验、旧新规格差异登记及价格/交付/实测证据分离完成。证据：[当前151配置471峰值验收](inventory/h07-source-review.json)、[97硬件原件/85目录来源审查](research/h07-review/audit.json)、[14项差异登记](research/h07-review/version-differences.json)、[商业及测量证据分离](research/h07-review/commercial-measurement-separation.json)。73条availability补独立位置及语义范围，公共校验器拒绝无来源状态；源指针无悬空/缺位。接受当前目录溯源，不宣称全部现价、实际交付或实测性能已取得，不代替H05逐峰值可用性审查。

### 第 1 章：资源估算

- [x] C01 单位与容量：BF16／INT8 70B、GB/GiB、400 Gb/s、总容量与逐卡容量（1.2、1.3）。证据：[实现](src/infra_calc/topics/resource_basics.py)、六个教学场景与[结果](results/README.md)、单位／逐卡反例／打包边界检查、正文 C01-units-capacity。70B 是明确的名义教学参数，实际模型形状和放置继续使用专用适配器。
- [x] C02 70 GB/3.35 TB/s、计算与通信下界、Roofline、KV／并发／批复用敏感性（1.3）。证据：[解码预算](src/infra_calc/topics/decode_budget.py)、[通信预算](src/infra_calc/topics/resource_basics.py)、[独立窗口](src/infra_calc/topics/memory_concurrency.py)、8 个 decode-budget 场景、交叉点／精度／容量检查与 C02-decode-budget 回填。限第 1 章声明的教学模型；实际逐算子、转换／工作区及测量继续归后续专题。
- [x] C03 在途请求、带宽—延迟、独立访存窗口（1.3.3，复用第 4、7 章）。证据：[实现](src/infra_calc/topics/memory_concurrency.py)、4 个正文场景、官方 KV 载荷／取整／并发与 batch 区分检查、C03-memory-concurrency 回填。默认接口条件是教学输入；实测曲线与完整执行仍归实验／运行时专题。
- [x] C04 TPU历史语音需求与SmartNIC核时／包率／PCIe约束（1.4、1.5）。证据：[TPU计算](src/infra_calc/topics/tpu_demand.py)、[NIC计算](src/infra_calc/topics/nic_budget.py)、11个复现场景、7项独立测试、官方论文原件锁与全局哈希、正文C04-tpu-demand/C04-nic-budget及1章扩写落点。历史锚点与线性/容量/卸载条件分开；完成原手算计算契约，不声称真实历史服务器库存、完整虚拟化、实测卸载收益或成本。
- [ ] C05 历史 UB 容量聚合、交接频次及当时条件下的选择翻转（1.6）。 [ub-scope](src/infra_calc/topics/ub_scope.py)现接10个现代Qwen教学场景、逐卡/消息图与精确带宽/容量边界，CLI及1.6正文C05-modern-scope完成；[历史缺口](research/c05-integration/acceptance-gaps.md)明确当年负载/设备/接口条件未取得，不能用现代示例勾选原历史要求。

### 第 2 章：真实模型逐算子核算

- [x] C06 四token／三层RNN与因果Transformer的工作、状态和缓存前后数值一致（2.1）。证据：[实现](src/infra_calc/topics/sequence_dependencies.py)、[逐矩阵/依赖图/实际输出](results/sequence-dependencies-book.md)、3项独立测试与正文C06-sequence-dependencies。固定教学权重和输入完全导出；十次同模型缓存/重算检查通过。只完成声明教学模型的矩阵、状态与图契约，非真实checkpoint、非矩阵性能或实际时延。
- [x] C07 Qwen3-8B 逐层 Q/K/V/O、QK Norm、RoPE、QKᵀ、Softmax、PV、SwiGLU、残差、最终 RMSNorm、嵌入／输出头；8192 prefill、B=1/64 decode、6144+2048 前缀续算（2.2，实验 2-2）。证据：[实现](src/infra_calc/models/qwen3.py)、[场景](scenarios/book.json)、[结果](results/README.md)、[官方索引与守恒检查](tests/test_accounting.py)、[正文回填](../outlines/02-模型架构.md)。完成的是声明的逻辑图与操作数载荷；tile、后端 HBM 与性能测量归 C25–C31。
- [x] C08 GQA/MHA/MQA、整段生成累计读取／写入与最终容量；完整／命中前缀比较（2.3）。证据：[实现](src/infra_calc/topics/cache_sequence.py)、6 个 Qwen／K3 场景与[结果](results/README.md)、逐步枚举／容量守恒／头共享检查、正文 C08-cache-sequence。含无缓存重算与 K3 两种 MLA 路径；口径为逻辑载荷，物理共享、工作区和并行复制仍归 C13／C32。
- [x] C09 K3 MLA 显式展开与权重吸收的矩阵、缓存和额外分支；输出门控（2.3.3）。证据：[实现](src/infra_calc/topics/k3_mla.py)、[两路径结果](results/README.md)、[小矩阵代数／形状／容量检查](tests/test_accounting.py)、正文 C09-MLA 回填。完成矩阵与容量口径；真实后端 padding／HBM 仍归执行专题，不将 compact 称为 HF 现行缓存。
- [ ] C10 V4-Flash 43 层窗口/CSA/HCA、索引扫描／top-k、压缩器、残差 mHC、输出头与 MTP 边界；8K/128K/1M、B=1/64、prefill/decode/前缀命中（2.4.1–2）。[基础前向汇总](src/infra_calc/topics/v4_forward.py)已组合矩阵／主要算术／状态，基础汇总的coverage仍保留运行时转换／分配和剩余复制／量化；[Flash单层MTP](src/infra_calc/topics/v4_mtp_forward.py)已另行接公共CLI、四场景和正文，含逐矩阵／量化／独立ring与1575条header核对（[验收](research/v4-mtp-integration/acceptance.json)），不再列为完全未做。实际草稿对齐、接受／验证／回滚尚未连接；合法逐token前缀续算已由[v4-prefix-continuation](src/infra_calc/topics/v4_prefix_continuation.py)接入6144+2048等场景，恢复成本、并行chunk与完整runtime继续待补；官方 checkpoint 全量索引／110 分片头与基础参数总数已核验；[非routed FP8 Linear](src/infra_calc/topics/v4_fp8_linear.py)补官方量化、tile与scale共享六场景（独立子账，不重复加入forward）；其余覆盖继续待办。
- [ ] C11 K3 69 KDA+24 MLA、短卷积、递推和块式 prefill、AttnRes、状态精度／检查点；与 V4 机制及真实格式比较（2.4.3）。[文本前向汇总](src/infra_calc/topics/k3_forward.py)已连接 MLA／KDA／专家／AttnRes 与全局节点，块式数学替换递推核心且通过数值等价检查；全部 checkpoint 索引／头及实际存储 dtype 已核验；69 个 A_log 存在 128 对 96 的官方来源差异；全header和邻接矩阵已核验，多2208参数/8832B，固定参考gate和参数加载探针拒绝该形状。状态布局别名兼容已确认，但不能修复该冲突，仍需官方匹配实现或转换依据。运行时量化转换与融合后端计量待完成。
- [ ] C12 Qwen3 MoE、V4、K3 潜空间专家：全参数、激活工作、每专家 token 数、批内专家并集、共享专家／dense 首层／路由（2.5）。Qwen3 两个 MoE 已完成逻辑前向与官方索引验证，见 [实现](src/infra_calc/models/qwen3_moe.py)；V4／K3 的 [FFN 矩阵子账](src/infra_calc/topics/experts.py)已实现，含 hash router、shared、latent、dense 首层；路由／激活／归一化／合并算术已单列，参考 dispatch 操作数与排序／直方图端点已单列，内部流量和完整前向未完成，保留待办。
- [ ] C13 8B/32B/70B/235B 与 24/48/80 GB、八卡、BF16/8/4-bit 元数据／工作区／KV 并发容量扫描；深宽与专家颗粒度变化（2.6.1–2）。[单设备扫描](src/infra_calc/topics/capacity_scan.py)已覆盖 Qwen8/32/235、8K/32K、分组 scale／逐行尾部与条件式并发上限；70B真实单设备容量及BF16逐rank TP/PP/DP六场景已接入；[Dense低位多卡](src/infra_calc/topics/dense_quantized_placement.py)与[Qwen235逐卡容量](src/infra_calc/topics/qwen235_placement.py)已补local-K分组/尾部、TP复制及最差rank门槛；[架构变体](src/infra_calc/topics/architecture_variants.py)已补声明的深宽/KV/FFN变化。[专家颗粒度](src/infra_calc/topics/qwen235_expert_granularity.py)六场景、[深宽tile](src/infra_calc/topics/architecture_tile_work.py)四场景、TP8/EP8容量场景，以及容量曲线和架构形状图已完成公共接入；不能再把这些列为未实现。有限缺口S10/S12/S14的完成证据分别见[原句审核目录](research/ch2-6-coverage-audit/)。[当前逐句验收](research/ch2-6-coverage-audit/C13-current-review.md)已核14条：11完成、3部分完成。剩余S01同任务大小模型质量/资源、S06质量/SLO/成本经济点、S11最小质量/训练评测；[S13条件汇总](research/ch2-6-coverage-audit/S13-resolution.json)已验收完成；当前空框不表示上述计算仍缺失；实际workspace/低位执行与质量未由条件算例证明，也不自动追加为本项原文之外的验收要求。
- [ ] C14 Chat／Agent／reasoning／MTP 的调用、输入／输出与质量口径，模型选择的条件式比较（2.6.3–5）。已完成：四模型完整逻辑请求账、[封存Chat到工作量](research/trace-resource-bridge-integration/acceptance.json)、[H100精度匹配资源约束](research/request-hardware-bridge-integration/acceptance.json)、[Flash单层MTP](research/v4-mtp-integration/acceptance.json)；[同轨迹缓存保留/条件取回](research/trace-cache-lifecycle-integration/acceptance.json)三场景已验收。仍缺：固定同任务质量对照与最小选择实验、实际MTP草稿/验证执行连接、图2-8已由[原轨迹六面板](research/chat-agent-figure-integration/acceptance.json)完成有限绘图交付（含明确假设KV），不再列为未交付。物理页身份和寿命缺少观测，不用应用间隔冒充。

### 第 3 章：负载与训练投入

- [ ] C15 成对长度与到达轨迹、同均值不同分布、prefill/decode 资源随形状变化（3.1.1–2）。[成对轨迹重放](src/infra_calc/topics/request_trace.py)已覆盖 Qwen8/235 的逐请求矩阵、FIFO 等待／TTFT／p95、KV 存活与均值相同的相关性／到达对照；有限共享 KV 预算已加入按声明输出上限预留的 FIFO 准入，活跃／预留峰值分开；V4、batch／命中扫描、真实放置与服务校准仍待完成。
- [ ] C16 reasoning 预算／成功率／有效输出成本；Agent 多轮前缀、工具等待、状态驻留、视觉 E→P→D 与 EC（3.1.2–3）。[真实 Agent 轨迹](src/infra_calc/topics/agent_trace.py)已导入实验 3-4 的两条哈希锁定原始记录，核对逐轮 token／命中、冷重算对照、实测关键路径替换与假设 KV 工具等待驻留，保留失败／截断和两层任务判据；多任务质量、分支工具、实际缓存生命周期及视觉仍待完成。
- [ ] C17 实时语音帧率、流水／响应时限、抖动与尾部预算（3.1.4）。[逐块教学时序](src/infra_calc/topics/audio_timing.py)已覆盖显式模型／链路流水、乱序传播、固定截止／按序停顿、PCM ready queue 和设备量子静音响应；[当前证据复核](research/c17-status-review/review.json)另确认两份历史记录已分析首块接收与到达间隔，并核对软件播放位置的源码契约；这些不能证明设备首播或取消。仍缺固定记录的实际首播/打断、模型/网络/缓冲可比较证据及图3-4的实际时序；声学配置与真实取消／flush继续待办。
- [ ] C18 Dense 6ND 与注意力修正、MoE 实际矩阵、SFT token mask、RL rollout/reward/update 分账（3.2.1–2）。[Dense 训练矩阵子账](src/infra_calc/topics/training_matrix.py)已覆盖 Qwen8/32/235 的前向／两个梯度、有效因果注意力、6ND 差额、显式输出头筛选与参数状态；Qwen MoE 已按各专家 token 数计量；非矩阵反向、重计算、[RL 批次子账](src/infra_calc/topics/rl_cycle.py)已连接 Qwen rollout／reference／teacher／更新及权重载荷，保持有效样本目标并计拒收开销；[条件式资源供给](src/infra_calc/topics/rl_supply.py)已支持阶段速率／验证服务槽／同步带宽导入、共享池累加和倍率扫描；V4/K3 训练、完整验证工作与实际阶段供给仍待完成。
- [x] C19 scaling law 受控数据拟合与预算最优、训练加生命周期服务成本、外推敏感性（3.2.3）。 [scaling-law](src/infra_calc/topics/scaling_law.py)已接三组合成教学场景、解析/有限候选最优、独立留出、声明生命周期费用和指数敏感性，原13项加10项边界测试通过，另7项独立缺陷回归已修复；[real-scaling-fit](src/infra_calc/topics/real_scaling_fit.py)已接作者8个C4点、6fit/2预定holdout及四项敏感性；[real-scaling-lifecycle](src/infra_calc/topics/real_scaling_lifecycle.py)已接主law与敏感性的调用量交叉和外推边界，plot-real-scaling已生成真实点/生命周期双图。[逐项状态复核](research/c19-status-review/README.md)确认原工作包及实验3-8的有限计算要求已交付，39专项测试全部通过。完整论文复现、同任务质量映射、实际硬件价格与置信区间未提供，继续作为适用限制；不追加为本计算条目的完成门槛。旧教学生成段落的过时待办已从生成源修正，结果再生、图依赖更新、正文及网页同步验证通过；该编辑欠账已关闭。
- [x] C20 Llama/Qwen/DeepSeek公开训练投入复算（3.2.4）。证据：[实现](src/infra_calc/topics/training_history.py)、[13模型/16归档历史表](results/training-history-published.md)、五场景、15项独立测试、[复核](research/c20-independent-review/REVIEW.md)、[验收记录](inventory/c20-review.json)、正文C20-training-history。总/激活参数、6ND代理、阶段小时/替代分支、reported阶段MFU和跨source条件日历分列；生命周期费用仅声明scope。完成公开字段与计算契约，原图计划、质量对齐实验及未披露的全程日志不借此标完成。

### 第 4 章：芯片资源

- [ ] C21 注意力矩阵／向量／特殊函数工作、FA4 资源配比；数据格式与转换开销（4.1–2）。 [公共FA4表1复算](results/fa4-qwen8-resource-balance.md)已绑定归档论文与Qwen8配置，16场景逐QK/PV矩阵、SMEM重复读取、指数及倍率切换；独立183检查与3专项tests（含三源破坏拒绝）通过。[公共接入验收](research/fa4-resource-integration/acceptance.json)已完成统一CLI、固定结果、来源目录与正文/网页同步（806tests784通过22跳过；1795产物/22图）；三架构完整非矩阵及低精度执行范围仍需逐条验收，不因表1算例完成而勾整项。
- [ ] C22 HBM/GDDR/统一内存容量与带宽、GEMM/Decode Roofline 及 batch 交叉点（4.3、4.5）。 已有25场景[逐阶段资源界](src/infra_calc/topics/stage_resource_bounds.py)，覆盖Qwen8/V4的阶段、batch和资源倍率；不能把空框解释为未实现。实验4-3已接[公共容量/带宽对照](results/storage-generation-qwen8-235.md)：官方Qwen8/235逐张量三格式、两上下文三batch及MoE路由，五产品与两种独立资源替换共54工作负载/810对照；6384独立闭式检查、3专项tests通过。[公共接入验收](research/storage-generation-integration/acceptance.json)已完成CLI、固定场景、结果再生与正文/网页同步（803测试781通过22跳过，1793产物/22图）；原要求的完整Roofline代际范围、图4-4/4-6及各小节覆盖仍须逐项验收，本条不勾选。
- [ ] C23 片上 tile／累加精度／双缓冲／地址元数据、矩阵—向量交接预算（4.4）。 已有gemm-tiles容量/重读与stream-buffer FIFO，但不能据双缓冲容量直接推时延。[公共注意力输入流水](results/attention-input-base.md)连接真实Qwen头宽、同步寄存器中转、异步在途/有限槽消费结束释放，六场景扫描K分块/1至8槽/供给/容量，1144独立逐时刻检查及4专项tests通过。[公共接入验收](research/attention-input-integration/acceptance.json)已完成统一CLI、可编辑输入、六固定场景、正文/网页与结果再生（810tests788通过22跳过；1807产物/22图）；[公共V4搬运坐标](results/v4-copy-coordinates-m32.md)新增真实共享专家三GEMM的tile起点/字节偏移/stride/scale及重复读取，M32/M64分别518361/1028473独立区间检查和3tests通过；[公共接入验收](research/v4-copy-integration/acceptance.json)已完成CLI、两固定场景和章节同步（813tests791通过22跳过；1811产物/22图）；[编译产物身份审查](research/v4-compiled-backend-audit/README.md)已找到SGLang SM120 FP8产物并统计889个静态PTX位置，但它不同于官方TileLang内核，不能替代目标的编译计数；[公共矩阵—向量交接](results/matrix-vector-staged-rows32-slots2.md)已补完整行QK→Softmax→PV依赖、两种声明路径、有限槽位和八场景，370独立tick检查及4tests通过；[公共接入验收](research/matrix-vector-integration/acceptance.json)已完成CLI、可编辑输入、八固定场景与正文网页（817tests795通过22跳过；1827产物/22图）；实际编译地址/描述符与指令、厂商专用通路映射和剩余原文要求继续待办。
- [ ] C24 Mac/RTX 与公开芯片参数的任务／整机／能耗成本比较，面积／功耗／封装／互联资源扫描（4.5–6）。 [公共配对投影费用/功率条件](results/paired-projection-unknown.md)复用实验4-6同夹具BF16原记录，11组16次批平均墙钟重算门槛，费用/功率缺失默认null，3场景136独立检查通过；[公共接入验收](research/paired-projection-integration/acceptance.json)已完成CLI、固定输入、六份JSON/Markdown结果及正文同步，4专项tests包含原始输入破坏拒绝，全套821项（799通过、22跳过）、1833产物/22图校验通过。仍缺：同期整机功率与实际费用未观测，不以TDP替代；生命周期、面积/封装/互联及剩余原文要求继续待办。

### 第 5 章：算子、融合与运行时

- [x] C25 GEMM 循环与 tile 枚举、128 MiB 下界、3096/1560 MiB 流量、24/80 KiB 缓冲，行归约与 partial buffer（5.1）。[GEMM tile 账](src/infra_calc/topics/gemm_tiles.py)已覆盖官方 Qwen 单支投影、正文全部容量／接口常数、output-stationary 与 K 外层 partial、双缓冲／尾块及容量筛选；[行归约](src/infra_calc/topics/row_reduction.py)已补三阶段 partial／inverse、重读、尾分片与舍入反例；[bank 枚举](src/infra_calc/topics/bank_mapping.py)已补32／33跨度、端口与同址广播，官方映射原件已锁定；[小循环访问](src/infra_calc/topics/loop_access.py)已逐数组表达式计量、尾块事件／数值回放，并匹配实验5-1的32组原始实测记录，哈希与离线验证通过。四类计算均有CLI、固定场景、结果、独立检查和第5章C25回填；完成本工作包的计量范围，真实GPU归约调度／完整缓存流量仍属于后端实测，不以CPU源码字节替代。
- [ ] C26 中间张量 2X、布局重排、活动张量生命周期和融合峰值，SiLU/Mul/量化链（5.2.1、5.3）。[主张量生命周期](src/infra_calc/topics/fusion_lifetime.py)已覆盖真实Qwen形状、2X、布局物化、连续分组与分配／释放联合峰值；固定尺度cast明确为条件模型，动态scale、局部scratch及完整执行峰值仍待完成。
- [x] C27 在线 Softmax 数值校验、因果 tile 工作、128 KiB 预算与 304/204 MiB 接口流量，循环／缩放代价（5.2.2）。[在线状态](src/infra_calc/topics/online_softmax.py)已覆盖(m,l,U)顺序／树形合并、空块／全掩码和独立稳定softmax检查，合并算术分列；[官方单头tile账](src/infra_calc/topics/attention_tiles.py)已覆盖因果边界、128KiB预算、204／304／436MiB、K/V双槽及旧输出缩放；四场景、尾块逐查询枚举、容量最大性检查和第5章C27回填齐全。完成所列分析计量，真实后端scratch／HBM／性能仍按实验输入另核，不作测量声明。
- [x] C28 FIFO 生产消费、48+32>64 KiB、64 MiB 主机拷贝、24 GiB/s、双端槽复用与异步时序（5.2.3）。
  - `host-transfer` 已覆盖双端槽独立释放、精确时序与四场景；`stream-buffer` 已覆盖48+32>64 KiB、五块逐事件占用、统一布局／单槽／慢生产／不足一槽变体及背压。独立逐格模拟核对递推，原进度与最后取走分列，CLI／场景／结果／正文回填齐全。完成本工作包的分析计量，实际API并发、转换成本、完整下游计算和分支图需后端记录，不冒充已测。
- [ ] C29 2^(k−1) 融合划分、合法性／舍入反例、融合重读／局部快整链慢（5.3）。[量化GEMM接口账](src/infra_calc/topics/quantized_gemm.py)已覆盖官方Qwen专家形状、444／620／588 MiB、全行scale交接与输出tile／尾部对照；连续分组枚举已在C26实现，[数值反例](src/infra_calc/topics/fusion_numerics.py)已补官方E4M3FN精确舍入／块序与不可逆局部状态检查；[在线可合并状态](src/infra_calc/topics/online_softmax.py)已验证顺序／树形与掩码单位元；一般变换的合法性需逐算子证明，完整链时间继续待完成。
- [x] C30 编译／调优摊销、形状 padding、CUDA Graph 拷贝与重放、persistent/微批提交／并发时间线（5.4）。[图执行成本](src/infra_calc/topics/graph_execution.py)已覆盖官方边界字节、2／16 MiB输入路径选择、FFN补齐、精确回本阈值和配置／设备有限流水；四场景与正文回填齐全。[候选部署账](src/infra_calc/topics/optimization_deployment.py)已补形状平均比值、调用频数、已知失败／缺失候选回退、分派与额外准备摊销，完整频数组阈值单列。[形状特化账](src/infra_calc/topics/shape_specialization.py)已补真实FFN工作、频数分布、最小可容纳桶、未覆盖回退、按工件缓存／准备与精确总时间交点；五场景与正文回填完成。图5-6已由同一结果生成SVG／PNG及精确逐点数据，图输入／产物哈希纳入校验；[运行记录复核](src/infra_calc/topics/runtime_trace.py)已补21方案原始中位数／范围、9段Nsight启动／kernel／复制计数及区间并集、顺序微批和padding张量账；MPK作者匹配模型／硬件比值单列。[设备任务账](src/infra_calc/topics/persistent_tasks.py)已补官方up→SiLU行块、两类独立worker、任务／完成事件／依赖计数、显式分派成本、尾块及中间存活；无开销／单块／高开销与区间峰值独立检查。所列分析计量、CLI、场景、图与正文回填齐全，勾选本工作包；MPK真实任务实现、共享SM驻留／轮询／原子成本按具体后端另核，未冒充本机运行。
- [ ] C31 Amdahl 与依赖图的请求收益、共享资源竞争及瓶颈转移；校准记录导入（5.5）。[请求DAG](src/infra_calc/topics/request_dag.py)已补确定性列表调度、依赖／串行资源边、关键路径转移、旧路径误推与串行等价Amdahl分列，四个教学情景、JSON输入及正文回填。[两微批争用账](src/infra_calc/topics/microbatch_overlap.py)已补官方FFN工作守恒／288与576MiB、1.20/1.36/1.16/1.28ms、联合窗口严格收益阈值和不等分变体，复用DAG保留填充排空。实际并发资源减速与实验5-9同引擎替换前后校准仍待补。

### 第 6 章：超节点

- [ ] C32 Qwen Dense TP/PP/DP 枚举，逐卡权重／KV／工作区／头复制与通信（6.1–2）。[逐卡放置](src/infra_calc/topics/dense_placement.py)已覆盖 BF16 权重形状、实际头身份、PP 首尾／层数、DP 复制、矩阵工作与消息载荷；[基础通信路径](src/infra_calc/topics/dense_communication.py)已连接嵌入归约、层输出、PP hidden、最后 logits 与 token 回传；[FIFO 流水](src/infra_calc/topics/pipeline_schedule.py)已覆盖阶段／链路串行、反馈依赖与双端边界缓冲存活，有限槽位反压／预留池与活跃峰值已分开；控制元数据、完整工作区、后端阶段校准与实际时延仍待完成。
- [ ] C33 Qwen235B/V4/K3 专家 EP/TP/PP 组合、路由倾斜、组播去重及逐卡峰值（6.3）。现有公共qwen235-placement、moe-dedup、grouped-experts已分别覆盖容量/路由去重/局部矩阵；[同cohort联合执行](src/infra_calc/topics/qwen235_execution.py)经独立审查后已接公共CLI及七场景。其他模型完整所有权图、实际通信/运行时与多目标扫描继续待补。
- [ ] C34 ring/tree/all-reduce/all-gather/reduce-scatter/all-to-all 的载荷、轮次、α+V/B 与资源竞争（6.4）。[ring 子账](src/infra_calc/topics/ring_collective.py)已覆盖 Qwen Dense 激活、RS/AG 两阶段、逐轮调度、数值回放和六个场景；[未分段 binomial tree](src/infra_calc/topics/tree_collective.py)已增加逐 rank 负载、非二次幂回放及同消息比较；[assignment all-to-all](src/infra_calc/topics/all_to_all.py)已覆盖源—目的矩阵、均匀／热点、逐轮屏障、端点负载与反向 combine；[显式 token 去重](src/infra_calc/topics/moe_dedup.py)已比较相同 assignment 直方图下不同目的集合及部分归约位置，元数据／执行代价仍待完成；[物理资源累加器](src/infra_calc/traffic.py)和[NUMA 中转算例](src/infra_calc/topics/numa_staging.py)已覆盖共享资源、方向、逐轮下界，[有向物理环路径](src/infra_calc/topics/collective_paths.py)已按官方Swing式2与递归对端枚举前三轮96消息、最短路径和逐链路字节，独立BFS／守恒检查及正文回填完成；逐轮路径图已由同一结果生成六面板SVG／PNG，零负载方向与全发送者字节一起保留，图哈希纳入校验；完整拓扑／争用和执行校准继续待办。
- [ ] C35 拓扑割集、链路方向、机柜功率／布线／同步规模、八卡到超节点敏感性（6.5）。[拓扑分配子账](src/infra_calc/topics/topology_allocation.py)已补4×4周期位置精确窗口装箱、同向割集均分／准入上限、ring有效端口带宽与准备摊销，prefill／decode和无收益变体齐全。实际路径映射、物理供电／布线和故障域仍待补。
- [x] C36 池化容量、远端访问频次、故障域、复制与多副本成本选择（6.6）。按[原文逐要求验收](research/supernode-integration/scope-review.md)完成有限教学计算：[内存池](src/infra_calc/topics/memory_pool_access.py)覆盖4×64GiB容量、迁移/借用、1/2/3副本与45组故障依赖和访问频次；[增长KV](src/infra_calc/topics/growing_remote_kv.py)补Qwen8/Qwen3.6逐位置读取、初始化/追加复制与commit epoch；[实验6-10](src/infra_calc/topics/supernode_cohort_cost.py)接同8卡独立物理超节点分组、Qwen8/32真实容量、54个模型/并发/deadline/恢复条件、完整响应SLO与有效请求费用。图6-8明确取回为远端读取，图6-9及精确阶梯已生成。1701独立tick候选检查、11新增专项tests、108实际CLI及108冻结结果一致；[公共验收](research/supernode-integration/acceptance.json)：846项tests（824通过/22可选跳过）、1998产物/24注册图、正文网页通过。物理分组/服务/恢复/费率为声明教学输入；不据此声称实测性能、完整KV服务或真实状态恢复协议，9.5及其他原工作包继续保留。

### 第 7 章：网络

- [ ] C37 跨节点训练／推理放置、分层集合通信、最忙割集与扩展效率（7.1–2）。已有[ring](src/infra_calc/topics/ring_collective.py)/[tree](src/infra_calc/topics/tree_collective.py)、Dense通信、Qwen235专家执行与物理路径子账；本轮[真实梯度两级归约](src/infra_calc/topics/hierarchical_gradient.py)连接Qwen3-8B首层gate FP32/BF16、8rank连续/交错ring及localRS→跨服务器AR→localAG，逐元素区间/贡献与发送接收NIC/出口入口/有向割集分列，1/2NIC共12固定场景。独立整数重放/资源复计20检查、12非法输入及4专项tests通过；[公共验收](research/hierarchical-gradient-integration/acceptance.json)850项tests（828通过/22可选跳过）、24实际CLI/24冻结结果一致、2022产物24图与正文网页通过。仍缺真实框架梯度分桶与全模型训练时序、TP/PP/EP跨服务器完整候选、多NIC借用后的排空等待、V4-Pro/K3跨服务器推理及完整强弱扩展。单张量完整归约不代替整个C37，声明资源下界不当实测。
- [ ] C38 RDMA 阶段时长、BDP/在途并发、主机代理与设备发起、发布与释放依赖（7.3）。[窗口复用扩展](src/infra_calc/topics/memory_concurrency.py)已补分配／活跃请求、串行服务启动间隔和三重精确上界，正文313／16.384／2.56／0.128复算，五场景及边界／同时瓶颈验证完成。[真实RPC阶段](src/infra_calc/topics/rpc_trace.py)已导入封存264次调用，复算三载荷的客户端／服务端阶段、配对差、CPU与应用字节，哈希及身份检查完成。[远程快照访问](src/infra_calc/topics/remote_state.py)补官方KV载荷、不变快照复用、直接远程／搬回本地、窗口约束、精确回本与容量门槛四场景。主机／设备发起校准、动态KV更新及完整交接生命周期继续待补。
- [ ] C39 连接/QP/状态数、共享传输规模、严格序与依赖序关键路径／队列（7.4）。[连接状态](src/infra_calc/topics/connection_states.py)已补本机有向活跃关系、按对端／隔离类共享、端点／绑定／传输容量与稀疏热点四场景；独立等价类划分及预算边界验证完成。[操作顺序](src/infra_calc/topics/operation_ordering.py)补全完成串行／必要发布依赖、共享资源阻塞及旧值响应排序／冲突重读四场景，事件取值与闭式时长独立核对完成。[完成回收](src/infra_calc/topics/completion_reclaim.py)补有限credit、周期批量消费、提交背压、缓冲／完成项容量和三个完成时刻，四场景与27组独立逐tick模拟核对完成。地址转换／异常回收、实际状态结构及规范／硬件行为校准继续待办。
- [ ] C40 incast／反馈队列、超订阅、多路径乱序缓冲、选择性重传与故障尾部（7.5）。[周期队列](src/infra_calc/topics/periodic_queue.py)已覆盖LCM／跨周期脉冲、错峰／漂移、600MB／150MB、12ms排空、兼容度及精确队列面积，五场景、独立逐tick检查与正文回填完成。[有限缓冲与显式反馈](src/infra_calc/topics/feedback_queue.py)已补初始积压、精确填满／排空、溢出丢弃与守恒，四场景覆盖反馈延迟和不排空。[报文事件](src/infra_calc/topics/packet_reorder.py)补官方激活分包、路径偏斜、按序释放、乱序保留及显式丢失单次恢复，四场景与独立前缀最大值核对完成。真实控制器、ACK／超时／有限窗口、OpenURMA校准及故障分布继续待办。
- [ ] C41 网络优化在暴露通信／训练步／完整任务中的收益及路径故障敏感性（7.6）。[就绪与尾部](src/infra_calc/topics/collective_tail.py)已复算四rank就绪偏差、交换加速、有限联合记录p50/p99/max与显式恢复四场景；独立展开记录核对分位数。完整TP/PP/EP任务依赖、逐rank提前推进及实测通信曲线校准仍待补。

### 第 8 章：单实例服务

- [ ] C42 batch 权重复用／KV 交叉点、固定与连续 batching、chunked prefill 的可复现事件模拟（8.1）。[真实同块历史](src/infra_calc/topics/chunk_history.py)已导入15封存文件、11请求176块，核对时间样本、连续历史与官方配对／backbone工作，整段守恒和配对统计独立验证；[官方batch复用](src/infra_calc/topics/batch_reuse.py)已补Qwen8矩阵、共享权重／逐请求KV、4090与H100的严格BF16/FP32 dense峰值、容量及两个交叉点五场景；容量／交叉整数边界独立验证。[逐迭代调度](src/infra_calc/topics/iteration_batching.py)已补同请求固定／连续／chunked与有限KV准入四场景，逐请求官方矩阵／输入位置守恒、补位边界、预算与时间闭式独立验证。实际重读、服务校准与图档位仍待补。
- [ ] C43 KV 分页／内部碎片／COW／分支共享、换出与重算、前缀命中收益／淘汰价值（8.2）。[页分配器](src/infra_calc/topics/kv_pages.py)已补官方Qwen144/188KiB几何、引用计数、尾页COW、安全点取消、预留／分页／共享字节，四场景及独立长度／引用／尾页边界验证完成。已补容量准入四场景：页预算取整、COW提前检查、原子拒绝、取消后无复制重试及同预算Qwen235差异，独立无界增长核对页需求。[真实块记录](src/infra_calc/topics/kv_trace.py)已导入实验8-3三个运行、21封存文件，核对池守恒、抢占保留270输出／额外调度1805位置、取消104块与延后释放，官方几何匹配。[换出与重算](src/infra_calc/topics/kv_restore.py)已补官方backbone工作、双向传输、已知下一使用窗口、容量释放byte*ns和恢复等待四场景，闭式矩阵量／时限边界核对完成。[前缀价值](src/infra_calc/topics/prefix_value.py)补官方full/suffix工作差、预期复用、整页容量与静态精确选择／密度贪心反例，四场景及独立子集枚举验证完成。[真实Agent/APC](src/infra_calc/topics/apc_trace.py)已导入实验8-4五条件60Agent请求、17封存文件，核对命中分母、官方剩余／节省工作与Agent／干扰／间隔时间，五场景及工作身份验证完成。重叠前缀树、未知复用时间与完整在线服务策略继续待补。
- [ ] C44 投机接受长度分布、验证与草稿成本、回滚／KV、在线预算和完整任务速度（8.3）。[轮次收支](src/infra_calc/topics/speculative_round.py)已补接受长度直方图、补偿／额外token、输出上限、官方目标验证／匹配串行工作与规范化KV回滚四场景，独立加权及全接受矩阵身份验证完成。[单步采样精确枚举](src/infra_calc/topics/speculative_sampling.py)已补225组分布对、拒绝正残差与错误重采样对照、零概率和全接受边界；[有限输出预算](src/infra_calc/topics/speculative_budget.py)已补准备状态、末轮截断、普通decode与多长度选择、固定策略四场景及全部小规模策略独立枚举。[官方DFlash检查点工作账](src/infra_calc/topics/dflash_work.py)已锁定配置／源码／58张量头，核对独立参数、共享目标头、非因果矩阵与特征／KV四场景。真实权重执行、多token采样器、实测成本、非平稳在线预算与完整任务仍待补。
- [ ] C45 量化 block 元数据／混合精度／GGUF 实际文件清单、卸载逐步读取、KV codec 代价（8.4）。[实际GGUF清单](src/infra_calc/topics/gguf_inventory.py)已锁定Qwen235发布者19变体72分片，逐片求和与完整性、LFS大小／身份、96／192GB声明预算和8K／32K官方KV四场景及字节边界验证；[实际GGUF头](src/infra_calc/topics/gguf_layout.py)已解析Q2_K与Q4_K_M五分片、1131官方张量，核对混合类型、码值／块尺度元数据与文件头／对齐字节守恒；固定GGML规范与结构体原件、解析器截断边界验证完成。[KV codec子账](src/infra_calc/topics/kv_codec.py)已补官方GQA／GGML q8_0/q4_0块尺度、融合／物化流量、显式转换成本及整数盈亏区间四场景；格式字节、物化差额和区间边界验证完成。[FFN卸载](src/infra_calc/topics/weight_offload.py)已补官方九层权重、净省容量／KV等价、逐forward流量、有限槽安全预取／双pass环回及decode/prefill摊销六场景；独立慢／快链路闭式与槽生命周期验证完成。[实际KV质量与驻留](src/infra_calc/topics/kv_quality.py)已导入三条件25封存文件，核对八任务重复执行的自然／固定模式、严格答案、实际KV池、scale冻结与Q-BF16控制；三场景及独立判据／窗口／几何验证完成。R1文件、权重量化组合、广泛质量、真实转换流量与卸载校准仍待补。
- [ ] C46 TTFT/TPOT/E2E/SLO goodput、质量一致条件下设备与到达率扫描（8.5）。[真实交付复算](src/infra_calc/topics/service_replay.py)已导入四条件72请求13固定文件，核对输入／源码／输出、逐请求联合计时阈值与三轮窗口加权goodput，四场景及独立事件统计／边界检查完成；真实任务质量、逐tokenSLO及设备／到达率扫描仍待补。

### 第 9 章：分布式服务

- [ ] C47 合置、PD、AF 基线资源图；阶段能力转请求/s、A100/H20 配比（9.1–2）。[PD池配比](src/infra_calc/topics/pd_pool.py)已完成有效阶段token/s转请求/s、异构整数分配、共置资源秒、网络上界及首输出／前缀／长输出六场景，回填9-2；实际设备校准、完整放置、AF基线与时变SLO仍待完成。
- [ ] C48 PD KV 每请求交接、双端缓冲／staging／格式转换；AF 每层往返、专家执行与搬权重阈值（9.2–3）。[交接账](src/infra_calc/topics/pd_af_handoff.py)已覆盖正文32层与官方Qwen8／235、每hop启动和独立接口、整消息双端缓冲及相同字节对照，五场景回填9-4；[单专家复用阈值](src/infra_calc/topics/expert_locality.py)现已精确分段覆盖全部正整数，含78／79边界及能力敏感性；格式转换、真实路由／流水、量化与NUMA路径仍待完成。
- [ ] C49 CPU/NUMA/GPU 专家复用、热门专家复制、token 迁移及 grouped GEMM/重叠代价（9.3–4）。[专家局部性](src/infra_calc/topics/expert_locality.py)已按官方Qwen MoE区分权重并集与任务数、单层非驻留CPU／搬权重GPU／常驻参考，五场景与9-5回填；32专家逐层驻留合计105.75GiB明确列出。[grouped专家tile](src/infra_calc/topics/grouped_experts.py)已复用GEMM分块账，五场景区分有效／全补齐工作、权重重读与连续／交错放置最忙rank，回填9-6。同模块已加入显式物理副本、商余数任务拆分、额外权重／KV等价和33任务padding反例，四场景回填9-6；[副本回本](src/infra_calc/topics/replica_payback.py)进一步接入逐rank资源服务、共享冷复制与严格批数／容量边界，五场景回填9-6。真实量化、NUMA、动态迁移协议、后端padding与重叠仍待完成。
- [ ] C50 HBM/DRAM/SSD/远端缓存容量／命中取回／存储字节秒、多级前缀／状态身份（9.5）。[真实正常重启](src/infra_calc/topics/cache_restart.py)已核验65份KV文件及两进程请求／调用，分开144MiB读取与141.75MiB复用、成功set与新文件，回填9-8；[缺页恢复](src/infra_calc/topics/cache_missing.py)已导入缺页0／32的连续前缀与重算，实际BF16原页／恢复页逐层差异和输出一致分列；同模块已导入显存512前缀v2对照与三路径页比较，核对前置仅1输出，排除528边界初版；[坏页预取策略](src/infra_calc/topics/cache_fault.py)已导入三策略同截断页，区分60秒未完成观察与零命中重算成功、最终坏页哈希，回填9-8；[多级驻留](src/infra_calc/topics/cache_residency.py)已完成完整GQA页同层共享并集、跨层副本、精确字节秒、峰值和超预算区间，并含Qwen8／235及容量边界场景；真实多级驻留事件、部分页、更多故障与混合状态仍待完成。
- [ ] C51 缓存亲和与排队／新鲜度、事件丢失／索引恢复、PD+AF+池组合（9.5）。[缓存路由](src/infra_calc/topics/cache_route.py)已复算官方KV、队列／取回依赖、远端等时带宽、失效两点分布及p99等号，五场景回填9-9；[原生路由回放](src/infra_calc/topics/router_trace.py)已导入9-9三策略36请求和实际worker日志，核对真实命中与官方矩阵节省，三场景回填9-9；[真实路由压力](src/infra_calc/topics/router_pressure.py)另导入9-9六组／18调用，配对核算目标节省与整组变慢，回填9-9；共享链路动态队列、预测规则、事件缺口与组合仍待完成。
- [ ] C52 TP/EP 重配置权重与状态迁移、摊销阈值、分流与恢复后的完整部署成本（9.6）。[迁移子账](src/infra_calc/topics/reconfiguration.py)已接9个官方Qwen3配置场景、逐卡权重/KV所有权、显式同卡物化/网络载荷与双缓冲峰值、条件有限寿命摊销，18项聚焦验证；[独立审查与集成](research/c52-independent-review/INTEGRATED.md)列明静止快照/单播/PP=DP=1边界。真实排空、分流、恢复重试、请求身份验证与SLO有效产出尚缺，带宽下界不能替代切换时间，原项保持未完成。

### 第 10 章：训练

- [ ] C53 参数／梯度／master／Adam 状态、ZeRO1/2/3、激活峰值／重计算／卸载与 casting（10.1）。[训练持久状态](src/infra_calc/topics/training_state.py)已按官方Qwen8／235完整参数张量完成BF16/FP32梯度、ZeRO0–3、DP展平／逐张量补齐及额外同时驻留预算六场景，回填10-1；[梯度转换放置](src/infra_calc/topics/gradient_cast.py)已迁入官方gate梯度两路径、6N转换访问、精确链路交点、两侧活跃缓冲与容量选择五场景，回填10-1；真实后端聚合／casting峰值、分块、激活重算／卸载及V4格式仍待。
- [ ] C54 任务 token／期限反推卡数，4090/A100/A800/H20 的容量与拓扑可行组合（10.1–2）。[训练期限](src/infra_calc/topics/training_deadline.py)已完成官方Qwen逐矩阵任务／尾序列、BF16/FP32 dense单设备峰值30/40/50%矩阵效率、独立算力／持久容量整数下界及日历扣除五场景；A800精度峰值缺项明确保留；H20 SXM5 96／141GB已锁定官方型号容量并进入容量下界，但精度峰值等仍缺，实际MFU、TP/PP/EP、激活峰值与拓扑仍待。
- [ ] C55 GPipe/1F1B 微批时序与峰值、pipeline bubble、不均衡与暴露通信，长序列／MoE（10.3）。[training-pipeline-schedule](src/infra_calc/topics/training_pipeline_schedule.py)已接Qwen8 PP4时序、有限缓冲、参数更新屏障和不均衡；[training-pipeline-gemm-state](src/infra_calc/topics/training_pipeline_gemm_state.py)已补253输入身份、325矩阵VJP依赖及保存/乘积重算合账。长序列/MoE扩展、实际BF16后端激活与完整运行峰值仍待，不勾选整项。
- [ ] C56 数据输入／预处理吞吐、checkpoint 大小／分片加载／持久化与恢复链路（10.4.1、3）。[逻辑重分片](src/infra_calc/topics/checkpoint_reshard.py)已完成官方gate行／展平布局交集、源与目标字节偏移、完整14byte状态／仅权重、4→8／8→4／7→5五场景与小数组字节重建，回填10章；[异步保存](src/infra_calc/topics/checkpoint_async.py)已完成官方全参数14byte载荷、取整8B对照、有限槽背压、实际capture与durable分列、故障可用点五场景；[实际保存基线](src/infra_calc/topics/checkpoint_baseline.py)已封存39原件、15次同状态运行与10份实际检查点，分列API／writer／训练／完整窗口及配对差值；[实际提交前故障](src/infra_calc/topics/checkpoint_fault.py)已导入20原件、提交缺失与实际加载拒绝、旧点恢复及40次更新回退，未完成时间保留null；[实际恢复续训](src/infra_calc/topics/checkpoint_resume.py)已核验15原件、19状态坐标覆盖、2→2/3/1布局、六rank下一步一致与Adam负对照，分开容器与逻辑／复制载荷；[训练输入供给](src/infra_calc/topics/training_input_supply.py)已补预token样本打包、21B线格式、R/P/H/C与snapshot/write及共享存储，经独立审查后接公共CLI与五场景。真实大模型输入/预处理校准、争用归因与完整恢复仍待。
- [ ] C57 故障率、checkpoint 周期 c/τ+λτ/2+λr、最优间隔和相关故障敏感性（10.4.2）。[周期与重试](src/infra_calc/topics/checkpoint_interval.py)已实现官方载荷的阻塞c、一阶分项／连续最优、独立设备与作业共同冲击、另列Poisson重试期望／数值最优，五场景含高率／零率／恢复敏感性；实际故障分布、一般相关故障、恢复再失败和异步策略仍待。
- [ ] C58 RL rollout/reward/teacher/learner 配比，长尾、抢占、WAL、状态回收与恢复（10.5）。 已有[RL周期](src/infra_calc/topics/rl_cycle.py)、[供给配比](src/infra_calc/topics/rl_supply.py)的等长Qwen cohort与声明资源率，以及[KV恢复](src/infra_calc/topics/kv_restore.py)固定权重恢复子账。仍缺显式长尾轨迹、策略版本/WAL提交点/故障恢复连接，V4-Flash Agent实际路径、异构硬件有效供给和历史草稿配比；等长服务上界不能代替真实RL闭环。
- [ ] C59 Routing Replay 元数据／带宽／版本及 token 对齐，教师 hidden cache，推训权重更新与交接（10.5）。[路由元数据](src/infra_calc/topics/routing_metadata.py)已复用官方Qwen30/235、V4 Flash/Pro和K3专家几何，分开主模型routed/shared/hash/dense层、ID编码范围、显式身份/位图/header、存储副本与供给带宽七场景；实际packing/缺失/版本对齐、教师cache容量/重投影/接口IO七场景已接入[teacher-cache](src/infra_calc/topics/teacher_cache.py)，[权重交接](src/infra_calc/topics/weight_handoff.py)已覆盖Qwen完整参数、非整除EP所有权、非专家复制、出口/接收界与阶段容量五场景；实际版本/token校验、教师质量、源重组、接收缓冲与引擎交接仍待。
- [ ] C60 1T/5T/10T Dense 和真实 MoE 的算量／MFU／日历期限／并行修正（10.6）。[名义Dense规模](src/infra_calc/topics/dense_training_scale.py)已按官方单设备BF16/FP32 dense峰值完成1T/5T/10T、固定20T或D=20N、30/40/50%效率、90/180天整数卡数／参数边界、容量与日历四场景；真实MoE训练、校准MFU、完整放置通信与保留进展仍待。

### 第 11 章：环境与成本

- [ ] C61 Agent CPU 核时、Little 定律、内存字节秒、GPU/工具等待和环境并发（11.1）。[environment-resources](src/infra_calc/topics/environment_resources.py)已接22原件、9组36进程及12轮控制器，CPU/RSS采样积分、有限窗Little恒等式、提交延迟/生命周期与失败质量分开；五场景完成，真实OS队列/整环境物理内存与生产供给仍待。
- [ ] C62 冷/暖/恢复创建、模板与快照增量、预热命中及空耗、clone 状态预算（11.2）。 [environment-lifecycle](src/infra_calc/topics/environment_lifecycle.py)已接五场景、共享/私有池容量、增量格式条件、预热等待与字节秒，并单列12次本地真实记录；云端四路径实际创建/恢复/首工具时间、物理内存与实际增量格式仍待，不标整项完成。
- [ ] C63 成组作业与资源碎片、抢占有效产出、验证尾部与 barrier、环境推测执行（11.3）。[原要求审计](research/plan-c63-c66-audit.md)确认已有成组容量/迁移子账、[真实抢占恢复](../experiments/ch11/11-04/README.md)、两批CPU验证记录及[公共环境预热](src/infra_calc/topics/environment_lifecycle.py)期待/记录复算；仍缺异构成组完成时间、抢占有效训练成本与资源存活窗口、验证资源—训练等待连接、多轮工具切换/重用下的预热边界。局部真实记录与单调用期待不代表完整任务账，保持未勾选。
- [ ] C64 订阅/API 固定快照与 usage 包含关系、缓存读写/TTL、reasoning 及成功任务成本（11.4）。[routing-cost](src/infra_calc/topics/routing_cost.py)已迁入正文假想价格、reasoning包含关系、全尝试分子、精确费用交点与质量/时限联合门槛六场景；实际usage/价目快照、TTL及重试仍待。
- [ ] C65 有限重试／回退树成功率、完整费用、CPU/GPU/环境池扩容边际收益（11.5）。[retry-paths](src/infra_calc/topics/retry_paths.py)已展开有限条件DAG，全部失败路径费用/时间/核秒/字节秒与质量/时限分母四场景；实际条件概率、真实重试轨迹和池扩容收益仍待。

### 第 12 章：端边云

- [x] C66 RAW/JPEG/输出图片字节与非对称上下载、编解码及本地/远端交叉点（12.1）。按[原要求逐项审查](research/image-streaming-integration/scope-review.md)完成声明元数据与同质量条件下的有限图片计算：[串行预算](src/infra_calc/topics/image_request_budget.py)覆盖原12.8s/0.27s、编解码/连接/压缩与本地交叉点，图12-1及791精确曲线点已生成；[分块与预览](src/infra_calc/topics/image_request_streaming.py)补同bytes/工作下整图屏障与授权独立块、分向传播、三资源争用、额外预览与完整成片分别交付。串行8场景、分块4场景均公共CLI/正文/扩写接入；独立26场景DAG/7拒绝及5037候选检查通过。[最终公共验收](research/image-streaming-integration/acceptance.json)：860项tests（838通过/22可选跳过）、8新增实际CLI/8冻结结果一致、2046产物26图及正文网页通过。块独立性和质量是声明条件，不证明真实RAW/JPEG模型可分块；真实codec执行、协议/WAN性能及相邻C67/C68不由本项推定。
- [ ] C67 语音/截图/视频、视觉编码特征 EC 与 KV 字节，搬输入/搬特征/搬状态/移动计算（12.2）。[multimodal-cache](src/infra_calc/topics/multimodal_cache.py)已覆盖官方Qwen3-VL静态图片完整DeepStack EC/KV、预处理后尺寸边界、搬特征与E/PD整数配比八场景；实际resize/视频、缓存服务与跨问题质量仍待。
- [ ] C68 连接复用／握手/RTT/拥塞窗口、带宽时延积、小请求/大文件/帧截止时间（12.3）。[原要求审计](../research/plan-c68-c69-audit.md)保留BDP与TCP/HTTP3局部实测；[单请求有限ACK](research/connection-window-integration/acceptance.json)及[连续请求共同窗口](research/connection-sequence-integration/acceptance.json)已公共接入。现[握手消息图](src/infra_calc/topics/protocol_handshake.py)与[长0RTT逐包切换](src/infra_calc/topics/protocol_early_stream.py)均公共CLI/统一复算/正文接入：17+13场景60产物，应用授权/拒绝重发、Initial/三倍预算/Handshake ACK、PN/STREAM offset/密钥同刻中途边界分列，30MB/5MB完整响应已计算。7官方RFC逐调用校验，默认布局/速率为声明值，不称实测或完整协议栈。[公共验收](research/protocol-integration/acceptance.json)：30完整候选payload一致、60实际CLI及60冻结结果通过；878tests（856通过/22跳过）、2152产物26图及正文网页通过。仍缺[HRR/Retry/PSK回退](research/protocol-integration/next-retry-scope.md)、后台票据和完整编码、一般ACK/PTO/丢失与指定实际拥塞流控、语音/截图/媒体截止及多流业务、完整图12-4，保持未勾选。
- [ ] C69 ACK 空口占用、上下行争用、双路径分流/冗余及合并等待（12.4）。[原要求审计](../research/plan-c68-c69-audit.md)确认已有[分包乱序恢复](src/infra_calc/topics/packet_reorder.py)及[双TCP音频取消/复制/共同故障](../experiments/ch12/12-06/README.md)真实记录；仍缺TCP与MAC ACK分别建模的空口频率、双向媒体期限、RAW汇合瓶颈/蜂窝费用能耗、截图版本与重试到任务结果的连接及图12-5。应用bytes不冒充物理无线计费/耗电，保持未勾选。
- [ ] C70 Queqiao 原始可用记录的同条件统计、流水阶段与时间戳误差；缺失帧分位数不得补造（12.5）。
- [ ] C71 跨地域输入/输出/状态传输与计费、放置盈亏平衡和同质量任务成本（12.6）。

### 第 13 章：协同设计

- [ ] C72 完整执行 DAG 资源下界／关键路径／面积／功率／容量，多目标候选筛选（13.1）。
- [ ] C73 OpenTallas 权重驻留后的激活扇出/扇入、总 hop、同步跨度、供给倒推及遗漏约束（13.2）。
- [ ] C74 两侧独立量化／副本／并行选择，负载／面积／quality 固定下的反例和翻转条件（13.3）。
- [ ] C75 NRE/交付/更新风险、盈亏平衡用量、整站电力/冷却/网络/利用率成本（13.4）。
- [ ] C76 留出配置、输入不确定区间、最有价值的补测与可证伪预测，跨章最终设计记录（13.5）。

## 完成审计

逐条原文审查必须确认没有因合并工作包遗漏具体算式；专题旧脚本需要迁入模块或有明确复用入口。真实模型必须用完整适配器而非参数标签缩放。需测量／质量输入的项目交付计算、输入契约及诚实的证据缺口；这不允许把实验宣称完成。所有必需计算完成、结果回填并验证前，全书目标保持进行中。


## 用户追加：生成式多模态短例（2026-09-09）

保留原C01–C76全范围，以下为追加范围，正文简练而定量条件完整。

- [ ] C77 Qwen3-Omni：官方配置/模型卡已锁定；逐段核算编码器、Thinker、Talker/code predictor/code2wav矩阵、KV、阶段hidden与首音频；不把视频理解当视频生成。[omni-audio-encoder](src/infra_calc/topics/omni_audio_encoder.py)已补有效mel分块/卷积/分段双向attention/Thinker投影六场景；[原始PCM前端](src/infra_calc/topics/omni_audio_preprocess.py)已锁固定Whisper/STFT/mel/mask和30s构造器边界，补齐max临时索引写入，经数值及独立审核后接公共CLI与四场景；现有[omni-understanding](src/infra_calc/topics/omni_understanding.py)已连接预计算媒体与Thinker。文件解码/重采样、FFT内部实现与完整请求运行时继续待补。 已完成补记：[音频生成账](src/infra_calc/topics/omni_audio.py)已有Transformer、桥接、码本循环及Omni codec计量；不能再把全部Talker/codec视为未实现。token准备/采样、多chunk、完整请求驻留与实测首音频仍待；条件供给下界不当作实测延迟。
- [ ] C78 Fish Audio S2 Pro：官方配置/模型卡/研究许可已锁定；[音频AR与codec账](src/infra_calc/topics/omni_audio.py)已接slow/fast AR、10码本、可选已tokenize纯文本prompt、RVQ/decoder与逐帧依赖，区分10次fast调用、2048采样/帧及44100Hz时钟；[波形导出账](src/infra_calc/topics/fish_wave_export.py)已接固定CLI的clone、两次code CPU复制、合并后一次codec及波形cast三场景，见[公共验收](research/fish-wave-export-integration/acceptance.json)。仍缺参考音频编码/tokenizer、采样、完整请求峰值、文件IO与实测RTF/TTFA；首码本不等于首音频。
- [ ] C79 图像生成：已固定Qwen-Image-2512与FLUX.2-klein-4B distilled的官方config、许可及版本；[图像生成账](src/infra_calc/topics/image_generation.py)已接latent/packing、DiT、CFG/NFE、text encoder、VAE矩阵/卷积、参考非矩阵/setup与阶段对象边界；[FLUX VAE细账](src/infra_calc/topics/flux_vae_decode.py)另细化decoder逐算子、49620259参数及命名张量生命周期四场景，见[独立审查](research/flux-vae-independent/REVIEW.md)，不与旧VAE矩阵重复相加。仍缺完整非矩阵、实际布局/workspace/运行峰值、完整图像IO及同协议质量/速度评价，不宣称无条件SOTA。
- [ ] C80 视频生成：[视频生成账](src/infra_calc/topics/video_generation.py)已接MiniMax-H3/Wan2.2-TI2V-5B的真实帧对齐、音视频latent、联合attention矩阵、NFE及声明regeneration两阶段五场景；另有[H3条件](src/infra_calc/topics/h3_conditioning.py)、[Wan文本编码](src/infra_calc/topics/wan_text_encoding.py)、[Wan VAE解码](src/infra_calc/topics/wan_vae_decode.py)。仍缺H3 Qwen3-VL编码器及音/视频VAE、Wan输入图像encode、其余scalar/调度/通信、完整驻留/关键路径与真实托管Context-IR/regeneration；正文2/3/5/8/12章短例仍需逐项覆盖验收，保留自定义许可边界。

DeepSeek V3经典模型补充：已接[v3-forward](src/infra_calc/topics/v3_forward.py)六场景的完整基础逻辑权重、主要算子、expanded MLA与分组路由；FP8实际格式、checkpoint索引、MTP/完整运行时继续待办，不代表C10/C11或全模型覆盖完成。

真实70B容量补充：[capacity-scan](src/infra_calc/topics/capacity_scan.py)已复用公开Llama70逐权重枚举，补8K/32K、分组尾部及逐字节容量阈值四场景；独立723索引名、五种group、GB/GiB及Qwen旧结果等价检查通过。单设备容量及BF16多卡六场景已接入，TP16明确复制完整KV头和K/V投影工作；低位多卡布局、完整通信和实际工作区仍待。

Qwen3.5经典模型补充：已接[qwen35-forward](src/infra_calc/topics/qwen35_forward.py)八场景及[语句补充](src/infra_calc/topics/qwen35_reference_steps.py)，1038基础文本张量形状、45层DeltaNet/15层完整attention/60层MoE、chunk尾块、卷积裁切、RoPE/mask/router与状态分别计量。独立36数值案例及最终10差异场景核对通过；公共CSV保留异构层repeats并验证与JSON工作守恒。属于声明BF16参考路径，视觉/MTP、已有record-past记录长度、真实后端及HBM范围保留；不代替C11/C12或C81整体验收。

- [ ] C81 多模态理解的视觉encoding完整开销：官方Qwen3-VL patch/vision Transformer/merger/DeepStack逐矩阵与非矩阵账，和语言prefill的视觉位置、KV/attention分段连接；扩展Omni/ComputerUse，预处理/编码器不能免费，端到端关键路径及驻留须核实。[vision-encoding](src/infra_calc/topics/vision_encoding.py)已接QwenVL4全部视觉矩阵/learned参数、参考非矩阵、逐图attention与整数cache命中六场景；[vl-request](src/infra_calc/topics/vl_request.py)已连接视觉→语言prefill→逐步decode，并支持混合尺寸与逐图缓存命中；[omni-vision-encoding](src/infra_calc/topics/omni_vision_encoding.py)已补Omni图像/视频打包、时间块attention、位置默认与独立DeepStack接口六场景；[omni-understanding](src/infra_calc/topics/omni_understanding.py)已连接encoder/placeholder/Thinker prefill与decode七场景；[vl-position-bridge](src/infra_calc/topics/vl_position_bridge.py)已补静态图片三轴索引/delta及直接model decode位置准备，4个请求场景与41官方CPU坐标/123decode对照；[视觉CPU预处理](src/infra_calc/topics/vision_preprocess.py)已完成固定已解码RGB单图路径、四场景与12772项独立检查，见[公共验收](research/vision-preprocess-integration/acceptance.json)。仍缺文件解码、其他设备/多图完整预处理路径、视频/Omni位置扩展、实际路由/采样及实测。

C10缓存续算补充：[v4-prefix-continuation](src/infra_calc/topics/v4_prefix_continuation.py)已支持固定源码合法的逐token已知后缀完整基础forward累计，默认6144+2048和Flash/Pro边界三场景；原多token单调用仍拒绝，因为增量源分支只写单槽。全部head、压缩/窗口/FP32状态与显式源分配计入所声明口径；恢复成本、并行chunk、完整runtime未知不由此闭合。

C79解码器细化：[flux-vae-decode](src/infra_calc/topics/flux_vae_decode.py)已接4场景、49620259解码参数、逐算子/偏置/GN affine及命名张量生命周期；独立16核心和8布局边界通过。与旧image-generation VAE矩阵一致，不重复相加；真实workspace/布局复制与完整图像流程仍依声明保留。

C13架构变体：[architecture-variants](src/infra_calc/topics/architecture_variants.py)已接4场景，官方基线与未训练深宽/KV/FFN变体分别给参数误差、逐算子、TP状态与容量/通信切换条件；独立42对齐及18请求/逐rank组合核验。默认减少KV补FFN严格等参，其他对齐以实际标志判定；MoE颗粒度、低位多卡和质量要求仍不由此完成。

C77–C80阶段进度：omni-audio五场景已接Transformer/桥接/码本循环，image-generation六场景已接DiT矩阵/packing/CFG，video-generation五场景已接core/真实帧对齐/声明再生成；均已CLI/报告/正文集成。已公开各模型的有限编码器/codec/VAE及参考非矩阵子账；完整请求准备、尚未覆盖组件、实际驻留/关键路径和测量按原C77–C80保留，不勾选完成。

C81阶段连接已接vl-request五场景：视觉/语言prefill/decode独立矩阵与语义读写、DeepStack注入、首输出与最终KV边界，固定已解码RGB单图CPU预处理已由vision-preprocess接入；仍待文件解码/其他预处理路径、实际阶段性能/其他模型。C77新增Omni codec/DAG/接口供给；C79新增完整text encoder/VAE矩阵及卷积、first-frame cache必要存活量；标量/实际全运行时和其他codec等继续待办。

C13 MoE逐卡容量补充：[qwen235-placement](src/infra_calc/topics/qwen235_placement.py)已接24场景，官方36945权重名/235093634560参数、四种八卡TP/EP/PP组织、三格式local-K打包、EP attention/KV复制及PP最差rank边界独立复核。低位为声明格式；真实通信、workspace与其余原要求仍待，不整体勾选C13。

C13 Dense低位多卡补充：[dense-quantized-placement](src/infra_calc/topics/dense_quantized_placement.py)已接三真实模型54场景，复用BF16分片并按local K重新打包/分组，TP16复制、DP min后sum、非均匀PP阈值经45组合与9边界独立审核。声明格式的逐rank容量已补；实际低位checkpoint/执行性能、完整通信与workspace仍不由此完成。

实验2-9/R22统一请求补充：[request-model-comparison](src/infra_calc/topics/request_model_comparison.py)已接原四模型S/P/G/B、首输出与G−1 decode、状态及逐步计算四场景，经105项独立数学与16项场景核对。K3 checkpoint冲突和V4顺序prefix路径保留；完整硬件时延、实际任务质量与runtime预算仍待，原实验不整体勾选。

C78外层阶段补充：[fish-wave-export](src/infra_calc/topics/fish_wave_export.py)已接3场景，官方固定CLI代码块clone/两次CPU复制/合并/一次codec/波形cast顺序，28项独立检查与4测试通过。无条件裁末列不保证terminal，输入实际帧数；不重复现有codec/AR工作。真实TTFA/RTF、IO与完整请求运行峰值仍待，C78不整体勾选。

实验3-3严格消耗补充：[strategy-record-cost](src/infra_calc/topics/strategy_record_cost.py)已接三批原记录132候选/72组，原协议严格解析和投票选择、独立DP真值、全部失败/截断消耗及客户端区间分列。18封存输入逐SHA核验；同质量成功率门槛未达到，不能据零成功数据给成功成本排名，原实验不整体勾选。

实验3-6 Dense非矩阵补充：[training-nonmatrix](src/infra_calc/topics/training_nonmatrix.py)已接5场景，Qwen8非矩阵前后向、声明AdamW、typed操作与保存/局部重算事件；原矩阵完整不变。14项FP64数值测试无跳过，独立公式计数/12组合审查，补compact梯度清零与Adam共享系数外提。V4训练、完整激活/运行时/通信仍待，不整体勾选实验3-6。

实验3-8真实点补充：[real-scaling-fit](src/infra_calc/topics/real_scaling_fit.py)已接作者官方8点提取链、6fit/2固定holdout、4坐标/网格敏感性和非负边界诊断；旧严格33行源审历史保留。公共提取迁移398检查通过，边界270检查及6浮点反例关闭。真实生命周期曲线已公共接入，见下一条；原完整实验/质量/费用范围不由单个fit勾完。

实验3-8生命周期补充：[real-scaling-lifecycle](src/infra_calc/topics/real_scaling_lifecycle.py)已接真实主law与4敏感性的N/D、调用量交叉、外推范围；146独立检查和5测试通过。plot-real-scaling生成真实点/留出与生命周期双图并绑定SHA，仍明确代理费率、有限候选和同loss非同任务质量；完整原实验范围不自动闭合。


V4训练子进度：router/专家门控/mHC split及mHC外包装前反向已独立审查并接入公共CLI，六个场景；不据此勾选完整V4训练。attention及外围投影反向继续独立推进。


V4训练子进度：共享KV稀疏attention core反向已124项独立检查及4项数值测试通过并接公共CLI/三个场景；完整attention层、量化反向、压缩器和整模型训练不据此勾选。


V4训练子进度：ratio0单attention外围五投影、RMSNorm、正/逆RoPE前反向经164独立检查和3数值测试通过并接公共CLI/三场景。core保存排除；不扩张为全部43层或压缩/indexer支路验收。


V4训练子进度：ratio128完整块compressor经170独立检查及4测试通过接CLI/三场景，逐feature softmax与跨块参数梯度明确。ratio4、尾块、online状态VJP及量化梯度仍未完成，不据此勾选整模型训练。


V4训练子进度：ratio4 fresh prefill输出/返回状态联合反向经383独立检查及4测试通过，接CLI/四场景；尾token状态梯度与首块padding明确。任意恢复初态、正start_pos在线过程及完整训练仍未完成。


C55子进度：Qwen8 PP4 GPipe/1F1B训练事件、通信/保存寿命及全梯度更新屏障经9120独立检查、5组测试通过，接公共CLI/14场景。真实matrix/nonmatrix归段守恒；部分activation reservation不等于完整峰值，长序列/MoE扩展仍保留原未完成勾选。


C81子进度：单图已解码RGB的固定CPU预处理经12772独立检查、原6测试及数值重放通过，接vision-preprocess CLI/四场景。公共5测试不含无关硬件patch；JPEG/PNG、设备/多图/完整runtime范围仍未完成。


硬件状态文案校正：H01–H07保持已验收，hardware.json旧in_progress/pending族说明与A800 Active旧注释更新；三字段反向替换可精确恢复原对象，所有数值/源记录不变。原验收hash保留历史，新旧hash与变更路径见research/hardware-status-cleanup。


C22有限逐层资源界经1725检查/7测试通过，unknown容量资格缺口已修，接25场景；完整运行时仍未完成。V4 online状态时间图经331检查/4测试通过，接四场景，量化/完整训练边界保留。四模型JSON键序两处sorted修复经6hashseed证明字节稳定且对象不变。


C55子进度：GEMM保存身份补账经972独立检查/4测试通过，接四场景；325矩阵、253新身份、gamma*z/a*u重算与SiLU工作区复用明确。原完整运行时/BF16/allocator/长序列MoE范围仍未完成。


V4训练子进度：固定选择MoE单层经2138数学/形状检查、76来源/产物检查及4测试通过，接四场景；完整主辅目标/QAT/运行峰值原范围仍未完成。

V4优化器子进度：真实参数分组与Muon/AdamW逐矩阵参考经独立审核，接四个条件场景；默认未明确分组、BF16数值、分布式实现及完整训练范围仍未完成。

C77前处理子进度：Omni PCM→mel已接公共CLI与四场景，补齐max临时索引写入；实际30秒构造器上限、FFT内部未知和encoder入口明确。原编码器/生成器全运行时范围不因此勾选完成。

F01第2.6逐原句覆盖审计拆24项，快照为8完成/14部分/2缺失（有限子项，非整章完成），见research/ch2-6-coverage-audit。基于该审计新增TP8完整KV头复制与EP8专家均分两个固定书中场景；专家粒度、质量约束实验等原缺口继续推进。

C13专家颗粒度：真实235B基线与E/F/top-k六场景经独立审后接公共CLI和第2章；router预算差、对齐误差、实际专家M/TP/EP消息与容量保留。未训练质量、真实tile利用率及完整运行时仍不推定。

C13/S09深窄浅宽tile工作经独立审后接四场景，严格分有效/矩形extra/尾补；图2-7容量曲线接SVG/PNG/PDF与数据，固定12输入，整数逐rank阈值。剩余架构示意、任务质量和实际硬件服务证据继续待补。

C14/T05封存轨迹连接：四条原Chat长度已接Qwen8逻辑prefill与显式串行返回ID策略两场景；实际model forward/采样步数未知保留，真实缓存恢复/完整执行轨迹仍未完成。

S14图2-7两部分已交：capacity-curves容量阶梯与architecture-shapes六面板形状伴图均提供SVG/PNG/PDF/数据/CLI及哈希校验。条件模型与未训练变体边界保留，此图项完成不等于C13整体完成。

C14/T08四模型硬件桥接经独立审后接公共四场景：原request保留、按precision分类、shared FP32 vector及必要容量明确；未决精度/特殊op/物理HBM/放置与实际时延继续未知，不等于实验2-9同质量选择完成。

Flash单层MTP调用账已接 `v4-mtp-forward`：四场景逐矩阵、标量/特殊操作、1575条权重记录与独立ring，复用已有attention子账；不推断实际草稿对齐、调用数、接受率、验证回滚或加速比。3377候选检查与5专项测试通过，8次实际CLI JSON/MD等值；公共验收792项测试（770通过/22跳过）、1777产物与19图通过。C10/C14仍未完整完成。

同轨迹缓存生命周期：已接 `trace-cache-lifecycle` 三场景，原device命中与条件host/remote取回分别列出；原token前缀/时间审核25检查，专项3tests与6次实际CLI等值通过。公共验收795项测试（773通过/22跳过）、1783产物与19图通过。物理页寿命、完整请求驻留曲线与实际迁移事件仍待补，C14保持未完成。

S13当前实现推进：[专家颗粒度选择候选](research/granularity-selection/REVIEW.md)已连接两变体必要容量、专家与router GEMM操作数及同一fabric条件；共同wire不导致翻转，精确计算率门槛含router成本。5专项测试通过；选择/非线性等剩余成本已用显式U变量纳入精确翻转条件（默认未知不排名），根独立闭式/选择/4输入破坏反例44检查和5专项tests通过，固定输入已校验；公共CLI、4场景与章节接入验收通过（800测试778通过/22跳过、1791产物/19图），S13有限要求complete；C13其余3条继续partial。

S01/S06配对证据准备：[已有Qwen8真实基线与最小协议](research/paired-model-quality/PROTOCOL.md)已复用8任务32次自然输出，严格评分28正确且错误集中同题，接原token长度到声明冷请求资源账；2专项tests通过。[第二模型实验包](research/paired-model-quality/prepared-run/manifest.json)已准备，8原任务重新生成一致且原run/probe字节不变；本机默认环境缺匹配vLLM/32B权重，第二模型尚未执行，共同质量/SLO/成本比较未完成，不据单模型记录勾选S01/S06；S11仍需训练或明确推理消融证据。

图2-8候选：[原记录六面板](research/chat-agent-figure/REVIEW.md)已生成PNG/SVG/PDF/data，显示4原Chat与4Agent轮次、marker边界/未观测首轮、工具毫秒与声明KV。274项原始字段/哈希独立检查与2数据tests通过，Chat来源已补、图例完善并重新看图；manifest已生成，公共verify完整集合14隔离检查、CLI/图注册/正文接入已验收，三图及data与审核候选byte一致；图2-8有限交付完成，C14其他缺口仍partial。


## 用户追加：Qwen3.6-35B-A3B（2026-09-09）

- [ ] C82 将官方Qwen3.6-35B-A3B加入第二章Qwen3-8B → 中等规模MoE → DeepSeek V4 Flash的递进算例，以及后续容量/请求/放置计算。固定config、模型卡、架构源码与checkpoint形状；分别核全部权重、路由/共享专家、混合attention逐矩阵与非矩阵账、KV/递推/卷积状态；提供CLI、固定场景、独立验证与正文。已固定70份官方原件与26分片头，1045张量/693基础文本形状核对通过；[来源审查](research/qwen36-inputs/REVIEW.md)、[共享公式与源码分支审查](research/qwen36-compute/REVIEW.md)。[基础文本CLI](src/infra_calc/topics/qwen36_forward.py)与[必要容量CLI](src/infra_calc/topics/qwen36_capacity.py)已接6个forward/7个容量场景，独立容量边界和6专项tests通过；[公共接入验收](research/qwen36-integration/acceptance.json)完成：827tests（805通过/22跳过），32实际CLI及32冻结产物核对，1865产物/22图和正文网页同步通过。第二章2.5.1主文已直接展开专家矩阵与三种资源口径，实验2-6已改为Qwen3.6先行、再推V4；6项专项测试与正文链接验证复跑通过。后续仍缺视觉/MTP执行、多卡放置及完整请求/硬件供给连接，保持未勾选。视觉/MTP与基础文本范围分别验收；模型名A3B不直接作为FLOPs或常驻内存输入。 后续增长KV已接[growing-remote-kv](src/infra_calc/topics/growing_remote_kv.py)：仅10层全历史KV远端化、30层固定递推/卷积留本地，副本追加/前缀尾部和容量边界分列，不代替完整请求runtime。
