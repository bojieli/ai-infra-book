# 公共就绪候选

迁入同名src topic和tests；建议topic `v4-attention-projections`，输入 batch/tokens，导出calculate/reference/markdown。三场景是单外围，不包含core，不乘43层。

`verify_public.py` 执行3测试、结果重放、54条既有来源原件hash与依赖绑定。运行解释器 `/Users/boj/miniconda3/bin/python`，要求3pass/0skip。没有新增源或共享目录修改。

固定源码边界与每项公式见上层CONTRACT.md。不要把core和外围保存的Q/KV再加一份；不要把压缩层额外indexer/compressor梯度当成已经完成。
