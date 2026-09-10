# 实验 2-6：从 Qwen3.6 到 V4-Flash 的专家矩阵与负载

对应正文 2.5（进阶延伸）。先算 Qwen3.6 的 256 选 8 ＋ 共享专家，改变 batch 与每专家 token 数；再用 V4 的 256 选 6 ＋ 共享专家重算；进阶换成 K3 的潜空间专家。核心问题：同一专家被多个 token 使用时，新增的是计算还是权重读取。

## 独立运行

```bash
python3 run.py    # 现场调用 calculations/calc.py，产物写入 results/
```

只需 Python 3.8+ 标准库。本实验**不另行实现公式**，全部由 `calc.py qwen36-forward` 与 `calc.py experts` 用官方 config 现场生成。

## Qwen3.6-35B-A3B（256 专家、top-8、共享专家，40 层）

| 场景 | 有工作的专家 | routed TFLOPs | routed 权重读取 | 共享 TFLOPs | 全模型 TFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: |
| prefill 8192，batch=1 | 256／256 | 16.49 | 60.0 GiB | 2.06 | 52.10 |
| decode batch=1 | **8**／256 | 0.0020 | **1.875 GiB** | 0.0003 | 0.007 |
| decode batch=64 | **256**／256 | 0.129 | **60.0 GiB** | 0.016 | 0.469 |

batch 从 1 到 64，routed 计算涨 **64 倍**（0.0020→0.129 TFLOPs，正比于 token 数），routed 权重读取却涨 **32 倍**（1.875→60.0 GiB）并在此**触顶**——因为 256 个专家已经全被点到，再加 batch 也不会读更多权重。这就是 MoE 的关键收支：**计算随 token 数线性增长，权重载荷随批内专家并集增长，而并集有上限**。

## V4-Flash／V4-Pro／K3 的 FFN 台账

| 模型 | batch | 路由 | FFN TFLOPs | 每层专家并集 | 批内权重载荷 |
| --- | ---: | --- | ---: | ---: | ---: |
| V4-Flash | 64 | balanced | 0.975 | 256 | **518.1 GiB** |
| V4-Flash | 64 | concentrated | 0.975 | 6 | **14.2 GiB** |
| V4-Pro | 64 | balanced | 3.632 | 384 | 2,890 GiB |
| V4-Pro | 64 | concentrated | 3.632 | 6 | 52.9 GiB |
| K3 | 64 | balanced | 8.553 | 896 | 5,105 GiB |
| K3 | 64 | concentrated | 8.553 | 16 | 124.5 GiB |

**同样的 FLOPs，权重载荷相差 36 倍（V4-Flash）到 55 倍（V4-Pro）。** 路由是否集中不改变一个 token 要做多少乘法，却完全改变这一批要把多少权重搬进来。这条差别决定了第 6 章的专家并行切分、第 9 章的热门专家放置与复制，以及所有关于“MoE 到底省不省”的讨论——省的是计算，不一定是搬移。

K3 的 dense 首层（0.093 TFLOPs @ b64）和潜空间专家（0.605）单列，不并进 routed；共享分支在所有三个模型里都是**每个 token 必读**的固定成本。

完整数值与每次 CLI 调用的原始输出见 [results/experts.md](results/experts.md)。

## 限制

- 均匀／集中路由是**声明的输入**，不是观测轨迹。真实路由分布见第 9 章的实测。
- 台账的统一 2 字节权重载荷不等于 V4 的 FP4/FP8 或 K3 的 MXFP4 实际存储。
- 专家矩阵台账不含路由标量、归一化、dispatch 排序与合并；这些在 calculations 的 `non_matrix_operations` 与 `dispatch_operations` 里单列。
- 多卡切分（第 6 章）与 CPU／GPU 放置和交接（第 9 章）不在本实验范围。
