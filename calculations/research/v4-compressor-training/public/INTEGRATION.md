# 公共迁移候选

迁入topic `v4_compressor_training.py` 和同名测试，依赖上一候选公共topic `v4_attention_projections` 的值/VJP helper，不调用其calculate。建议CLI topic `v4-compressor-training`，输入batch/tokens，只允许128正整数倍。

三个场景/完整报告/54已有source记录原件/官方报告文本和模块依赖均绑定。用 `/Users/boj/miniconda3/bin/python calculations/research/v4-compressor-training/public/verify_public.py` 验证，要求4pass/0skip。

仅ratio128完整块prefill可微数学，ratio4/online restored-state/cast gradient字段保持false或null。状态bytes为active B切片，不是预分配maxbatch。不计其他topic工作量或saved，不能称完整V4训练完成。
