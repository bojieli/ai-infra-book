# fusion-rounding-and-state-counterexamples — 

输入：`{"block_size": 128, "larger_first": false}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| finite_nonnegative_e4m3fn_encodings | 127 |
| maximum_finite | 448 |
| full_row_exact | `"55/56"` |
| prefix_exact | `"1"` |
| exact_difference | `"1/56"` |
| full_row_fp16 | 0.98193359375 |
| prefix_fp16 | 1.0 |
| equal_after_fp16 | `false` |
| lost_state_full_result | 3 |
| lost_state_unsafe_result | `"1"` |
| sufficient_state_result | 3 |
| actual_gpu_kernel_result | `null` |

计量条件：

- E4M3FN按官方ONNX位布局枚举非负有限编码，bias=7、3位fraction，subnormal步长2^-9，最大448；转换只接受有限数，饱和最近偶数舍入，零统一为正零。不是E4M3FNUZ或均匀INT8刻度。
- 反例两块首项分别1与10，只给1对应权重设1，其他项为0。整行尺度取amax/448；前缀尺度随块更新，已累加量按旧／新amax重新缩放。larger_first同时重排值和权重，不改变原始数学点积。
- FP8舍入用Fraction精确计算，其余算术也用有理数隔离舍入影响；最后另转IEEE FP16。未模拟真实FP32累加、融合指令或GPU执行，不能把此结果称某个kernel实测。
- 不可逆因子反例保留各块(m,c)：m为零时c丢失sum(y)，将零分母换成1无法恢复。增加sum(y)状态才可正确合并，不将防除零等同于语义证明。
- 本例证明某些输入和分块会不等价，不估计一般误差分布或质量影响；前缀顺序改变结果，也不能由随机宽容差测试推出逐位等价。

固定来源：

- [sources/formats/onnx-float8.html](https://onnx.ai/onnx/technical/float8.html)，SHA256 `8200a9f0872e8cb61915983e9b6eb3d2a587c6abdd470b24e586fb55eddb818e`。
