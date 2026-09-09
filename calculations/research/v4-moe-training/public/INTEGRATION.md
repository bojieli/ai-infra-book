# 公共就绪候选

迁入v4_moe_training topic与同名测试；依赖公共router primitive、投影helper与routing_counts。建议CLI topic `v4-moe-training`，输入batch/tokens/layer_id/routing/counts。

四场景区分负载/层分支，4tests0skip；verify_public验证来源与结果重放。完整quantization边界和单层scope见CONTRACT，不能将此加到旧43层router primitive总账产生重复。
