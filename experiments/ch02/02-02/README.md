# 实验 2-2：Qwen3-8B 的逐层计算

对应正文 2.2 的核心练习。读取固定官方配置，逐算子输出尺寸、FLOPs、常驻字节与访问字节，代入四个场景，并把**容量、读取、新增写入**三项各自复算——不能只给一项“显存需求”。

## 独立运行

```bash
python3 run.py    # 写出 results/qwen3-8b.json 与 .md
```

只需 Python 3.8+ 标准库。数值取自本书统一计算项目已复算的逐算子账（官方 Qwen3-8B config、固定 revision，已通过官方权重索引与守恒检查）：`calculations/results/qwen3-8b-{prefill-8192,decode-b1-s8192,decode-b64-s8192,prefix-6144-plus-2048}.json`。本实验不重算这些数字，只做本题的分组、对照与判断。

## 模型形状

36 层、hidden 4096、intermediate 12288、32 个 Q 头／8 个 KV 头（GQA）、head_dim 128、词表 151,936，参数 8,190,735,360。

## 结果

| 场景 | 矩阵 TFLOPs | 常驻权重 | 结束时 KV | 权重读取 | 历史读取 | 新写 KV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8192-token prefill | 133.59 | 15.256 GiB | 1.125 GiB | 14.160 GiB | 1.125 GiB | 1.125 GiB |
| decode batch=1，历史 8192 | 0.0200 | 15.256 GiB | 1.125 GiB | 14.097 GiB | 1.125 GiB | 0.00014 GiB |
| decode batch=64，历史 8192 | 1.278 | 15.256 GiB | **72.009 GiB** | 14.098 GiB | **72.009 GiB** | 0.0088 GiB |
| 命中 6144 前缀，补 2048 | 37.11 | 15.256 GiB | 1.125 GiB | 14.113 GiB | 1.125 GiB | 0.281 GiB |

四条判断：

1. **三项不能合成一项**。batch=64 decode 的常驻权重仍是 15.3 GiB，KV 却涨到 72.0 GiB——容量项由 KV 主导；同一步的矩阵工作只有 1.28 TFLOPs，是 prefill 的百分之一。把它们加成一个“显存需求”会同时看错容量和时间。
2. **prefill 与 decode 的比例完全不同**。8192 prefill 做 133.6 TFLOPs，一步 decode（batch=1）只做 0.02 TFLOPs，相差 6,700 倍；而两者读的权重几乎一样（14.16 vs 14.10 GiB）。这就是 prefill 计算密集、decode 访存密集的来源。
3. **命中前缀省的是计算，不是容量**。命中 6144 后补 2048，矩阵工作从 133.6 降到 37.1 TFLOPs（降 72%），新写 KV 从 1.125 降到 0.281 GiB，但结束时的 KV 常驻仍是 1.125 GiB——前缀还在那儿占着。
4. **按功能分组后，prefill 的工作集中在 SwiGLU**（89.1 of 133.6 TFLOPs，权重读取 10.1 GiB），注意力只有 19.8 TFLOPs，但它的激活读写高达 579 GiB——这正是 FlashAttention 要消除的那一部分（第 5 章展开）。

完整的逐场景、逐功能组表见 [results/qwen3-8b.md](results/qwen3-8b.md)。

## 限制

- 逐算子账是**逻辑载荷**：输入与权重理想读一次、输出物化，注意力分数默认 FP32 矩形物化。它显示融合能消除哪些边，**不是整个模型的 HBM 下界，更不是某引擎的实测流量**。
- 未计 tile 重读、L2 命中、KV dtype 转换、分配器工作区、kernel 启动与调度。
- 标量／特殊函数（exp、rsqrt、比较）单列，不折算成矩阵吞吐。
- `--output-head last` 口径：普通生成只算最后位置的输出头；训练／logprob 场景需另算。
