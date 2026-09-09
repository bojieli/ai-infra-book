# online-softmax-state-merge — 

输入：`{"block_sizes": [1, 0, 1, 2], "scores": [null, 1000, 1001, null], "values": [[0, 0], [1, 2], [3, -2], [5, 7]]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| direct_output | `[2.4621171572600096, -0.9242343145200195]` |
| sequential_output | `[2.4621171572600096, -0.9242343145200195]` |
| tree_output | `[2.4621171572600096, -0.9242343145200195]` |
| naive_mean_of_block_outputs | `[2.0, 0.0]` |
| sequential_max_abs_error | 0.0 |
| tree_max_abs_error | 0.0 |
| naive_mean_max_abs_error | 0.9242343145200195 |
| nonempty_blocks | 2 |
| nontrivial_merges | 1 |
| merge_exp_calls | 2 |
| merge_subtractions | 2 |
| merge_weighted_sum_flops | 9 |
| merge_max_comparisons | 1 |
| final_divisions | 2 |
| actual_kernel_flops | `null` |

| 块 | 位置数 | 有效状态 | 块输出 | 前缀合并输出 |
| --- | ---: | --- | --- | --- |
| 0 | 1 | False | None | None |
| 1 | 0 | False | None | None |
| 2 | 1 | True | [1.0, 2.0] | [1.0, 2.0] |
| 3 | 2 | True | [3.0, -2.0] | [2.4621171572600096, -0.9242343145200195] |

计量条件：

- 每块保存最大值m、稳定指数和l、未归一化加权向量U。两块先换到共同最大值后分别合并l/U；最终只除一次l，不能将各块最终输出等权平均。
- None或负无穷分数为显式掩码，空块／全掩码块用None状态作合并单位元，避免exp(-inf-(-inf))。全体无有效位置的最终输出留空，不擅自定义成零。
- Python双精度与math.fsum作为小规模数值参照；顺序和树形在实数上等价，浮点检查采用误差容限，不声称任意GPU树或低精度路径逐位相同。
- 普通非空合并的最大值比较、两个exp／减法、l/U加权和及最终除法分别计量。空状态直接返回不计普通合并；局部QK/PV、局部softmax、拷贝及实际kernel填充不在合并子账内。
- 默认是正文三个分数和标量值的教学例；可通过JSON输入多维值、不同块划分及掩码。状态字节、执行时序与硬件性能需另给格式和后端。

固定来源：

