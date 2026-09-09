# 公共候选

迁入v4_compressor_online与同名测试，模块依赖v4_attention_projections纯函数helper；组合测试另需ratio128和ratio4 prefill topics。建议CLI topic `v4-compressor-online`，参数batch/start_pos/tokens/ratio/initial_state_mode。

4测试/0skip及4场景/完整报告/54来源记录原件、report文本、三个helper候选绑定。用 `/Users/boj/miniconda3/bin/python calculations/research/v4-compressor-online/public/verify_public.py` 验证。

正start_pos仅单token串行，不支持并行chunk。initial_state_mode指梯度所有权而非实际训练detach策略。所有cast/量化surrogate未知，完整训练和实际峰值未完成。
