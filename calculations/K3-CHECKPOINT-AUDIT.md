# Kimi K3 checkpoint 与配置差异审查

固定官方仓库 `moonshotai/Kimi-K3` revision `f831ab66814297da540d832a5235f8e904f29d06`。输入为[官方配置](https://huggingface.co/moonshotai/Kimi-K3/blob/f831ab66814297da540d832a5235f8e904f29d06/config.json)、[官方参考代码](https://huggingface.co/moonshotai/Kimi-K3/blob/f831ab66814297da540d832a5235f8e904f29d06/modeling_kimi_linear.py)及[官方索引](https://huggingface.co/moonshotai/Kimi-K3/blob/f831ab66814297da540d832a5235f8e904f29d06/model.safetensors.index.json)。原件与每个 HTTP Range 元数据头的 SHA256 保存于 [sources.lock.json](configs/sources.lock.json)。

## 已核对的存储

96 个分片、497,220 个张量；逐项检查索引归属、key 唯一性、shape × dtype 字节、偏移连续性及官方 total_size。只下载索引与元数据头，未读取权重载荷值。实现见 [k3_checkpoint.py](src/infra_calc/topics/k3_checkpoint.py)。

| 部分 | checkpoint 张量载荷 bytes |
| --- | ---: |
| 文本参数，不含量化 scale | 1,474,879,955,968 |
| 文本量化 scale | 85,085,650,944 |
| 文本合计 | 1,559,965,606,912 |
| 视觉塔 | 802,428,928 |
| 多模态投影器 | 92,289,024 |
| 全索引合计 | 1,560,860,324,864 |

92 层 × 896 routed 专家 × 3 矩阵 ×（packed 权重与 scale）共 494,592 个 U8 张量。权重的输出维保持不变，输入维压成二分之一；scale 输入维为原始输入维的 1/32，与 config 的 MXFP4/group-32 相符。每逻辑专家参数含 scale 的 checkpoint 载荷为 17/32 bytes。其余文本参数为 BF16 或 FP32；例如短卷积权重、输出归一化和衰减向量包含 FP32。U8 是存储容器，不是 INT8 计算声明；MXFP4 权重也不证明所选后端使用原生 FP4 Tensor 指令。

## 不能忽略的形状差异

全部 69 个 KDA 层的 `self_attn.A_log` 在官方 checkpoint 中是 `[128]`，但同 revision 的 config 为 `num_heads=96`，参考代码也用 `self.num_heads` 构造它。相邻 `b_proj.weight` 为 `[96,7168]`，Q/K/V 投影宽度为 `96×128=12288`；不能通过把整个模型改成 128 个头来消除这一差异。

| 口径 | 文本逻辑参数 |
| --- | ---: |
| config／参考代码推导 | 2,779,484,476,000 |
| checkpoint 元数据枚举（排除 scale，解开 packed 计数） | 2,779,484,478,208 |
| 差值 | 2,208 = 69 × (128 − 96) |

所有非专家文本张量逐名生成预期 shape；所有 packed 专家和 scale 按层号／专家号／矩阵类型核对。除上述 A_log 外，其余文本形状与当前枚举一致。报告同时保留 `checkpoint_index_validation=true` 和 `config_checkpoint_shape_match=false`：文件元数据自洽不等于模型加载兼容。未修改官方 config，未擅自裁剪 A_log，也没有通过运行模型验证兼容。

`k3-forward` 仍是明确采用 config／参考代码的数学计算。实际 checkpoint 载荷单列；运行时转换、是否存在加载适配、真实计算精度、完整显存及 HBM 仍待证据。状态容量中的两字节短卷积缓存是教学场景，不因权重 FP32 就自动推断缓存也是 FP32。

## 复现

```bash
python3 calculations/calc.py verify-sources
python3 calculations/calc.py k3-forward --tokens 1 --history 8192 --format md
python3 calculations/calc.py reproduce
python3 calculations/calc.py verify-results
```

生成结果的 `checkpoint` 保留全部 69 个冲突张量名称、配置形状、checkpoint 形状和参数差值。`fetch --model kimi-k3` 使用锁定的 HTTP Range 重取元数据；服务器不遵守范围请求时拒绝继续读取整个分片。
