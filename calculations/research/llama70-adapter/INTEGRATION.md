公开70B代表：DeepSeek-R1-Distill-Llama-70B适配器交付

2026-09-09。仅本research目录新增模块、测试、6份输入锁引用与4组场景结果，未改共享src/config/scenarios，未下载权重。选型保持DeepSeek原发布者名称；原gated Llama3.1-70B记录继续独立保留。

集成步骤：

1. 将 `llama70.py` 放到 `src/infra_calc/models/llama70.py`。模块仅复用schema及Qwen算子代数助手，不调用Qwen模型验证/权重入口；显式删除q_norm/k_norm，允许Llama3 scaledRoPE。
2. 把 `sources-to-append.json` 中唯一固定Transformers提交的 `modeling_rope_utils.py` 来源加入公共锁。其他5个原发布者/架构输入已由主线集成；不要再次追加旧research路径的同一模型输入。`calculate`会要求RoPE源码在该模型provenance中并逐原件验SHA。
3. 在 `models/__init__.py` 的forward分派为 `model_type=llama` 且model恰为 `deepseek-r1-distill-llama-70b` 调用 `llama70.calculate`。像Dense一样拒绝routing/counts；其他Llama变体不能静默落入此适配器。
4. `scenarios.json`给prefill8192、decode(history8192)、batch8 decode(history32768)、prefill512/all-head四例；按现CLI的forward接口接入。建议先复现前两例，再按书稿需要追加其余敏感性场景。
5. 测试可将 `import llama70` 改为 `from infra_calc.models import llama70` 接入公共测试。当前独立测试直接使用原固定输入，以index名称和独立闭式公式核验，不依赖GPU/PyTorch。

本地验证命令：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src:calculations/research/llama70-adapter python3 -m unittest discover -s calculations/research/llama70-adapter -p test_llama70.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=calculations/src:calculations/research/llama70-adapter python3 calculations/research/llama70-adapter/run_examples.py
```

计算边界与已覆盖工作：

- 80层，H8192/F28672，Q64/KV8，head128，vocab128256。723个展开权重名称与官方index完全一致；配置形状推导70,553,706,496参数。index名称匹配不证明实际张量shape/dtype，BF16是逻辑格式预算。
- 每层Q/K/V/O及gate/up/down全矩阵、因果QK/PV、两次RMSNorm、RoPE、scale/mask/softmax、SiLU门控、两次残差，末RMS与可选输出头均计入。无Q/K Norm；全模型RMS执行161次。
- 默认源码 `position_ids=cache_position.unsqueeze(0)`，位置表第一维是1；批内等长连续位置共享表，而非按batch重复。显式不同请求position_ids不在当前接口。每forward仅建一次表，80层复用；源中sin/cos后的乘1没有优化掉。cast在FP32已同类型时不伪计转换。
- scaledRoPE初始化独立列出，64个inverse frequencies、772普通算术及pow/比较/选择等特殊工作；torch.where两侧全向量表达式照源计数。`original_inv_freq`别名不重复记驻留，256字节buffer单列。初始化不混入每token/每层预算。
- 权重操作数、激活操作数读写、矩形score物化与KV追加/驻留/历史/逻辑Q头载荷均分列。FMA=2、因果有效矩阵工作与矩形工作分开；默认KV每请求每token327680字节（320KiB）。
- 采用现项目逻辑算子载荷约定：不是literal eager trace，也不是实测HBM。行内FP32临时量在片上，视图/GQA repeat不强制物化；采样、tokenizer、分配器、kernel launch、后端workspace、旧cache的torch.cat整段复制均不计。不能据此宣称完整token延迟。

默认2-byte权重/KV，1请求、last-head结果：

| 场景 | 矩阵FLOPs | 普通scalar FLOPs | KV驻留后字节 |
| --- | ---: | ---: | ---: |
| prefill8192 | 1,209,475,629,318,144 | 834,477,498,368 | 2,684,354,560 |
| decode历史8192，追加1token | 160,480,886,784 | 185,761,249 | 2,684,682,240 |

可入书短例：公开的DeepSeek-R1-Distill-Llama-70B具有80层、64个Q头与8个KV头。按官方配置推导70.554B参数，BF16逻辑权重约141.107GB；每请求每token的BF16 KV为320KiB。单请求8K prefill约需1.2095×10^15矩阵FLOPs，已有8K历史后的一次decode约需1.6048×10^11矩阵FLOPs。标量、特殊函数与初始化另计，不能将这些理论工作量直接当成执行时间。

真实验证：6个测试全部通过，包括723名index对齐、参数闭式公式、3组prefill/decode矩阵公式、全scalar闭式式、KV守恒、初始化分段和batch共享表、类型/上下文拒绝、6原件SHA。各场景结果带sources/input_hashes以及适配器/Qwen助手/schema的implementation_hashes；不把源码哈希当成执行测量。
