# training-deadline — qwen3-235b-a22b

输入：`{"deadline_days": 30, "devices": ["rtx4090", "rtx5090", "a100-80gb-sxm", "a800-40gb-active", "h20-sxm5-96gb", "h20-sxm5-141gb", "h100-sxm", "b200-sxm"], "efficiencies": ["3/10", "2/5", "1/2"], "gradient_bytes": 2, "model": "qwen3-235b-a22b", "sequence_tokens": 8192, "task_tokens": 100000000000, "unavailable_seconds": 0}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| parameters | 235,093,634,560 |
| full_sequences | 12,207,031 |
| tail_sequence_tokens | 2,048 |
| full_sequence_matrix_flops | 1,370,192,546,365,440 |
| tail_sequence_matrix_flops | 284,411,459,272,704 |
| task_training_matrix_flops | 16,725,983,173,863,322,681,344 |
| matrix_flops_per_task_token_exact | `"8166983971612950528/48828125"` |
| required_tokens_per_available_second_exact | `"3125000/81"` |
| persistent_state_bytes | 3,761,498,152,960 |
| available_training_seconds | 2,592,000 |
| usable_hardware_profiles | 5 |
| missing_hardware_profiles | `["a800-40gb-active", "h20-sxm5-96gb", "h20-sxm5-141gb"]` |

效率分母严格BF16输入／FP32累加／tensor／dense，每张设备；并非已校准MFU。

| 型号 | 矩阵效率 | 算力张数下界 | 持久容量张数下界 | 两者max | 条件式训练秒 |
| --- | --- | ---: | ---: | ---: | --- |
| rtx4090 | 3/10 | 131 | 157 | 157 | 1361163995268825088/633212890625 |
| rtx4090 | 2/5 | 98 | 157 | 157 | 1020872996451618816/633212890625 |
| rtx4090 | 1/2 | 79 | 157 | 157 | 4083491985806475264/3166064453125 |
| rtx5090 | 3/10 | 103 | 118 | 118 | 2722327990537650176/1207080078125 |
| rtx5090 | 2/5 | 78 | 118 | 118 | 2041745992903237632/1207080078125 |
| rtx5090 | 1/2 | 62 | 118 | 118 | 8166983971612950528/6035400390625 |
| a100-80gb-sxm | 3/10 | 69 | 48 | 69 | 340290998817206272/131396484375 |
| a100-80gb-sxm | 2/5 | 52 | 48 | 52 | 21268187426075392/8251953125 |
| a100-80gb-sxm | 1/2 | 42 | 48 | 48 | 21268187426075392/9521484375 |
| h100-sxm | 3/10 | 22 | 48 | 48 | 170145499408603136/144931640625 |
| h100-sxm | 2/5 | 17 | 48 | 48 | 42536374852150784/48310546875 |
| h100-sxm | 1/2 | 14 | 48 | 48 | 170145499408603136/241552734375 |
| b200-sxm | 3/10 | 10 | 21 | 21 | 1361163995268825088/1153564453125 |
| b200-sxm | 2/5 | 8 | 21 | 21 | 340290998817206272/384521484375 |
| b200-sxm | 1/2 | 6 | 21 | 21 | 1361163995268825088/1922607421875 |

| 型号 | 可选状态 | 持久容量张数下界 | 缺项原因 |
| --- | --- | ---: | --- |
| rtx4090 | available | 157 | 已核对精度与单设备范围 |
| rtx5090 | available | 118 | 已核对精度与单设备范围 |
| a100-80gb-sxm | available | 48 | 已核对精度与单设备范围 |
| a800-40gb-active | unavailable | 95 | No verified peak for a800-40gb-active: BF16/FP32/tensor/dense. Do not substitute another precision or product. |
| h20-sxm5-96gb | unavailable | 40 | No verified peak for h20-sxm5-96gb: BF16/FP32/tensor/dense. Do not substitute another precision or product. |
| h20-sxm5-141gb | unavailable | 27 | No verified peak for h20-sxm5-141gb: BF16/FP32/tensor/dense. Do not substitute another precision or product. |
| h100-sxm | available | 48 | 已核对精度与单设备范围 |
| b200-sxm | available | 21 | 已核对精度与单设备范围 |

计量条件：

- 复用官方Qwen完整线性及有效因果QK/PV前后向矩阵账，序列互相独立、输出头覆盖全部输入行。task_tokens为实际参与这些矩阵的有效位置，不额外推断padding/文本token/标签覆盖；尾序列单独计算，不用固定长序列每token工作乘剩余token。
- 效率为矩阵子账定义的BF16/FP32 dense峰值比例，30/40/50%为教学敏感性，不直接借用其它FLOPs口径的公开MFU。若效率已含通信、重计算与气泡耗时，不再重复加时间；本处未证实任何拓扑能达到输入效率。
- 设备峰值严格选择BF16输入、FP32累加、tensor、dense及single_device；不以structured sparsity、TF32、FP8或整机值替代缺项。不可用型号保留原因和可得容量下界，不猜测参数。
- 时间下界为矩阵FLOPs/(有效训练秒×峰值×效率)向上取整。容量下界为完整参数/梯度/master/Adam持久字节除官方标称GB（十进制），假设理想任意分片；二者取max仍只是必要下界，不是已证明可部署的卡数。
- MoE矩阵按实际top-k直方图计算，持久容量包含全部专家；未包含激活、临时聚合、allocator、TP/PP/EP可除性、通信拓扑和每rank不均衡。平均状态字节不是最忙rank峰值。
- unavailable_seconds为明确排除的日历时间预算，先从期限扣除，再算稳态矩阵效率；不能把相同保存/故障/数据停顿同时扣时间又包含进效率。输出条件式时间不代表实际训练交付或质量达标。

固定来源：

- [configs/models/qwen3-235b-a22b/config.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/config.json)，SHA256 `0ecd5d6fe6f2db6739e4e36ab06b88ebe7bd013ef31b9583f43796059a2b23a4`。
- [sources/qwen3-235b-a22b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-235B-A22B/resolve/8efa61729e24bd65b1d152b5ab5409052aa80e65/model.safetensors.index.json)，SHA256 `53dd34fac4a29fc7ee58fa9d92c7892ea6884431c3bd3d0dc93def7bbd0b8b78`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/hardware/nvidia-a100-page.html](https://www.nvidia.com/en-us/data-center/a100/)，SHA256 `4f9e4119f72f14db039bf46b25e123a7786b73d8bbff9f2e7243dfaaacb5e8c1`。
- [sources/hardware/nvidia-h100-page.html](https://www.nvidia.com/en-us/data-center/h100/)，SHA256 `8fe697dfa96dceeeed6e7a16517294e15d9100cc0e9f1e6e5edbce78699b4681`。
- [sources/hardware/nvidia-hgx-page.html](https://www.nvidia.com/en-us/data-center/hgx/)，SHA256 `37ed56ca6dbda836f4dd0aaabe4e7f4e898550438b2888db688caeb5a0ed65d7`。
- [sources/hardware/nvidia-hgx-components.html](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html)，SHA256 `8db5c1cb160cfb3935d36324a112155d827a9b2e32768e59540ebd56f40840ec`。
- [sources/hardware/nvidia-rtx-blackwell-whitepaper.pdf](https://images.nvidia.com/aem-dam/Solutions/geforce/blackwell/nvidia-rtx-blackwell-gpu-architecture.pdf)，SHA256 `906ff2a409d7a7e4cbc56f5d3a179d574120d19aaba99520670e1a0c064595fa`。
- [../references/files/specs/nvidia-a100.pdf](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf)，SHA256 `3a800ad7668ec37037fa5870a8e3bb681b75f19668b3d11492ab9b0da0d58815`。
- [../references/files/specs/nvidia-h100.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/705n6ur546g0uk43w0117r17n8042d73.pdf)，SHA256 `3641614979809a027a8aabdc2e77639efb8fcd0f8dc7873a22ba2125489f5a27`。
- [sources/hardware/nvidia-ptx-isa-9-3.html](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html)，SHA256 `940cc68f858cefdf82425b47ee3bac3afde447c8a85b95f43d7d6fb1f46b4413`。
- [sources/hardware/nvidia-a800-active-page.html](https://www.nvidia.com/en-us/products/workstations/a800/)，SHA256 `73da9cce681c8eeadd7ffa1325480495738ead5fa41cbc69c815e00a0cd84814`。
- [../references/files/specs/nvidia-blackwell-brief.pdf](https://dam-cdn.nvd.orangelogic.com/AssetLink/gl2l4l4812s5fw0p614s6i8bv6mi3vx5.pdf)，SHA256 `df58a797c6bc4236b1877b634fe31ff8da4c82fff289605adfb5aaca424aec69`。
- [sources/hardware/nvidia-a800-active-specs.pdf](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-a800-40gb-active-datasheet.pdf)，SHA256 `9e415e45f6ad7f43003f5a42278e58b256f1856d74b17be2614da1b607404836`。
- [sources/hardware/nvidia-h20-vgpu-release7.html](https://docs.nvidia.com/ai-enterprise/release-7/latest/infra-software/vgpu/reference/hopper.html)，SHA256 `7dcb1f989bc74d7c6a3d94f52b18233308684c03009d6027910e344c2660e830`。
- [research/hardware-nvidia-closure/rtx4090.html](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/)，SHA256 `2b315d1402135bfe273c3fbde57aa31ca482522ee8928b92af96cab8088906f8`。
- [research/hardware-nvidia-closure/rtx5090.html](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/)，SHA256 `33715ee8c890c82dda0615a28b9bf2d6879965b7a85ec6ae7e3e4c4497835df7`。
- [research/hardware-nvidia-h01-round2/b200-pcf.pdf](https://images.nvidia.com/aem-dam/Solutions/documents/HGX-B200-PCF-Summary.pdf)，SHA256 `e689cb9a859cb52267fd2896837830d81ce606dad036e2b5f4324f2b60842084`。
- [research/h05-next-review/cuda-programming-guide-12.8.1.html](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-c-programming-guide/index.html)，SHA256 `cdc49d93372b4e03e94d56f24345373f82ad76b8663c745073463263009637ce`。
- [research/blackwell-bf16-independent/mma.py](https://raw.githubusercontent.com/NVIDIA/cutlass/147295a3d4b75f3aeff247c25b8927cea9a7006a/python/CuTeDSL/cutlass/cute/nvgpu/tcgen05/mma.py)，SHA256 `abb9b3a8d2b5329677999b00a45c6c6e6ab763fc748cfbeeaa333de0df881baa`。
