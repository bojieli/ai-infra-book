# A800 40GB Active：补齐整数稀疏峰值的审计建议

审计日期：2026-09-09。范围为单张 A800 40GB Active 工作站卡，不扩展到 A800 80GB 数据中心卡。此文件是待合并建议，不代表硬件目录已经更新。

## 官方证据

在线复核 [NVIDIA A800 产品页](https://www.nvidia.com/en-us/products/workstations/a800/) 的 Highlights / Tensor Performance 与相邻脚注。页面明确列出“1,247 AI TOPS²”，脚注为“Theoretical INT8 TOPS using sparsity.”。同一页 Features / Third-Generation Tensor Cores 说明结构化稀疏支持；因此目录的 sparsity 枚举可以记录为 structured。

已有锁定来源 `nvidia-a800-active-page`，无需重复下载或新增来源 ID：

- 原件：`sources/hardware/nvidia-a800-active-page.html`，552620 bytes。
- 锁定 revision：`snapshot-2026-09-08`。
- SHA-256：`73da9cce681c8eeadd7ffa1325480495738ead5fa41cbc69c815e00a0cd84814`。
- 本轮重新计算 SHA，与来源锁匹配；原件包含上述值、脚注和结构化稀疏说明。2026-09-09 在线页面仍给相同口径。

## 可合并修改

将相邻文件 `a800-int8-peak-proposal.json` 的 `peak` 追加到 `a800-40gb-active.peak_rates`，同时追加 `note`。保留既有的 623.8 浮点峰值原始记录，不修改其 unspecified 字段。

| 字段 | 建议值 | 证据边界 |
| --- | --- | --- |
| input_precision | INT8 | 脚注明确 |
| accumulator_precision | unspecified | 产品页没有提供与该峰值绑定的累加格式 |
| execution_unit | tensor | Tensor Performance 标题与 Tensor Cores 说明 |
| sparsity | structured | 峰值脚注给 sparsity，同页特性说明给 structural sparsity |
| tera_ops_per_second | 1247 | 保留页面整数 TOPS 原值 |
| operation_kind | integer | 不得标为 floating_point 或 TFLOPS |
| source_id | nvidia-a800-active-page | 已有原件和哈希 |
| derivation | null | 直接记录，不除二、不推算 BF16 |

`clock_basis` 只记录理论峰值，不把 FP64 旁脚注 1 的 GPU Boost Clock 条件自动挪到 INT8 的脚注 2。目录已有 `spec_scope=single_device`，因此无需添加或更改 scope。

## 合并后的检查

目录总记录数预计从 271 增为 272，型号数保持 52；应以最终 catalog 实际输出为准。检查该设备只有一条 INT8/unspecified/tensor/structured 记录，并确保 `select_peak` 继续拒绝未知累加格式、整数 TOPS 作 FLOPs 分母及无依据的 BF16/FP32/dense 查询。必要时给 `HARDWARE-AUDIT.md` 添加该补核记录并更新计数，重新生成硬件可读表及结果来源清单。

此补核没有解决 A800 的 BF16 dense 训练峰值缺口。网页规格表的 623.8 TFLOPS 没有足够的输入、累加和稀疏限定；1247/2 的算术不能使它变成可用于 BF16 训练的证据。
