# 实验 2-3 结果：GQA 与 K3 MLA 的容量和访问

## 一个 decode 步（历史 8192、batch=1）

| 模型／路径 | 每 token 状态 | 常驻历史 | 历史读取 | 新增写入 |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-8B（GQA，8 KV 头） | 147456 B | 1152.000 MiB | 1152.000 MiB | 147456 B |
| Kimi K3（MLA compact 路径） | — | 649.406 MiB | 216.000 MiB | — |
| Kimi K3（MLA expanded 路径，HF 实际保存） | — | 11953.406 MiB | 11520.000 MiB | — |

## 一段完整生成（prompt 8192、1024 步、命中前缀 6144）

| 组 | 变体 | KV 头 | 每 token | 最终常驻 | 整段历史读取 | 整段写入 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B batch=1 | native_gqa（基准） | 8 | 147456 B | 1.266 GiB | 1223.9 GiB | 0.141 GiB |
| Qwen3-8B batch=1 | counterfactual_mha | 32 | 589824 B | 5.062 GiB | 4895.7 GiB | 0.562 GiB |
| Qwen3-8B batch=1 | counterfactual_mqa | 1 | 18432 B | 0.158 GiB | 153.0 GiB | 0.018 GiB |
| Qwen3-8B batch=64 | native_gqa（基准） | 8 | 147456 B | 81.000 GiB | 78331.5 GiB | 9.000 GiB |
| Qwen3-8B batch=64 | counterfactual_mha | 32 | 589824 B | 324.000 GiB | 313326.0 GiB | 36.000 GiB |
| Qwen3-8B batch=64 | counterfactual_mqa | 1 | 18432 B | 10.125 GiB | 9791.4 GiB | 1.125 GiB |
| Kimi K3 batch=1 | expanded（基准） | — | 1474560 B | 13.079 GiB | 12239.3 GiB | 1.406 GiB |
| Kimi K3 batch=1 | compact | — | 27648 B | 0.661 GiB | 229.5 GiB | 0.026 GiB |

## K3 两条 MLA 执行路径（batch=64、历史 8192、单步）

| 路径 | 矩阵参数 | 投影 TFLOPs | 注意力 TFLOPs | 历史载荷 | 新增写入 | 每层 FP32 分数张量 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| compact（权重吸收，教学执行路径） | 5.573 B | 0.7133 | 2.6288 | 13.50 GiB | 1.69 MiB | 192.0 MiB |
| expanded（显式展开，HF 代码实际保存） | 5.573 B | 0.7133 | 0.7732 | 720.00 GiB | 90.00 MiB | 192.0 MiB |
