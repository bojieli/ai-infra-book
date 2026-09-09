# qwen3-8b Dense 分片量化容量

TP=2 / PP=4 / DP=1；保留长度 32,768 （含最后新 token）；每卡 48,000,000,000 bytes，workspace 条件预算 2,147,483,648 bytes。

全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；条件并发受每副本最差 rank 限制，不是实际运行峰值保证。

| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |
|---:|---:|---:|---|
| 16 | 16,382,087,168 | 72 | True |
| 8 | 9,544,847,360 | 73 | True |
| 4 | 6,071,963,648 | 74 | True |

| 副本 | bits | 同副本最大请求 | 限制 ranks |
|---:|---:|---:|---|
| 0 | 16 | 72 | [0, 1, 6, 7] |
| 0 | 8 | 73 | [0, 1, 6, 7] |
| 0 | 4 | 74 | [0, 1, 6, 7] |

分组按 local K 重新计算：group_size=128，scale=2 bytes；最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。

## Rank 0（DP 0 / PP 0 / TP 0）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 2,358,923,776 | 0 | 603,979,776 | 43,493,592,576 | 72 | True | 47,992,951,296 | 48,596,931,072 |
| 8 | 1,490,702,848 | 13,565,952 | 603,979,776 | 44,348,247,552 | 73 | True | 47,742,276,096 | 48,346,255,872 |
| 4 | 1,056,592,384 | 13,565,952 | 603,979,776 | 44,782,358,016 | 74 | True | 47,912,145,408 | 48,516,125,184 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [75968, 4096] | 1 | False | 622,329,856 / 0 | 622,329,856 / 0 | 622,329,856 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 1（DP 0 / PP 0 / TP 1）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8]；Q heads [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 2,358,923,776 | 0 | 603,979,776 | 43,493,592,576 | 72 | True | 47,992,951,296 | 48,596,931,072 |
| 8 | 1,490,702,848 | 13,565,952 | 603,979,776 | 44,348,247,552 | 73 | True | 47,742,276,096 | 48,346,255,872 |
| 4 | 1,056,592,384 | 13,565,952 | 603,979,776 | 44,782,358,016 | 74 | True | 47,912,145,408 | 48,516,125,184 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [75968, 4096] | 1 | False | 622,329,856 / 0 | 622,329,856 / 0 | 622,329,856 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 2（DP 0 / PP 1 / TP 0）

层 IDs [9, 10, 11, 12, 13, 14, 15, 16, 17]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,736,593,920 | 0 | 603,979,776 | 44,115,922,432 | 73 | True | 47,974,601,216 | 48,578,580,992 |
| 8 | 868,372,992 | 13,565,952 | 603,979,776 | 44,970,577,408 | 74 | True | 47,723,926,016 | 48,327,905,792 |
| 4 | 434,262,528 | 13,565,952 | 603,979,776 | 45,404,687,872 | 75 | True | 47,893,795,328 | 48,497,775,104 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 3（DP 0 / PP 1 / TP 1）

层 IDs [9, 10, 11, 12, 13, 14, 15, 16, 17]；Q heads [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,736,593,920 | 0 | 603,979,776 | 44,115,922,432 | 73 | True | 47,974,601,216 | 48,578,580,992 |
| 8 | 868,372,992 | 13,565,952 | 603,979,776 | 44,970,577,408 | 74 | True | 47,723,926,016 | 48,327,905,792 |
| 4 | 434,262,528 | 13,565,952 | 603,979,776 | 45,404,687,872 | 75 | True | 47,893,795,328 | 48,497,775,104 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 4（DP 0 / PP 2 / TP 0）

层 IDs [18, 19, 20, 21, 22, 23, 24, 25, 26]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,736,593,920 | 0 | 603,979,776 | 44,115,922,432 | 73 | True | 47,974,601,216 | 48,578,580,992 |
| 8 | 868,372,992 | 13,565,952 | 603,979,776 | 44,970,577,408 | 74 | True | 47,723,926,016 | 48,327,905,792 |
| 4 | 434,262,528 | 13,565,952 | 603,979,776 | 45,404,687,872 | 75 | True | 47,893,795,328 | 48,497,775,104 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 5（DP 0 / PP 2 / TP 1）

层 IDs [18, 19, 20, 21, 22, 23, 24, 25, 26]；Q heads [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,736,593,920 | 0 | 603,979,776 | 44,115,922,432 | 73 | True | 47,974,601,216 | 48,578,580,992 |
| 8 | 868,372,992 | 13,565,952 | 603,979,776 | 44,970,577,408 | 74 | True | 47,723,926,016 | 48,327,905,792 |
| 4 | 434,262,528 | 13,565,952 | 603,979,776 | 45,404,687,872 | 75 | True | 47,893,795,328 | 48,497,775,104 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 6（DP 0 / PP 3 / TP 0）

层 IDs [27, 28, 29, 30, 31, 32, 33, 34, 35]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 2,358,931,968 | 0 | 603,979,776 | 43,493,584,384 | 72 | True | 47,992,959,488 | 48,596,939,264 |
| 8 | 1,490,711,040 | 13,565,952 | 603,979,776 | 44,348,239,360 | 73 | True | 47,742,284,288 | 48,346,264,064 |
| 4 | 1,056,600,576 | 13,565,952 | 603,979,776 | 44,782,349,824 | 74 | True | 47,912,153,600 | 48,516,133,376 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.norm.weight | [4096] | 1 | False | 8,192 / 0 | 8,192 / 0 | 8,192 / 0 |
| lm_head.weight | [75968, 4096] | 1 | False | 622,329,856 / 0 | 622,329,856 / 0 | 622,329,856 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## Rank 7（DP 0 / PP 3 / TP 1）

层 IDs [27, 28, 29, 30, 31, 32, 33, 34, 35]；Q heads [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 2,358,931,968 | 0 | 603,979,776 | 43,493,584,384 | 72 | True | 47,992,959,488 | 48,596,939,264 |
| 8 | 1,490,711,040 | 13,565,952 | 603,979,776 | 44,348,239,360 | 73 | True | 47,742,284,288 | 48,346,264,064 |
| 4 | 1,056,600,576 | 13,565,952 | 603,979,776 | 44,782,349,824 | 74 | True | 47,912,153,600 | 48,516,133,376 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [2048, 4096] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 4096] | 9 | True | 37,748,736 / 0 | 18,874,368 / 294,912 | 9,437,184 / 294,912 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 2048] | 9 | True | 150,994,944 / 0 | 75,497,472 / 1,179,648 | 37,748,736 / 1,179,648 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 9 | False | 2,304 / 0 | 2,304 / 0 | 2,304 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 9 | False | 73,728 / 0 | 73,728 / 0 | 73,728 / 0 |
| model.norm.weight | [4096] | 1 | False | 8,192 / 0 | 8,192 / 0 | 8,192 / 0 |
| lm_head.weight | [75968, 4096] | 1 | False | 622,329,856 / 0 | 622,329,856 / 0 | 622,329,856 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.up_proj.weight | [6144, 4096] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 6144] | 9 | True | 452,984,832 / 0 | 226,492,416 / 3,538,944 | 113,246,208 / 3,538,944 |

## 范围

- Reuses the public dense_placement local tensor shapes/copies, KV-head identity and pipeline ownership unchanged. BF16 weights and one-request residency exactly match the base graph.
- Retained length includes the last new token: base history=length-1, tokens=1, batch_per_replica=1. KV remains BF16 for every weight format; no fractional KV-head saving.
- 8/4bit symmetric teaching storage quantizes local 2D projections only, independently per output row and local K group, with ceil tail groups and per-row packed-byte rounding. Embedding, head and all norms stay BF16; no zero points.
- All three models use actual config-derived weights. Storage is not a released quantized checkpoint, quality result, or supported kernel claim.
- Each independent DP replica is limited by its worst rank. TP/PP ranks share a cohort; free bytes on another rank cannot cover a failing rank. DP global request capacities sum independent replica cohorts.
- Workspace is a fixed supplied per-rank reserve, not inferred peak. Activation, routing, dequantization, collective, allocator and batch-dependent workspace may exceed it; conditional maximum requests is not measured runtime capacity.
- Base BF16 placement arithmetic/communication summaries are reference values only; quantization does not establish kernel arithmetic or traffic savings. C13 remains broader than this declared storage model.

## 固定来源

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)；SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)；SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)；SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)；SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
