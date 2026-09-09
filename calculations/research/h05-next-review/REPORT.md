H05 下一轮有限来源核验（2026-09-09）

本轮闭合 H100 NVL 的产品 Base/Boost，以及 H100 SXM/PCIe80GB 四条 FP32/FP64 scalar FMA 的类型与理论峰值映射。独立补丁未改共享配置；H05仍不能整项关闭。

新查到并下载的 [H100 NVL 产品简报 PB-11773-001_v01](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/h100/PB-11773-001_v01.pdf)（2024-03，Table1印刷页3/物理页7）明确 P1010 SKU210 的Base1080MHz、Boost1785MHz。该表已渲染目视核对。补丁新增设备clock及9条峰值的产品时钟来源，状态明确为 `exact_product_boost_clock`；**没有证据表明1785MHz就是每种Tensor峰值的实际运行域**，该未知仍显式保留。

同一简报明确400W最大/默认板功耗需电缆配置为450W或600W模式；300W电缆模式下最大/默认为310W。补丁为已有400W补充此条件，不改变功率数值，不把电缆供电额定值当作GPU功耗。Table2给3938GB/s，而现有产品网页为舍入3.9TB/s；本轮保留当前内存值，记录同SKU精确简报值可作后续细化，未混入时钟修正。

四条scalar映射采用 [CUDA12.8.1官方指令吞吐表](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html#arithmetic-instructions)：CC9.0的FP32/FP64 multiply-add分别128/64结果/(SM·cycle)。表头与colspan已核，不能只看扁平文本列顺序。结合H100白皮书Table3的SKU SM数和明确FP32/FP64时钟域，结果如下：

| SKU | scalar类型 | 算式（结果为TFLOPS） | 产品表舍入值 |
| --- | --- | --- | --- |
| H100 SXM | FP32 | 132×128×1980e6×2/1e12 = 66.90816 | 66.9 |
| H100 SXM | FP64 | 132×64×1980e6×2/1e12 = 33.45408 | 33.5 |
| H100 PCIe80 | FP32 | 114×128×1755e6×2/1e12 = 51.21792 | 51.2 |
| H100 PCIe80 | FP64 | 114×64×1755e6×2/1e12 = 25.60896 | 25.6 |

[PTX9.3 fma说明](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html#floating-point-instructions-fma)给出同类型addend/destination及舍入语义。这里闭合的是scalar FMA输入/加数/结果精度与理论吞吐的关联；融合中间计算不应被误称为固定FP32/FP64位宽的内部累加器。证明链多于“PTX允许这种类型”：官方native指令吞吐和精确SKU时钟/SM均参与重建。但这仍不是运行时吞吐实验，不改变产品表的舍入值。

仍不可关闭：NVL逐精度时钟；NVL FP16/FP8在产品峰值下的累加选项；NVL其余6条Tensor及1条FP32的完整产品rate/指令映射；H100 SXM/PCIe TF32/INT8/FP64 Tensor完整映射；FP16/BF16 non-Tensor的产品时钟域。该组问题采用有限检索停止点，见 `search-log.json`，不声称官方从未披露、不把问题无限延期、不通过匹配数值反推时钟。上轮20条显式累加器证据保持已闭合。

可合并文件：

- `proposed-sources.patch.json`：先合2条新官方原件锁（含末记录guard）。
- `proposed-hardware.patch.json`：30条操作，3个完整设备guard；补产品clock、9条clock证据、明确功率条件及4条完整supporting_evidence链。
- `sources.lock.json`：3条既有原件与2条新原件的URL/版本/SHA/bytes。
- `field-audit.json`：47条峰值逐条状态、当前输入SHA及可关/不可关列表。
- `vector-rate-reconstruction.json`、`tests.json`：四个公式及实际验证。

实际验证：按RFC6902顺序应用两个补丁，guards通过；全部151设备通过validate_device；所有峰值键和数值不变；5个来源SHA与字节数通过；四条公式舍入吻合产品表。未跑全量suite。原始PDF/HTML与派生文本/PNG严格区分，派生件不替代原件证据。
