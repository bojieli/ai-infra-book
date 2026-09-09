# deepseek-r1-distill-llama-70b Dense 分片量化容量

TP=2 / PP=4 / DP=1；保留长度 32,768 （含最后新 token）；每卡 80,000,000,000 bytes，workspace 条件预算 2,147,483,648 bytes。

全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；条件并发受每副本最差 rank 限制，不是实际运行峰值保证。

| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |
|---:|---:|---:|---|
| 16 | 141,110,050,816 | 44 | True |
| 8 | 73,728,557,056 | 50 | True |
| 4 | 39,503,036,416 | 53 | True |

| 副本 | bits | 同副本最大请求 | 限制 ranks |
|---:|---:|---:|---|
| 0 | 16 | 44 | [0, 1, 6, 7] |
| 0 | 8 | 50 | [0, 1, 6, 7] |
| 0 | 4 | 53 | [0, 1, 6, 7] |

分组按 local K 重新计算：group_size=128，scale=2 bytes；最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。

## Rank 0（DP 0 / PP 0 / TP 0）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 18,164,088,832 | 0 | 1,342,177,280 | 59,688,427,520 | 44 | True | 79,367,372,800 | 80,709,550,080 |
| 8 | 9,607,708,672 | 133,693,440 | 1,342,177,280 | 68,111,114,240 | 50 | True | 78,997,749,760 | 80,339,927,040 |
| 4 | 5,329,518,592 | 133,693,440 | 1,342,177,280 | 72,389,304,320 | 53 | True | 78,746,091,520 | 80,088,268,800 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [64128, 8192] | 1 | False | 1,050,673,152 / 0 | 1,050,673,152 / 0 | 1,050,673,152 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 1（DP 0 / PP 0 / TP 1）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 18,164,088,832 | 0 | 1,342,177,280 | 59,688,427,520 | 44 | True | 79,367,372,800 | 80,709,550,080 |
| 8 | 9,607,708,672 | 133,693,440 | 1,342,177,280 | 68,111,114,240 | 50 | True | 78,997,749,760 | 80,339,927,040 |
| 4 | 5,329,518,592 | 133,693,440 | 1,342,177,280 | 72,389,304,320 | 53 | True | 78,746,091,520 | 80,088,268,800 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [64128, 8192] | 1 | False | 1,050,673,152 / 0 | 1,050,673,152 / 0 | 1,050,673,152 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 2（DP 0 / PP 1 / TP 0）

层 IDs [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 17,113,415,680 | 0 | 1,342,177,280 | 60,739,100,672 | 45 | True | 79,658,876,928 | 81,001,054,208 |
| 8 | 8,557,035,520 | 133,693,440 | 1,342,177,280 | 69,161,787,392 | 51 | True | 79,289,253,888 | 80,631,431,168 |
| 4 | 4,278,845,440 | 133,693,440 | 1,342,177,280 | 73,439,977,472 | 54 | True | 79,037,595,648 | 80,379,772,928 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 3（DP 0 / PP 1 / TP 1）

层 IDs [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 17,113,415,680 | 0 | 1,342,177,280 | 60,739,100,672 | 45 | True | 79,658,876,928 | 81,001,054,208 |
| 8 | 8,557,035,520 | 133,693,440 | 1,342,177,280 | 69,161,787,392 | 51 | True | 79,289,253,888 | 80,631,431,168 |
| 4 | 4,278,845,440 | 133,693,440 | 1,342,177,280 | 73,439,977,472 | 54 | True | 79,037,595,648 | 80,379,772,928 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 4（DP 0 / PP 2 / TP 0）

层 IDs [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 17,113,415,680 | 0 | 1,342,177,280 | 60,739,100,672 | 45 | True | 79,658,876,928 | 81,001,054,208 |
| 8 | 8,557,035,520 | 133,693,440 | 1,342,177,280 | 69,161,787,392 | 51 | True | 79,289,253,888 | 80,631,431,168 |
| 4 | 4,278,845,440 | 133,693,440 | 1,342,177,280 | 73,439,977,472 | 54 | True | 79,037,595,648 | 80,379,772,928 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 5（DP 0 / PP 2 / TP 1）

层 IDs [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 17,113,415,680 | 0 | 1,342,177,280 | 60,739,100,672 | 45 | True | 79,658,876,928 | 81,001,054,208 |
| 8 | 8,557,035,520 | 133,693,440 | 1,342,177,280 | 69,161,787,392 | 51 | True | 79,289,253,888 | 80,631,431,168 |
| 4 | 4,278,845,440 | 133,693,440 | 1,342,177,280 | 73,439,977,472 | 54 | True | 79,037,595,648 | 80,379,772,928 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 6（DP 0 / PP 3 / TP 0）

层 IDs [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]；Q heads [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]；KV heads [0, 1, 2, 3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 18,164,105,216 | 0 | 1,342,177,280 | 59,688,411,136 | 44 | True | 79,367,389,184 | 80,709,566,464 |
| 8 | 9,607,725,056 | 133,693,440 | 1,342,177,280 | 68,111,097,856 | 50 | True | 78,997,766,144 | 80,339,943,424 |
| 4 | 5,329,534,976 | 133,693,440 | 1,342,177,280 | 72,389,287,936 | 53 | True | 78,746,107,904 | 80,088,285,184 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.norm.weight | [8192] | 1 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| lm_head.weight | [64128, 8192] | 1 | False | 1,050,673,152 / 0 | 1,050,673,152 / 0 | 1,050,673,152 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## Rank 7（DP 0 / PP 3 / TP 1）

层 IDs [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79]；Q heads [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；KV heads [4, 5, 6, 7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 18,164,105,216 | 0 | 1,342,177,280 | 59,688,411,136 | 44 | True | 79,367,389,184 | 80,709,566,464 |
| 8 | 9,607,725,056 | 133,693,440 | 1,342,177,280 | 68,111,097,856 | 50 | True | 78,997,766,144 | 80,339,943,424 |
| 4 | 5,329,534,976 | 133,693,440 | 1,342,177,280 | 72,389,287,936 | 53 | True | 78,746,107,904 | 80,088,285,184 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.layers.{layer}.self_attn.q_proj.weight | [4096, 8192] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.self_attn.k_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.v_proj.weight | [512, 8192] | 20 | True | 167,772,160 / 0 | 83,886,080 / 1,310,720 | 41,943,040 / 1,310,720 |
| model.layers.{layer}.self_attn.o_proj.weight | [8192, 4096] | 20 | True | 1,342,177,280 / 0 | 671,088,640 / 10,485,760 | 335,544,320 / 10,485,760 |
| model.layers.{layer}.input_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [8192] | 20 | False | 327,680 / 0 | 327,680 / 0 | 327,680 / 0 |
| model.norm.weight | [8192] | 1 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| lm_head.weight | [64128, 8192] | 1 | False | 1,050,673,152 / 0 | 1,050,673,152 / 0 | 1,050,673,152 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.up_proj.weight | [14336, 8192] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |
| model.layers.{layer}.mlp.down_proj.weight | [8192, 14336] | 20 | True | 4,697,620,480 / 0 | 2,348,810,240 / 36,700,160 | 1,174,405,120 / 36,700,160 |

## 范围

- Reuses the public dense_placement local tensor shapes/copies, KV-head identity and pipeline ownership unchanged. BF16 weights and one-request residency exactly match the base graph.
- Retained length includes the last new token: base history=length-1, tokens=1, batch_per_replica=1. KV remains BF16 for every weight format; no fractional KV-head saving.
- 8/4bit symmetric teaching storage quantizes local 2D projections only, independently per output row and local K group, with ceil tail groups and per-row packed-byte rounding. Embedding, head and all norms stay BF16; no zero points.
- All three models use actual config-derived weights. Storage is not a released quantized checkpoint, quality result, or supported kernel claim.
- Each independent DP replica is limited by its worst rank. TP/PP ranks share a cohort; free bytes on another rank cannot cover a failing rank. DP global request capacities sum independent replica cohorts.
- Workspace is a fixed supplied per-rank reserve, not inferred peak. Activation, routing, dequantization, collective, allocator and batch-dependent workspace may exceed it; conditional maximum requests is not measured runtime capacity.
- Base BF16 placement arithmetic/communication summaries are reference values only; quantization does not establish kernel arithmetic or traffic savings. C13 remains broader than this declared storage model.

## 固定来源

- [configs/models/deepseek-r1-distill-llama-70b/config.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/config.json)；SHA256 `95ef9768e4741543dbfaf0c274f101855883ff338b235c99eca2b6a4f4abee12`。
- [sources/deepseek-r1-distill-llama-70b/model.safetensors.index.json](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/model.safetensors.index.json)；SHA256 `3b91e78c60e2708c9354d46fe4fc20520d0a12713e13d5ffab60118305c96620`。
- [sources/deepseek-r1-distill-llama-70b/README.md](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/resolve/b1c0b44b4369b597ad119a196caf79a9c40e141e/README.md)；SHA256 `d26d26ddb518fee60c6c6bf7a708bd751b1619d93a4944f188143693d956c77f`。
- [sources/deepseek-r1-distill-llama-70b/modeling_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/modeling_llama.py)；SHA256 `9f7e93602e876a8f3f171e4911df5a5898ac407b8eb8982099e52b53daf0469e`。
- [sources/deepseek-r1-distill-llama-70b/configuration_llama.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/llama/configuration_llama.py)；SHA256 `c13469c62dc2c4fe76cc5bc50e6db2de21e302dae259945ef03308f0ac429ff6`。
- [research/llama70-adapter/modeling_rope_utils.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/modeling_rope_utils.py)；SHA256 `c28b3e88edca8fdb5497e5c36091bf753db49bd94ace33a84e9f9c61cbf66032`。
