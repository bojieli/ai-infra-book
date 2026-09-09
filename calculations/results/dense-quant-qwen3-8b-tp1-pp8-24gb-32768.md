# qwen3-8b Dense 分片量化容量

TP=1 / PP=8 / DP=1；保留长度 32,768 （含最后新 token）；每卡 24,000,000,000 bytes，workspace 条件预算 2,147,483,648 bytes。

全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；条件并发受每副本最差 rank 限制，不是实际运行峰值保证。

| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |
|---:|---:|---:|---|
| 16 | 16,381,470,720 | 27 | True |
| 8 | 9,544,230,912 | 29 | True |
| 4 | 6,071,347,200 | 29 | True |

| 副本 | bits | 同副本最大请求 | 限制 ranks |
|---:|---:|---:|---|
| 0 | 16 | 27 | [0] |
| 0 | 8 | 29 | [0] |
| 0 | 4 | 29 | [0] |

分组按 local K 重新计算：group_size=128，scale=2 bytes；最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。

## Rank 0（DP 0 / PP 0 / TP 0）

层 IDs [0, 1, 2, 3, 4]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 3,174,124,032 | 0 | 671,088,640 | 18,678,392,320 | 27 | True | 23,441,000,960 | 24,112,089,600 |
| 8 | 2,209,434,112 | 15,073,280 | 671,088,640 | 19,628,008,960 | 29 | True | 23,833,561,600 | 24,504,650,240 |
| 4 | 1,727,089,152 | 15,073,280 | 671,088,640 | 20,110,353,920 | 29 | True | 23,351,216,640 | 24,022,305,280 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [151936, 4096] | 1 | False | 1,244,659,712 / 0 | 1,244,659,712 / 0 | 1,244,659,712 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |

## Rank 1（DP 0 / PP 1 / TP 0）

层 IDs [5, 6, 7, 8, 9]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,929,464,320 | 0 | 671,088,640 | 19,923,052,032 | 29 | True | 23,538,518,528 | 24,209,607,168 |
| 8 | 964,774,400 | 15,073,280 | 671,088,640 | 20,872,668,672 | 31 | True | 23,931,079,168 | 24,602,167,808 |
| 4 | 482,429,440 | 15,073,280 | 671,088,640 | 21,355,013,632 | 31 | True | 23,448,734,208 | 24,119,822,848 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |

## Rank 2（DP 0 / PP 2 / TP 0）

层 IDs [10, 11, 12, 13, 14]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,929,464,320 | 0 | 671,088,640 | 19,923,052,032 | 29 | True | 23,538,518,528 | 24,209,607,168 |
| 8 | 964,774,400 | 15,073,280 | 671,088,640 | 20,872,668,672 | 31 | True | 23,931,079,168 | 24,602,167,808 |
| 4 | 482,429,440 | 15,073,280 | 671,088,640 | 21,355,013,632 | 31 | True | 23,448,734,208 | 24,119,822,848 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |

## Rank 3（DP 0 / PP 3 / TP 0）

层 IDs [15, 16, 17, 18, 19]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,929,464,320 | 0 | 671,088,640 | 19,923,052,032 | 29 | True | 23,538,518,528 | 24,209,607,168 |
| 8 | 964,774,400 | 15,073,280 | 671,088,640 | 20,872,668,672 | 31 | True | 23,931,079,168 | 24,602,167,808 |
| 4 | 482,429,440 | 15,073,280 | 671,088,640 | 21,355,013,632 | 31 | True | 23,448,734,208 | 24,119,822,848 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 5 | True | 41,943,040 / 0 | 20,971,520 / 327,680 | 10,485,760 / 327,680 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 5 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 5 | False | 1,280 / 0 | 1,280 / 0 | 1,280 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 5 | False | 40,960 / 0 | 40,960 / 0 | 40,960 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 5 | True | 503,316,480 / 0 | 251,658,240 / 3,932,160 | 125,829,120 / 3,932,160 |

## Rank 4（DP 0 / PP 4 / TP 0）

层 IDs [20, 21, 22, 23]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,543,571,456 | 0 | 536,870,912 | 20,308,944,896 | 37 | True | 23,555,278,848 | 24,092,149,760 |
| 8 | 771,819,520 | 12,058,624 | 536,870,912 | 21,068,638,208 | 39 | True | 23,869,327,360 | 24,406,198,272 |
| 4 | 385,943,552 | 12,058,624 | 536,870,912 | 21,454,514,176 | 39 | True | 23,483,451,392 | 24,020,322,304 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |

## Rank 5（DP 0 / PP 5 / TP 0）

层 IDs [24, 25, 26, 27]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,543,571,456 | 0 | 536,870,912 | 20,308,944,896 | 37 | True | 23,555,278,848 | 24,092,149,760 |
| 8 | 771,819,520 | 12,058,624 | 536,870,912 | 21,068,638,208 | 39 | True | 23,869,327,360 | 24,406,198,272 |
| 4 | 385,943,552 | 12,058,624 | 536,870,912 | 21,454,514,176 | 39 | True | 23,483,451,392 | 24,020,322,304 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |

## Rank 6（DP 0 / PP 6 / TP 0）

层 IDs [28, 29, 30, 31]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 1,543,571,456 | 0 | 536,870,912 | 20,308,944,896 | 37 | True | 23,555,278,848 | 24,092,149,760 |
| 8 | 771,819,520 | 12,058,624 | 536,870,912 | 21,068,638,208 | 39 | True | 23,869,327,360 | 24,406,198,272 |
| 4 | 385,943,552 | 12,058,624 | 536,870,912 | 21,454,514,176 | 39 | True | 23,483,451,392 | 24,020,322,304 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |

## Rank 7（DP 0 / PP 7 / TP 0）

层 IDs [32, 33, 34, 35]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3, 4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 2,788,239,360 | 0 | 536,870,912 | 19,064,276,992 | 35 | True | 23,726,204,928 | 24,263,075,840 |
| 8 | 2,016,487,424 | 12,058,624 | 536,870,912 | 19,823,970,304 | 36 | True | 23,503,382,528 | 24,040,253,440 |
| 4 | 1,630,611,456 | 12,058,624 | 536,870,912 | 20,209,846,272 | 37 | True | 23,654,377,472 | 24,191,248,384 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.k_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.v_proj.weight | [1024, 4096] | 4 | True | 33,554,432 / 0 | 16,777,216 / 262,144 | 8,388,608 / 262,144 |
| model.layers.{layer}.self_attn.o_proj.weight | [4096, 4096] | 4 | True | 134,217,728 / 0 | 67,108,864 / 1,048,576 | 33,554,432 / 1,048,576 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 4 | False | 1,024 / 0 | 1,024 / 0 | 1,024 / 0 |
| model.layers.{layer}.input_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [4096] | 4 | False | 32,768 / 0 | 32,768 / 0 | 32,768 / 0 |
| model.norm.weight | [4096] | 1 | False | 8,192 / 0 | 8,192 / 0 | 8,192 / 0 |
| lm_head.weight | [151936, 4096] | 1 | False | 1,244,659,712 / 0 | 1,244,659,712 / 0 | 1,244,659,712 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.up_proj.weight | [12288, 4096] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |
| model.layers.{layer}.mlp.down_proj.weight | [4096, 12288] | 4 | True | 402,653,184 / 0 | 201,326,592 / 3,145,728 | 100,663,296 / 3,145,728 |

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
