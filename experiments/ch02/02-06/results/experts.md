# 实验 2-6 结果：专家矩阵与负载

## Qwen3.6-35B-A3B（256 选 8 ＋ 共享专家，40 层）

| 场景 | 有工作的专家 | routed TFLOPs | routed 权重读取 | 共享 TFLOPs | 共享权重 | 全模型 TFLOPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.6 prefill 8192（batch=1） | 256／256 | 16.4927 | 60.000 GiB | 2.0629 | 0.235 GiB | 52.095 |
| Qwen3.6 decode batch=1 | 8／8 | 0.0020 | 1.875 GiB | 0.0003 | 0.235 GiB | 0.007 |
| Qwen3.6 decode batch=64 | 256／256 | 0.1288 | 60.000 GiB | 0.0161 | 0.235 GiB | 0.469 |

## V4-Flash／V4-Pro／K3 的 FFN 矩阵台账

| 模型 | batch | 路由 | FFN TFLOPs | routed | shared | latent | dense 首层 | 每层专家并集 | 批内权重载荷 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek-v4-flash | 1 | balanced | 0.0152 | 0.0130 | 0.0022 | 0.0000 | 0.0000 | 6 | 14.19 GiB |
| deepseek-v4-flash | 64 | balanced | 0.9754 | 0.8311 | 0.1385 | 0.0000 | 0.0000 | 256 | 518.10 GiB |
| deepseek-v4-flash | 1 | concentrated | 0.0152 | 0.0130 | 0.0022 | 0.0000 | 0.0000 | 6 | 14.19 GiB |
| deepseek-v4-flash | 64 | concentrated | 0.9754 | 0.8311 | 0.1385 | 0.0000 | 0.0000 | 6 | 14.19 GiB |
| deepseek-v4-pro | 1 | balanced | 0.0568 | 0.0484 | 0.0081 | 0.0000 | 0.0000 | 6 | 52.85 GiB |
| deepseek-v4-pro | 64 | balanced | 3.6321 | 3.0948 | 0.5158 | 0.0000 | 0.0000 | 384 | 2890.07 GiB |
| deepseek-v4-pro | 1 | concentrated | 0.0568 | 0.0484 | 0.0081 | 0.0000 | 0.0000 | 6 | 52.85 GiB |
| deepseek-v4-pro | 64 | concentrated | 3.6321 | 3.0948 | 0.5158 | 0.0000 | 0.0000 | 6 | 52.85 GiB |
| kimi-k3 | 1 | balanced | 0.1336 | 0.0972 | 0.0243 | 0.0095 | 0.0015 | 16 | 124.46 GiB |
| kimi-k3 | 64 | balanced | 8.5530 | 6.2234 | 1.5559 | 0.6051 | 0.0930 | 896 | 5105.40 GiB |
| kimi-k3 | 1 | concentrated | 0.1336 | 0.0972 | 0.0243 | 0.0095 | 0.0015 | 16 | 124.46 GiB |
| kimi-k3 | 64 | concentrated | 8.5530 | 6.2234 | 1.5559 | 0.6051 | 0.0930 | 16 | 124.46 GiB |
