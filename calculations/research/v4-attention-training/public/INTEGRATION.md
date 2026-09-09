# 公共就绪候选

迁入 `src/infra_calc/topics/v4_attention_training.py` 与 `tests/test_v4_attention_training.py`。建议 topic=`v4-attention-training`，calculate 参数为 batch/tokens/kv_tokens/heads/head_dim/indices；专用 markdown 完整列出结果字段。

`book.append.json` 提供3个扁平场景。两个默认配置窗口场景覆盖128边界及129跨窗口，第三个是明确的小尺寸重复ID夹具，不能标作真实模型完整forward。

执行 `/Users/boj/miniconda3/bin/python calculations/research/v4-attention-training/public/verify_public.py`，需4pass/0skip；纯 unittest 可直接 discover 此 tests 目录，也可迁入后运行。

既有公共来源锁54记录重用、原件hash核验，无新增下载。结果和来源依赖绑定在 bindings.json。

量化警戒不是泛泛免责声明：官方 source 在PV前转换的是未归一化指数的BF16，候选返回 `quantized_kernel_value_equivalence=false`、`cast_surrogate_gradient=null`。不能把这里实数softmax的梯度说成已证明的源码BF16 backward。完整 attention layer、压缩器、indexer loss、外围投影/位置变换、QAT和整模型训练均保留未完成。
