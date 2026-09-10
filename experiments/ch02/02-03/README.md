# 实验 2-3：GQA 与 K3 MLA 的容量和访问

对应正文 2.3。用 Qwen3-8B（GQA）与 Kimi K3（MLA）的实际配置，分别算常驻历史、单步历史读取与新增写入，再累加一段完整生成；比较两种 MLA 执行路径的矩阵尺寸和额外中间量。

## 独立运行

```bash
python3 run.py    # 写出 results/gqa-mla.json 与 .md
```

只需 Python 3.8+ 标准库。数值取自 `calculations/results/` 已复算的结果（官方 config、固定 revision）：`state-qwen3-8b-*`、`state-kimi-k3-*`、`cache-sequence-*`、`k3-mla-*`。本实验不重算。

## 结果

**一个 decode 步（历史 8192、batch=1）**

| 模型／路径 | 每 token 状态 | 常驻历史 | 历史读取 |
| --- | ---: | ---: | ---: |
| Qwen3-8B（GQA，8 KV 头） | 147,456 B | 1,152 MiB | 1,152 MiB |
| Kimi K3（MLA compact） | 27,648 B | 649 MiB | 216 MiB |
| Kimi K3（MLA expanded，HF 实际保存） | 1,474,560 B | 11,953 MiB | 11,520 MiB |

**同一序列上的头共享对照（prompt 8192、1024 步、命中 6144 前缀）**

| 变体 | KV 头 | 每 token | 最终常驻 | 整段历史读取 |
| --- | ---: | ---: | ---: | ---: |
| MHA（反事实） | 32 | 589,824 B | 5.06 GiB | 4,896 GiB |
| **GQA（Qwen3-8B 实际）** | 8 | 147,456 B | 1.27 GiB | 1,224 GiB |
| MQA（反事实） | 1 | 18,432 B | 0.16 GiB | 153 GiB |

头共享把容量和读取按 KV 头数**成比例**缩小：32→8 头降 4 倍，8→1 头再降 8 倍。batch=64 时同样的比例放大到 324／81／10.1 GiB——这就是 GQA 被普遍采用的直接原因。

**MLA 的两条执行路径（batch=64、历史 8192、单步）**

| 路径 | 投影 TFLOPs | 注意力 TFLOPs | 历史载荷 | 每层 FP32 分数张量 |
| --- | ---: | ---: | ---: | ---: |
| compact（权重吸收） | 0.713 | 2.629 | 13.5 GiB | 192 MiB |
| expanded（显式展开，HF 实际） | 0.713 | 0.773 | 720 GiB | 192 MiB |

**同一个 MLA 有两种执行方式，代价完全相反**：compact 只存低秩潜向量，历史载荷降到 1/53（13.5 vs 720 GiB），但注意力矩阵工作涨到 3.4 倍（2.63 vs 0.77 TFLOPs）；expanded 反之。选哪条取决于当前是访存受限还是计算受限——decode 通常选 compact，prefill 通常选 expanded。

比较 K3 与 Qwen3-8B 时必须点明是哪条路径：K3 compact 的每 token 状态（27,648 B）比 Qwen3-8B 的 GQA（147,456 B）小 5.3 倍，但 K3 expanded（1,474,560 B）反而大 10 倍。**不指明执行路径的“MLA 比 GQA 省多少”是无意义的**。

完整数值见 [results/gqa-mla.md](results/gqa-mla.md)。

## 限制

- 逻辑载荷口径：物理共享、分页填充、工作区和并行复制未计入，加入后要重算。
- compact 是教学执行路径；固定 HF 代码实际保存的是 expanded K/V。两者都列出，不把 compact 称作 K3 的现行缓存。
- 反事实 MHA／MQA 只改 KV 头数，其余配置不变，用于隔离头共享这一个因子，不代表存在这样的官方模型。
- 每头／每层对照与整模型对照在结果文件中分开保存，避免用单层数字乘错层数。
