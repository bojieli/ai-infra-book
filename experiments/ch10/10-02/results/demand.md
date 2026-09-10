# 实验 10-2 结果：从训练任务反推资源

目标：100B token／30 天。

**算法 FLOPs 的统计范围**：算法 FLOPs 的统计范围＝训练矩阵子账（前向＋反向的矩阵乘，含注意力，按所声明的输出头范围）；不含非矩阵、优化器、重计算、通信与格式转换。效率因此按同一子账定义，不能直接套用完整训练步口径的 MFU。

| 模型 | 更新范围 | 每 token 训练矩阵 | 总量 | 设备 | 效率 | 需要设备数 | 容量下界设备数 | 谁支配 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | A100 80GB SXM | 30% | **21** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | A100 80GB SXM | 40% | **16** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | A100 80GB SXM | 50% | **13** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | H100 SXM | 30% | **7** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | H100 SXM | 40% | **5** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | H100 SXM | 50% | **4** | 2 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | B200 SXM | 30% | **3** | 1 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | B200 SXM | 40% | **3** | 1 | 算力 |
| qwen3-8b | 全 token | 4.9e+10 FLOPs | 4.9e+21 FLOPs | B200 SXM | 50% | **2** | 1 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | A100 80GB SXM | 30% | **20** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | A100 80GB SXM | 40% | **15** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | A100 80GB SXM | 50% | **12** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | H100 SXM | 30% | **7** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | H100 SXM | 40% | **5** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | H100 SXM | 50% | **4** | 2 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | B200 SXM | 30% | **3** | 1 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | B200 SXM | 40% | **2** | 1 | 算力 |
| qwen3-8b | SFT（1/4 计损失） | 4.62e+10 FLOPs | 4.62e+21 FLOPs | B200 SXM | 50% | **2** | 1 | 算力 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | A100 80GB SXM | 30% | **62** | 53 | 算力 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | A100 80GB SXM | 40% | **46** | 53 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | A100 80GB SXM | 50% | **37** | 53 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | H100 SXM | 30% | **20** | 53 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | H100 SXM | 40% | **15** | 53 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | H100 SXM | 50% | **12** | 53 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | B200 SXM | 30% | **9** | 24 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | B200 SXM | 40% | **7** | 24 | 容量 |
| qwen3-235b-a22b | 全 token | 1.48e+11 FLOPs | 1.48e+22 FLOPs | B200 SXM | 50% | **6** | 24 | 容量 |
