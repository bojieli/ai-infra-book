# 实验 2-5 结果：混合结构的状态与检索能力

同一条件：历史 32768 token、batch=1。

## 常驻状态的构成

| 模型／路径 | 常驻合计 | 分项 |
| --- | ---: | --- |
| K3（MLA compact ＋ KDA） | 1.267 GiB | kda_recurrent 414.0 MiB；short_conv_slots 19.4 MiB；mla_history 864.0 MiB |
| K3（MLA expanded ＋ KDA） | 45.423 GiB | kda_recurrent 414.0 MiB；short_conv_slots 19.4 MiB；mla_history 46080.0 MiB |
| V4-Flash（窗口＋压缩＋索引） | 0.227 GiB | window_history 5.4 MiB；compressed_history 173.0 MiB；index_history 42.0 MiB；main_compressor_buffer 11.3 MiB；index_compressor_buffer 0.3 MiB；main_selected_payload 20.9 MiB |
| V4-Pro（窗口＋压缩＋索引） | 0.325 GiB | window_history 7.6 MiB；compressed_history 247.8 MiB；index_history 60.0 MiB；main_compressor_buffer 17.4 MiB；index_compressor_buffer 0.5 MiB；main_selected_payload 45.4 MiB |
| Qwen3-8B（GQA 对照） | 4.500 GiB | kv_history 4608.0 MiB |

## prefill 与 decode 的工作

| 场景 | 矩阵 TFLOPs | 标量 GFLOPs |
| --- | ---: | ---: |
| K3 prefill 8192 | 1744.7010 | 2245.3 |
| K3 decode 历史 8192 | 0.2204 | 1.0 |
| V4-Flash prefill 8192 | 231.1253 | 5410.7 |
| V4-Flash decode 历史 8192 | 0.0295 | 0.7 |

固定检索质量记录见 [../02-09/paired-retrieval/README.md](../02-09/paired-retrieval/README.md)。
