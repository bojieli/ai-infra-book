# 公共候选接入

迁入v4_compressor_overlap topic及同名测试，依赖v4_attention_projections纯数学helper。建议CLI topic `v4-compressor-overlap`，参数batch/tokens；4场景覆盖无完整块、首块、两块及尾状态。

使用 `/Users/boj/miniconda3/bin/python calculations/research/v4-compressor-overlap/public/verify_public.py`，4pass/0skip。普通unittest可直接discover tests。54已有来源原件和官方报告文本均绑定。

显式公共表达式共享使APE forward少于源重复计算，差额字段保留；不是源码指令级复刻。状态输出提供上游梯度接口，不表示已实现未来online/任意restore。actual_peak、cast surrogate保持null。旧候选及公共文件未改。
