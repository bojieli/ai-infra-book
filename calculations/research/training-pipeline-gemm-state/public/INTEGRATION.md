# 公共候选迁移

迁入training_pipeline_gemm_state topic和同名测试。依赖已公共training_pipeline_schedule/training_nonmatrix/training_matrix，建议CLI topic `training-pipeline-gemm-state`。

参数microbatches/microbatch_size/tokens/policy/activation_policy/gemm_policy，加可选service_options（仅时间和link输入）。不让调用者混入additional_saved_bytes，否则会和按identity新增的预算混淆。

四场景、全字段报告、来源锁子集及公共依赖绑定已准备。运行 `python calculations/research/training-pipeline-gemm-state/public/verify_public.py`，4tests无可选依赖，不跳过。

汇总峰值已包含新persistent GEMM inputs和单product recompute workspace；原nonlinear/P/GQA不重计。字段仍明确是stage reservation subset，不能替代allocator peak或完整训练容量。
