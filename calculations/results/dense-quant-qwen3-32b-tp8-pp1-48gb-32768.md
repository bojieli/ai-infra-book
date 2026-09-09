# qwen3-32b Dense 分片量化容量

TP=8 / PP=1 / DP=1；保留长度 32,768 （含最后新 token）；每卡 48,000,000,000 bytes，workspace 条件预算 2,147,483,648 bytes。

全部权重形状与 KV 所有权复用 BF16 placement。低比特为教学存储格式；条件并发受每副本最差 rank 限制，不是实际运行峰值保证。

| bits | 物理权重 bytes（含复制） | 独立 DP 副本合计最大请求 | 全卡权重+workspace 可放入 |
|---:|---:|---:|---|
| 16 | 65,533,722,624 | 35 | True |
| 8 | 34,815,688,704 | 38 | True |
| 4 | 19,212,877,824 | 40 | True |

| 副本 | bits | 同副本最大请求 | 限制 ranks |
|---:|---:|---:|---|
| 0 | 16 | 35 | [0, 1, 2, 3, 4, 5, 6, 7] |
| 0 | 8 | 38 | [0, 1, 2, 3, 4, 5, 6, 7] |
| 0 | 4 | 40 | [0, 1, 2, 3, 4, 5, 6, 7] |

分组按 local K 重新计算：group_size=128，scale=2 bytes；最后不满组仍有完整 scale，每行分别向上取整打包，无 zero point。embedding/head/norm 保持 BF16。下表 payload/scale 已包含 copies，勿再次乘层数。

## Rank 0（DP 0 / PP 0 / TP 0）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [0, 1, 2, 3, 4, 5, 6, 7]；KV heads [0]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 1（DP 0 / PP 0 / TP 1）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [8, 9, 10, 11, 12, 13, 14, 15]；KV heads [1]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 2（DP 0 / PP 0 / TP 2）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [16, 17, 18, 19, 20, 21, 22, 23]；KV heads [2]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 3（DP 0 / PP 0 / TP 3）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [24, 25, 26, 27, 28, 29, 30, 31]；KV heads [3]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 4（DP 0 / PP 0 / TP 4）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [32, 33, 34, 35, 36, 37, 38, 39]；KV heads [4]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 5（DP 0 / PP 0 / TP 5）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [40, 41, 42, 43, 44, 45, 46, 47]；KV heads [5]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 6（DP 0 / PP 0 / TP 6）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [48, 49, 50, 51, 52, 53, 54, 55]；KV heads [6]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

## Rank 7（DP 0 / PP 0 / TP 7）

层 IDs [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]；Q heads [56, 57, 58, 59, 60, 61, 62, 63]；KV heads [7]。其他 rank 出现相同 KV head 是真实副本，其权重与状态均再次计入。

| bits | payload bytes | scale bytes | KV bytes/请求 | KV 可用 bytes | 最大请求 | 权重+workspace 可放入 | 最大请求常驻 bytes | 下一请求 bytes |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 16 | 8,191,715,328 | 0 | 1,073,741,824 | 37,660,801,024 | 35 | True | 47,920,162,816 | 48,993,904,640 |
| 8 | 4,291,012,608 | 60,948,480 | 1,073,741,824 | 41,500,555,264 | 38 | True | 47,301,634,048 | 48,375,375,872 |
| 4 | 2,340,661,248 | 60,948,480 | 1,073,741,824 | 43,450,906,624 | 40 | True | 47,498,766,336 | 48,572,508,160 |

| 权重模板 | local shape | copies | 低位适用 | BF16 payload/scale bytes | 8bit payload/scale bytes | 4bit payload/scale bytes |
|---|---|---:|---|---:|---:|---:|
| model.embed_tokens.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.self_attn.q_proj.weight | [1024, 5120] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.k_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.v_proj.weight | [128, 5120] | 64 | True | 83,886,080 / 0 | 41,943,040 / 655,360 | 20,971,520 / 655,360 |
| model.layers.{layer}.self_attn.o_proj.weight | [5120, 1024] | 64 | True | 671,088,640 / 0 | 335,544,320 / 5,242,880 | 167,772,160 / 5,242,880 |
| model.layers.{layer}.self_attn.q_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.self_attn.k_norm.weight | [128] | 64 | False | 16,384 / 0 | 16,384 / 0 | 16,384 / 0 |
| model.layers.{layer}.input_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.layers.{layer}.post_attention_layernorm.weight | [5120] | 64 | False | 655,360 / 0 | 655,360 / 0 | 655,360 / 0 |
| model.norm.weight | [5120] | 1 | False | 10,240 / 0 | 10,240 / 0 | 10,240 / 0 |
| lm_head.weight | [18992, 5120] | 1 | False | 194,478,080 / 0 | 194,478,080 / 0 | 194,478,080 / 0 |
| model.layers.{layer}.mlp.gate_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.up_proj.weight | [3200, 5120] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |
| model.layers.{layer}.mlp.down_proj.weight | [5120, 3200] | 64 | True | 2,097,152,000 / 0 | 1,048,576,000 / 16,384,000 | 524,288,000 / 16,384,000 |

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
