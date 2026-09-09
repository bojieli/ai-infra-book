# qwen3-32b Dense 分片量化容量

TP=2 / PP=4 / DP=1；保留长度 32,768 （含最后新 token）；每卡 80,000,000,000 bytes，workspace 条件预算 2,147,483,648 bytes。

全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；条件并发受每副本最差 rank 限制，不是实际运行峰值保证。

| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |
|---:|---:|---:|---|
| 16 | 65,525,600,256 | 64 | True |
| 8 | 34,807,566,336 | 68 | True |
| 4 | 19,204,755,456 | 69 | True |

| 副本 | bits | 同副本最大请求 | 限制 ranks |
|---:|---:|---:|---|
| 0 | 16 | 64 | [0, 1, 6, 7] |
| 0 | 8 | 68 | [0, 1, 2, 3, 4, 5, 6, 7] |
| 0 | 4 | 69 | [0, 1, 6, 7] |

分组按 local K 重新计算：group_size=128，scale=2 bytes；最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。

## Rank 0（DP 0 / PP 0 / TP 0）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,579,653,632 | 0 | 1,073,741,824 | 69,272,862,720 | 64 | True | 79,446,614,016 | 80,520,355,840 |
| 8 | 4,678,950,912 | 60,948,480 | 1,073,741,824 | 73,112,616,960 | 68 | True | 79,901,827,072 | 80,975,568,896 |
| 4 | 2,728,599,552 | 60,948,480 | 1,073,741,824 | 75,062,968,320 | 69 | True | 79,025,217,536 | 80,098,959,360 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [75968, 5120] | 1 | False | 777,912,320 / 0 | 777,912,320 / 0 | 777,912,320 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 1（DP 0 / PP 0 / TP 1）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,579,653,632 | 0 | 1,073,741,824 | 69,272,862,720 | 64 | True | 79,446,614,016 | 80,520,355,840 |
| 8 | 4,678,950,912 | 60,948,480 | 1,073,741,824 | 73,112,616,960 | 68 | True | 79,901,827,072 | 80,975,568,896 |
| 4 | 2,728,599,552 | 60,948,480 | 1,073,741,824 | 75,062,968,320 | 69 | True | 79,025,217,536 | 80,098,959,360 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [75968, 5120] | 1 | False | 777,912,320 / 0 | 777,912,320 / 0 | 777,912,320 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 2（DP 0 / PP 1 / TP 0）

层 IDs [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 7,801,741,312 | 0 | 1,073,741,824 | 70,050,775,040 | 65 | True | 79,742,443,520 | 80,816,185,344 |
| 8 | 3,901,038,592 | 60,948,480 | 1,073,741,824 | 73,890,529,280 | 68 | True | 79,123,914,752 | 80,197,656,576 |
| 4 | 1,950,687,232 | 60,948,480 | 1,073,741,824 | 75,840,880,640 | 70 | True | 79,321,047,040 | 80,394,788,864 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 3（DP 0 / PP 1 / TP 1）

层 IDs [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 7,801,741,312 | 0 | 1,073,741,824 | 70,050,775,040 | 65 | True | 79,742,443,520 | 80,816,185,344 |
| 8 | 3,901,038,592 | 60,948,480 | 1,073,741,824 | 73,890,529,280 | 68 | True | 79,123,914,752 | 80,197,656,576 |
| 4 | 1,950,687,232 | 60,948,480 | 1,073,741,824 | 75,840,880,640 | 70 | True | 79,321,047,040 | 80,394,788,864 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 4（DP 0 / PP 2 / TP 0）

层 IDs [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 7,801,741,312 | 0 | 1,073,741,824 | 70,050,775,040 | 65 | True | 79,742,443,520 | 80,816,185,344 |
| 8 | 3,901,038,592 | 60,948,480 | 1,073,741,824 | 73,890,529,280 | 68 | True | 79,123,914,752 | 80,197,656,576 |
| 4 | 1,950,687,232 | 60,948,480 | 1,073,741,824 | 75,840,880,640 | 70 | True | 79,321,047,040 | 80,394,788,864 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 5（DP 0 / PP 2 / TP 1）

层 IDs [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 7,801,741,312 | 0 | 1,073,741,824 | 70,050,775,040 | 65 | True | 79,742,443,520 | 80,816,185,344 |
| 8 | 3,901,038,592 | 60,948,480 | 1,073,741,824 | 73,890,529,280 | 68 | True | 79,123,914,752 | 80,197,656,576 |
| 4 | 1,950,687,232 | 60,948,480 | 1,073,741,824 | 75,840,880,640 | 70 | True | 79,321,047,040 | 80,394,788,864 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 6（DP 0 / PP 3 / TP 0）

层 IDs [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,579,663,872 | 0 | 1,073,741,824 | 69,272,852,480 | 64 | True | 79,446,624,256 | 80,520,366,080 |
| 8 | 4,678,961,152 | 60,948,480 | 1,073,741,824 | 73,112,606,720 | 68 | True | 79,901,837,312 | 80,975,579,136 |
| 4 | 2,728,609,792 | 60,948,480 | 1,073,741,824 | 75,062,958,080 | 69 | True | 79,025,227,776 | 80,098,969,600 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [75968, 5120] | 1 | False | 777,912,320 / 0 | 777,912,320 / 0 | 777,912,320 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 7（DP 0 / PP 3 / TP 1）

层 IDs [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,579,663,872 | 0 | 1,073,741,824 | 69,272,852,480 | 64 | True | 79,446,624,256 | 80,520,366,080 |
| 8 | 4,678,961,152 | 60,948,480 | 1,073,741,824 | 73,112,606,720 | 68 | True | 79,901,837,312 | 80,975,579,136 |
| 4 | 2,728,609,792 | 60,948,480 | 1,073,741,824 | 75,062,958,080 | 69 | True | 79,025,227,776 | 80,098,969,600 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 5120] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 5120] | 16 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 4096] | 16 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 16 | False | 4,096 / 0 | 4,096 / 0 | 4,096 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 16 | False | 163,840 / 0 | 163,840 / 0 | 163,840 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [75968, 5120] | 1 | False | 777,912,320 / 0 | 777,912,320 / 0 | 777,912,320 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [12800, 5120] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 12800] | 16 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## 范围

- Reuses the public dense_placement local tensor shapes/copies, KV-head identity and pipeline ownership unchanged. BF16 weights and one-request residency exactly match the base graph.
- Retained length includes the last new token: base history=length-1, tokens=1, batch_per_replica=1. KV remains BF16 for every weight format; no fractional KV-head saving.
- 8/4bit symmetric teaching storage quantizes local 2D projections only, independently per output row and local K group, with ceil tail groups and per-row packed-byte rounding. Embedding, head and all norms stay BF16; no zero points.
- All three models use actual config-derived weights. Storage is not a released quantized checkpoint, quality result, or supported kernel claim.
- Each independent DP replica is limited by its worst rank. TP/PP ranks share a cohort; free bytes on another rank cannot cover a failing rank. DP global request capacities sum independent replica cohorts.
- Workspace is a fixed supplied per-rank reserve, not inferred peak. Activation, routing, dequantization, collective, allocator and batch-dependent workspace may exceed it; conditional maximum requests is not measured runtime capacity.
- Base BF16 placement arithmetic/communication summaries are reference values only; quantization does not establish kernel arithmetic or traffic savings. C13 remains broader than this declared storage model.

## 固定来源

- [configs/models/qwen3-32b/config.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/config.json)；SHA256 `97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb`。
- [sources/qwen3-32b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-32B/resolve/9216db5781bf21249d130ec9da846c4624c16137/model.safetensors.index.json)；SHA256 `bed42c6c55274bc08a1f616bceb3bcb84b3f02cb6584c573bd18c6519291ecd0`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)；SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)；SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
