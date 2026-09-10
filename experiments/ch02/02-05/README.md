# 实验 2-5：混合结构的状态与检索能力

对应正文 2.4 的核心练习。以 Kimi K3 与 DeepSeek-V4 为主，在同一长度与 batch 下列出常驻状态、prefill 与 decode 的工作；KDA 状态、MLA 历史、V4 索引和压缩缓冲分别列出，再配上固定检索质量记录。

## 独立运行

```bash
python3 run.py    # 现场调用 calculations/calc.py，产物写入 results/
```

资源侧数字由 `calc.py state|k3-forward|v4-forward` 用官方 config 现场生成，本实验不另行实现公式。本目录另有若干实跑子目录（`expert-preflight/`、`expert-stages/`、`full-model-run/`、`native-layer-probe/`、`runtime-preflight/`），各自独立说明在其 README 中。

## 常驻状态（历史 32,768、batch=1）

| 模型／路径 | 常驻合计 | 分项 |
| --- | ---: | --- |
| V4-Flash | **0.227 GiB** | 窗口 5.4 ＋ 压缩历史 173.0 ＋ 索引 42.0 ＋ 压缩缓冲 11.6 MiB |
| V4-Pro | 0.325 GiB | 窗口 7.6 ＋ 压缩历史 247.8 ＋ 索引 60.0 ＋ 压缩缓冲 17.9 MiB |
| K3（MLA compact ＋ KDA） | 1.267 GiB | KDA 递推 414.0 ＋ 短卷积槽 19.4 ＋ MLA 历史 864.0 MiB |
| Qwen3-8B（GQA 对照） | 4.500 GiB | KV 历史 4,608 MiB |
| K3（MLA expanded ＋ KDA） | 45.423 GiB | KDA 递推 414.0 ＋ 短卷积槽 19.4 ＋ MLA 历史 46,080 MiB |

同一条历史，五种表示相差 **200 倍**。三类机制各省下不同的东西：

- **V4 的压缩＋索引**把历史换成定长窗口 ＋ 压缩块 ＋ 索引项。省的是容量，增加的是索引扫描（实验 2-4 里 1M 历史时索引扫描是选中载荷的 7.6 倍）和压缩缓冲。
- **K3 的 KDA**把一部分层换成定长递推状态（414 MiB，与长度无关），省的是随长度增长的那一部分；代价是这些层不再能任意回看历史。
- **K3 的 MLA** 省的是每 token 的维度（低秩潜向量），但**只在 compact 路径上成立**——expanded 路径反而比 GQA 大 10 倍。

## prefill 与 decode 的工作

| 场景 | 矩阵 TFLOPs | 标量 GFLOPs |
| --- | ---: | ---: |
| K3 prefill 8192 | 1,744.7 | 2,245 |
| K3 decode 历史 8192 | 0.220 | 1.0 |
| V4-Flash prefill 8192 | 231.1 | 5,411 |
| V4-Flash decode 历史 8192 | 0.030 | 0.7 |

省容量不是免费的：V4-Flash 的 prefill 矩阵工作只有 K3 的 1/7.5，但**标量工作是 K3 的 2.4 倍**（5,411 vs 2,245 GFLOPs）——压缩、量化编解码、索引 top-k 和门控都记在这一栏。第 4 章讨论的“非矩阵工作接替成为限制”，在这张表上第一次出现。

## 检索质量

固定检索质量记录见 [../02-09/paired-retrieval/README.md](../02-09/paired-retrieval/README.md)：同一批消息上 Qwen3-8B 与 V4-Flash 均 8/8 通过，**不足以据此选出质量赢家**。省状态是否损害检索能力，需要专门的长距离检索题（多键变体已固定题目，见 `../02-09/multikey/`）。

完整数值见 [results/hybrid.md](results/hybrid.md)。

## 限制

- 状态是所声明的逻辑驻留，不是实际 HBM 占用；运行时量化转换、预分配与分配器工作区未计入。
- K3 compact 是教学执行路径，固定 HF 代码实际保存 expanded；两条都列出。
- V4 的统一 2 字节口径不等于实际混合 FP8/FP4 格式。
- 前缀检查点与恢复成本在第 8、9 章处理，本实验只给驻留与单次工作。
