# 模型覆盖审计与下一实施任务

2026-09-09，根据当前工作树和已经锁定的官方原件审计；未下载权重载荷，也未把配置下载算成可运行模型支持。

| 模型 | 已有主要覆盖 | 仍缺的重要覆盖 |
|---|---|---|
| Qwen3-8B / 32B | 通用完整逻辑 forward，矩阵/非矩阵/载荷，训练矩阵子账 | 非矩阵反向、实际后端运行和完整生命周期 |
| Qwen3-30B-A3B / 235B-A22B | 通用 MoE forward，显式路由直方图，参数索引核验 | 实际路由轨迹、并行 placement 和完整训练执行 |
| DeepSeek V4 Flash / Pro | 独立 v4_forward，attention/expert/mHC/state/checkpoint 子账 | 非 routed FP8 Linear 计量、运行时格式与分配、MTP/多 token 前缀路径 |
| Kimi K3 | 独立 k3_forward，MLA/KDA/AttnRes/latent experts/checkpoint | 69 个 A_log 的 128/96 来源差异；运行时格式、vision/MTP/训练 |
| DeepSeek V3 | 官方 config + modeling_deepseek.py 已锁定 | 尚无 forward、state 或 experts 分派 |
| Qwen3.5-397B-A17B / Qwen3-VL-4B | 官方 config 已锁定 | 必要实现来源和结构适配 |
| 实际 70B 代表 | PLAN F02 仍待办 | 当前 C01 名义 70B 不替代具体模型 |

通用 models.forward 只分派 qwen3 和 qwen3_moe，但不能据此断言 V4/K3 零覆盖；它们使用独立专题入口。PLAN C10/C11/C12 仍未勾选与当前实际边界一致。

## 本轮已实施：V4 非 routed FP8 Linear

新增 `topics/v4_fp8_linear.py` 与三个针对性测试，尚未接 CLI/reproduce/正文。复用 `v4_attention.calculate` 的矩阵记录和 `experts.calculate` 的 shared 类；读取固定 config，并校验官方 `sources/{model}/inference/model.py` / `kernel.py` 的 SHA。没有新增网络来源。

选择 wq_a、wq_b、wkv_shared、wo_b、CSA index_wq_b 和 shared gate/up/down。排除显式 BF16 wo_a/weights_proj、FP32 compressor/router/head、routed FP4 和 MTP。`ModelArgs.scale_dtype='fp8'` 是配置省略字段时的官方代码默认；参考 Linear 权重为 E4M3，scale 为 E8M0，输入 BF16，累加 FP32，限定 world_size=1。

官方 kernel 的 tile 为 32×128×128。对于 M/K/N，K/N 按 128 对齐：

- 有效矩阵：2MKN；tile：2ceil(M/32)×32×K×N。
- 激活量化：每个有效元素一次除法，每个 128-group 一次 scale 乘法；abs/max/clamp/cast 与 power-of-two 位操作单列。
- 每 K-block 的 Scale_C 只按 row/output-block 计算，乘法数为 M×(N/128)×(K/128)；输出修正为 2MN×(K/128)。**不是每个输出元素三个 FLOPs**，因为 scale product 由 128 列共享。
- 接口字节分两次调用：act_quant 的 BF16 读、FP8/scale 写；GEMM 的 FP8/scale/weight 读和 BF16 写。临时结果跨接口重复出现，明确不是物理 HBM 流量。
- shared gate/up 同输入仍分别触发量化；不擅自假定缓存复用。

推荐集成场景：Flash/Pro 各 T=8192 prefill、B=1/T=1/H=8192 decode；Flash B=64 decode；Flash T=33 对照尾 tile。现有 attention 边界会拒绝 H>0 且 T>1 的未覆盖执行路径。

验证已执行：`PYTHONPATH=calculations/src python3 -m unittest discover -s calculations/tests -p test_v4_fp8_linear.py -q`，3 项通过。覆盖独立 tile 循环枚举、scale 共享、接口字节、1/31/32/33/64 行边界、非法维度和官方两模型几何。后续集成必须从 v4_forward 的既有矩阵总数中替换对应 valid subtotal，不能把这些矩阵再加一次。新增 scalar 部分只限这些 Linear，不能将全图 non_matrix coverage 标为完整。

## 后续完整子任务：DeepSeek V3 基础逻辑前向

官方固定 config 与实现已在 `configs/models/deepseek-v3/config.json` / `sources/deepseek-v3/modeling_deepseek.py`，均经 `read_source` 校验。字段：61 层、H=7168、前 3 层 dense F=18432；后 58 层 256 routed/top-8、一个 shared、F=2048。MLA 为 128 heads，q rank1536、KV rank512、NoPE128+RoPE64、V128；词表129280，独立输出头，MTP 一层单列。

实现应复用 Scenario 因果 pairs、Qwen routing_counts、通用单位和 provenance；不要复用 K3 的 NoPE/output gate 假设。V3 官方 forward 实际执行 RoPE，且先展开 K/V 再 cache.update。MoE noaux_tc 使用 sigmoid、修正 bias、每组 top-2 和四组选择，再从原始 scores 提取权重并归一化乘 2.5；不能套平面 top-k。紧凑 MLA 只能作为有代数验证的替代路径。

验收：逐矩阵/归一化/路由/残差/嵌入输出头账；61 层完整参数张量枚举；独立 shape 对照；decode/prefill/缓存容量守恒；expanded/compact 小矩阵等价；checkpoint 索引头未获取前明确 config/source 参数数未获 checkpoint 验证；FP8 物理存储/运行时量化、MTP 和训练保持明确缺口。该子任务可补 F02/C12 经典模型支持，但不使全书自动完成。
