# speculative-sampling — 

输入：`{"draft": ["1/2", "1/2", "0"], "target": ["1/2", "1/2", "0"]}`

数值为教学概率的精确有理数枚举，不是模型采样实测。

| 结果 | 值 |
| --- | ---: |
| vocabulary_size | 3 |
| acceptance_exact | `"1"` |
| rejection_exact | `"0"` |
| output_mass_exact | `"1"` |
| output_matches_target | `true` |
| total_variation_exact | `"0"` |
| wrong_total_variation_exact | `"0"` |

| token | 目标 p | 草稿 q | 条件接受 | 接受质量 | 拒绝修正分布 | 正确输出 | 错误输出 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1/2 | 1/2 | 1 | 1/2 | None | 1/2 | 1/2 |
| 1 | 1/2 | 1/2 | 1 | 1/2 | None | 1/2 | 1/2 |
| 2 | 0 | 0 | None | 0 | None | 0 | 0 |

计量条件：

- 单个固定前缀上的教学概率，词表以共同索引对齐；输入必须已完成temperature/top-k/top-p等处理且归一化，不代表任何真实模型准确率。
- 接受概率min(1,p/q)，拒绝后按正残差max(0,p-q)归一化采样。逐项枚举接受质量与每条拒绝→替换路径；全部采用有理数。
- q=0的提议不可达，条件接受率记null；拒绝总质量为零时残差分布不可达，记null，不计算0/0。
- 错误对照在拒绝后直接从原目标p重采样；某些特殊分布仍恰好无偏，不能用这类样例替代一般正确性。
- 算法依据：[Leviathan et al., ICML 2023, Algorithm 1 / Appendix A.1](https://proceedings.mlr.press/v202/leviathan23a.html)。本模块只验证单步概率质量，不验证多token引擎、随机数实现、浮点误差或KV回滚。

固定来源：

