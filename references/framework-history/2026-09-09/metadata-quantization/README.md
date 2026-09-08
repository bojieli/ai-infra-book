# M²XFP：格式、数值评估与真实执行

围绕当前 4.2.5→5.3→8.4，选读 M²XFP arXiv v1 的物理页 2–13，共十二页，实际查看页 8–13 的六张页面。[正文范围](../../../proceedings/ASPLOS/2026/m2xfp-reading.json)与[实现范围](reading.json)分别记录。正文原件带会议 DOI，仍按 2026-01-27 的公开 v1 引用；没有读取最终出版全文或第 14–17 页参考文献。

本批十九份原始响应均成功。十一份说明／脚本／代码全文已读；vLLM v0.12.0 文件只读 1–406 行，当前 online 文件只读 1–140 行。其余为四份身份／路径响应、NVIDIA 四节与发布日期字段、PyTorch 一个 API 页面范围；另复用此前归档的 v0.12.0 发布身份。详细范围不由文件下载量代替。没有执行下载代码、模型、GPU、仿真器或综合工具。

## 格式的代价与工作发生的时机

论文 §5.2 为每 32 个值保存 128 bit 数据、8 bit scale、8 bit 元数据，平均为 4.5 bit/value；不是纯四位存储。§6.1 使用 group 32、subgroup 8。静态权重采用三种组指数偏移和四种子组尺度的搜索，动态激活则量化后选取子组最大值，并保留额外两位。前者离线优化，后者需要在线编码与消费。

专用实现包含 top-1 解码、扩展 PE 和量化单元。性能评估采用修改的 DNNWeaver 周期模拟，Verilog 用 28 nm／500 MHz 综合，缓存通过 CACTI 估计。质量匹配时，基线需要把部分张量退回八位；论文速度并非相同 W4A4 算子在现有 GPU 上的直接比较。0.26% 的面积数字只涉及所列解码／量化单元；PE tile 自身又比 MXFP4 基线增大约 4%，不能把前者当作总架构开销。

质量实验使用 Llama、Mistral、OPT、Falcon 以及 R1-Distill-Qwen 1.5B／7B。它们是历史评估对象，不是完整 DeepSeek-R1、V4 或 K3；推理任务的损失也不由常识问答平均分代表。§6.4 的 KV 延伸属于讨论，没有给出相应 KV 实验，不能接成现成缓存功能。论文的“损失减少百分比”与准确率百分点增益分开。

## 公开工件与论文路径

作者仓库固定提交 `2ed16eb6c456ee58ceea9f8c0d7dcf258de7e1f4`，时间为 2026-01-29。[README](author-README.md)明确称其为 pseudo quantization；建议 vLLM 0.7.0，而 [pyproject](author-pyproject.toml)对 vLLM 没有固定版本。该环境不是当前框架支持保证。

[量化函数](author-quant_func.py)先在浮点张量上计算并选择候选，再转回原 dtype；[普通 Linear](author-linear.py)及 [vLLM 方法](author-quant_method.py)随后做普通 `x_q @ weight.T`。vLLM 方法继承未量化权重方法，这条读取路径没有保存论文的三路打包格式，也没有调用论文扩展 PE。方法注册只处理 `LinearBase`，并不证明支持融合 MoE、KV 或任意最新模型。

[Llama 脚本](author-llama3_run.sh)配置 `mxes` 权重、`mxem` 激活；[reasoning 脚本](author-reasoning.sh)默认 `mxfp`，不能直接当成 M²XFP 结果复现命令。评估 [main](author-main_vllm.py)和 [patch](author-patch.py)处理 LightEval／vLLM 入口、生成与结果；没有运行整条脚本链或复现任何质量分数。

论文指定量化后并列最大值取最低下标；公开函数使用 `torch.topk`，没有额外固定下标的处理。[PyTorch 2.14 API](https://docs.pytorch.org/docs/2.14/generated/torch.topk.html)明确不保证并列值下标稳定。这只能说明源码不足以建立所述 tie 规则，不能未经执行声称每次都选错。独立八值反例显示，把额外精度给不同位置会改变误差；若解码不存索引，编码与解码还必须对同一位置达成一致。

## 与框架演进对照

[NVIDIA 文章](https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/)发布于 2025-06-24，当前快照还标有 2026-01-08 修改时间。所读四节解释 E2M1、每 16 值 E4M3 scale 和全局 FP32 scale；生态段写 vLLM 早期支持、SGLang 后续支持，作为文章版本中的叙述保留，不能据此确定特性第一次可用的日期。质量、速度曲线与相关链接文章未采用。

vLLM v0.12.0 发布于 2025-12-03 UTC。[所读配置与分配路径](vllm-012-mxfp4.py)对普通 Linear 使用未量化方法，对 Attention 不提供该方法，对 MoE 分配打包权重和组 scale，并按平台、依赖和选项选择 FlashInfer、Triton 或 Marlin。源码还注明其他量化入口有不同支持，不能扩大为“整个 vLLM 当时都没有 MXFP4 Linear”。

当前对照固定于 `537af2c3a4ba7462ddc9bc94ec7a4ea496da6d2e`（2026-09-07）。[在线量化指南](vllm-online-guide.md)将权重加载时转换与每次激活处理分开，允许按 Dense／MoE、层和激活格式配置；[`Mxfp4OnlineLinearMethod`](vllm-current-online-mxfp4.py)会检查 K 维整除 32，转换并替换权重／scale，然后交给选择的 kernel。指南明确激活可能保留 BF16，不能由选项名推出所有后端都采用 FP4 运算。这是两个固定时点的对照，没有审计完整 kernel 选择链或断定首次合并时间。

## 不进入正文的争议与边界

公开 v1 页 8、10 的文本层含重复及失真的旧段落，已与页面图核对，以可见图文理解编码与右移；不以重复文本作为另一套算法。页 13 按所印公式声称两种尺度规则对任意最大值等价，但 `amax=7` 已使其指数分别为 0 与 1；独立计算保留这个反例，不继承普遍等价结论。将 round-to-nearest 本身称为额外“不确定性”也不作为本书数值规则。

引言将 MXFP4 原生支持泛化到 MI300／Maia 100，没有在本轮核实相应指令，故不作为这些硬件的规格依据。405B BF16 纯权重约 810 GB，不能由它直接推出“纯权重需要数 TB”；其他状态应另列。

书中只接入[既有算子案例](../../../../case-studies/kernel-orchestration-and-quantization.md)：同一 Qwen3 权重的真实格式字节、静态与动态工作、打包与解压生存期。数字见[独立算例](../../../../research/2026-infra-survey/metadata-quantization-arithmetic.json)，沿用实验 4-2／5-4 与图 4-3，不增加章节、实验或配图编号。
