# qwen-shape-specialization — qwen3-8b

输入：`{"bucket_compile_ns": 200000000, "bucket_flops_per_second": 200000000000000, "buckets": [512, 2048], "cached_artifacts": [], "generic_compile_ns": 100000000, "generic_flops_per_second": 100000000000000, "repetitions": 1000, "shapes": [{"count": 8, "tokens": 256}, {"count": 1, "tokens": 1536}, {"count": 1, "tokens": 2048}], "specialized_compile_ns": 300000000, "specialized_flops_per_second": 250000000000000, "specialized_tokens": [256, 1536, 2048]}`

数值是分析计算；字节以 bytes 保存，FMA=2，不是硬件测量。

| 结果 | 值 |
| --- | ---: |
| cohort_calls | 10 |
| cohort_real_matrix_flops | 1,700,807,049,216 |
| selected_policy | `"specialized"` |
| actual_gpu_seconds | `null` |

| 策略 | 准备 ms | 每频数组 ms | 含准备总计 ms | 补齐 FLOPs | 回退调用数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| generic | 100.0 | 17.00807049216 | 17108.07049216 | 0 | 0 |
| bucket | 400.0 | 12.36950581248 | 12769.50581248 | 773094113280 | 0 |
| specialized | 900.0 | 6.803228196864 | 7703.228196864 | 0 | 0 |

generic工件与映射：`{"artifacts": {"generic": 100000000}, "shapes": [{"tokens": 256, "count": 8, "executed_tokens": 256, "artifact": "generic", "fallback": false, "per_call_matrix_flops": 77309411328}, {"tokens": 1536, "count": 1, "executed_tokens": 1536, "artifact": "generic", "fallback": false, "per_call_matrix_flops": 463856467968}, {"tokens": 2048, "count": 1, "executed_tokens": 2048, "artifact": "generic", "fallback": false, "per_call_matrix_flops": 618475290624}]}`


bucket工件与映射：`{"artifacts": {"bucket:512": 200000000, "bucket:2048": 200000000}, "shapes": [{"tokens": 256, "count": 8, "executed_tokens": 512, "artifact": "bucket:512", "fallback": false, "per_call_matrix_flops": 154618822656}, {"tokens": 1536, "count": 1, "executed_tokens": 2048, "artifact": "bucket:2048", "fallback": false, "per_call_matrix_flops": 618475290624}, {"tokens": 2048, "count": 1, "executed_tokens": 2048, "artifact": "bucket:2048", "fallback": false, "per_call_matrix_flops": 618475290624}]}`


specialized工件与映射：`{"artifacts": {"specialized:256": 300000000, "specialized:1536": 300000000, "specialized:2048": 300000000}, "shapes": [{"tokens": 256, "count": 8, "executed_tokens": 256, "artifact": "specialized:256", "fallback": false, "per_call_matrix_flops": 77309411328}, {"tokens": 1536, "count": 1, "executed_tokens": 1536, "artifact": "specialized:1536", "fallback": false, "per_call_matrix_flops": 463856467968}, {"tokens": 2048, "count": 1, "executed_tokens": 2048, "artifact": "specialized:2048", "fallback": false, "per_call_matrix_flops": 618475290624}]}`


精确交叉条件：`[{"policy_a": "generic", "policy_b": "bucket", "difference_intercept_ns": -300000000, "difference_slope_exact_ns": "14495514624/3125", "equality_repetitions_exact": "1220703125/18874368", "condition": "A faster iff intercept + repetitions * slope < 0; repetitions is a positive integer"}, {"policy_a": "generic", "policy_b": "specialized", "difference_intercept_ns": -800000000, "difference_slope_exact_ns": "159450660864/15625", "equality_repetitions_exact": "6103515625/77856768", "condition": "A faster iff intercept + repetitions * slope < 0; repetitions is a positive integer"}, {"policy_a": "bucket", "policy_b": "specialized", "difference_intercept_ns": -500000000, "difference_slope_exact_ns": "86973087744/15625", "equality_repetitions_exact": "30517578125/339738624", "condition": "A faster iff intercept + repetitions * slope < 0; repetitions is a positive integer"}]`

计量条件：

- 工作对象为官方Qwen Dense单层FFN三个矩阵，FLOPs=6*M*H*F；不包含激活函数、注意力、通信或完整模型。形状频数为显式教学输入。
- 100/200/250TFLOP/s是按同一有效矩阵口径定义的教学服务率，不是GPU官方峰值或实测，不从率差声称编译器实际加速。分桶用补齐后的行数重新计工作。
- 按最小可容纳桶分派，超出桶上限或未列入特化集合时用通用路径；通用编译仅在实际使用时计一次。每个用到的artifact每实例准备一次，缓存命中准备为零，不按调用次数重复编译。
- 缓存是声明可直接使用的已兼容工件，未计加载／校验时间；实例之间是否共享须由输入指定。三个策略是互斥部署方案，不把它们的准备成本加在一起。
- 总时间=缺失工件准备+频数组重复次数*执行时间；串行预算，不模拟编译重叠、缓存淘汰或形状到达顺序。交叉条件为精确仿射不等式，不保证交点在正整数部署范围内。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
