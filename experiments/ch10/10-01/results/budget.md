# 实验 10-1 结果：训练状态的容量预算

BF16 权重与梯度、FP32 主权重与两个 Adam 动量；逐 rank 字节按 ZeRO 阶段分列。

| 模型 | rank 数 | 设备 | stage 0 | stage 1 | stage 2 | stage 3 | 最低可行阶段 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| qwen3-8b | 8 | 4090 24 GB | 122.1 GiB✗ | 42.0 GiB✗ | 28.6 GiB✗ | 15.3 GiB | **stage 3** |
| qwen3-8b | 8 | A100/H100 80 GB | 122.1 GiB✗ | 42.0 GiB | 28.6 GiB | 15.3 GiB | **stage 1** |
| qwen3-8b | 8 | B200 180 GB | 122.1 GiB | 42.0 GiB | 28.6 GiB | 15.3 GiB | **stage 0** |
| qwen3-8b | 64 | 4090 24 GB | 122.1 GiB✗ | 31.9 GiB✗ | 16.9 GiB | 1.9 GiB | **stage 2** |
| qwen3-8b | 64 | A100/H100 80 GB | 122.1 GiB✗ | 31.9 GiB | 16.9 GiB | 1.9 GiB | **stage 1** |
| qwen3-8b | 64 | B200 180 GB | 122.1 GiB | 31.9 GiB | 16.9 GiB | 1.9 GiB | **stage 0** |
| qwen3-32b | 8 | 4090 24 GB | 488.2 GiB✗ | 167.8 GiB✗ | 114.4 GiB✗ | 61.0 GiB✗ | **全部放不下** |
| qwen3-32b | 8 | A100/H100 80 GB | 488.2 GiB✗ | 167.8 GiB✗ | 114.4 GiB✗ | 61.0 GiB | **stage 3** |
| qwen3-32b | 8 | B200 180 GB | 488.2 GiB✗ | 167.8 GiB✗ | 114.4 GiB | 61.0 GiB | **stage 2** |
| qwen3-32b | 64 | 4090 24 GB | 488.2 GiB✗ | 127.8 GiB✗ | 67.7 GiB✗ | 7.6 GiB | **stage 3** |
| qwen3-32b | 64 | A100/H100 80 GB | 488.2 GiB✗ | 127.8 GiB✗ | 67.7 GiB | 7.6 GiB | **stage 2** |
| qwen3-32b | 64 | B200 180 GB | 488.2 GiB✗ | 127.8 GiB | 67.7 GiB | 7.6 GiB | **stage 1** |
| qwen3-235b-a22b | 8 | 4090 24 GB | 3503.2 GiB✗ | 1204.2 GiB✗ | 821.1 GiB✗ | 437.9 GiB✗ | **全部放不下** |
| qwen3-235b-a22b | 8 | A100/H100 80 GB | 3503.2 GiB✗ | 1204.2 GiB✗ | 821.1 GiB✗ | 437.9 GiB✗ | **全部放不下** |
| qwen3-235b-a22b | 8 | B200 180 GB | 3503.2 GiB✗ | 1204.2 GiB✗ | 821.1 GiB✗ | 437.9 GiB✗ | **全部放不下** |
| qwen3-235b-a22b | 64 | 4090 24 GB | 3503.2 GiB✗ | 916.8 GiB✗ | 485.8 GiB✗ | 54.7 GiB✗ | **全部放不下** |
| qwen3-235b-a22b | 64 | A100/H100 80 GB | 3503.2 GiB✗ | 916.8 GiB✗ | 485.8 GiB✗ | 54.7 GiB | **stage 3** |
| qwen3-235b-a22b | 64 | B200 180 GB | 3503.2 GiB✗ | 916.8 GiB✗ | 485.8 GiB✗ | 54.7 GiB | **stage 3** |

（✗ 表示该阶段逐 rank 状态超出设备容量。）
