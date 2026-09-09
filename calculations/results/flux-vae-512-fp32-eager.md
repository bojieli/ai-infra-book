# FLUX2 Klein VAE 解码算子账

输入 `[1, 32, 64, 64]` → RGB `[1, 3, 512, 512]`；dtype=fp32，attention=eager。

解码权重 49,620,259 参数 / 198,481,036 bytes；dense matrix/conv 2,515,584,155,648 FLOPs，有效非 padding 2,499,289,811,968 FLOPs，标量算术 4,660,786,112。特殊函数另列。

命名张量边界峰值 806,354,944 bytes，位于 `up3.residual0.silu1`。条件权重+边界+指定 workspace：未知 / 未提供 bytes。

以下接口 bytes 不是 HBM 实测；边界峰值不含 primitive 内部临时量、未知 layout 复制和分配器开销。实际运行峰值未知，不能据此直接宣称设备可运行。

| 步 | 算子 | 输入形状 → 输出形状 | matrix FLOPs | scalar | 特殊函数 | 读 / 写 / 权重 bytes |
|---:|---|---|---:|---:|---|---|
| 0 | post_quant (conv2d) | 1×32×64×64 → 1×32×64×64 | 8,388,608 | 131,072 | {} | 524,288 / 524,288 / 4,224 |
| 1 | decoder.input (conv2d) | 1×32×64×64 → 1×512×64×64 | 1,207,959,552 | 2,097,152 | {} | 524,288 / 8,388,608 / 591,872 |
| 2 | mid.residual0.norm1 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 3 | mid.residual0.silu1 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 4 | mid.residual0.conv1 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 5 | mid.residual0.norm2 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 6 | mid.residual0.silu2 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 7 | mid.residual0.conv2 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 8 | mid.residual0.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 9 | mid.residual0.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 10 | mid.attention.norm (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 11 | mid.attention.q (linear_1x1) | 1×512×64×64 → 1×512×64×64 | 2,147,483,648 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 1,050,624 |
| 12 | mid.attention.k (linear_1x1) | 1×512×64×64 → 1×512×64×64 | 2,147,483,648 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 1,050,624 |
| 13 | mid.attention.v (linear_1x1) | 1×512×64×64 → 1×512×64×64 | 2,147,483,648 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 1,050,624 |
| 14 | mid.attention.qk (attention_qk) | 1×512×64×64, 1×512×64×64 → 1×4096×4096 | 17,179,869,184 | 16,777,216 | {} | 16,777,216 / 67,108,864 / 0 |
| 15 | mid.attention.softmax (softmax) | 1×4096×4096 → 1×4096×4096 | 0 | 50,327,552 | {"exp": 16777216, "max_comparisons": 16773120} | 67,108,864 / 67,108,864 / 0 |
| 16 | mid.attention.pv (attention_pv) | 1×4096×4096, 1×512×64×64 → 1×512×64×64 | 17,179,869,184 | 0 | {} | 75,497,472 / 8,388,608 / 0 |
| 17 | mid.attention.out (linear_1x1) | 1×512×64×64 → 1×512×64×64 | 2,147,483,648 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 1,050,624 |
| 18 | mid.attention.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 19 | mid.attention.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 20 | mid.residual1.norm1 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 21 | mid.residual1.silu1 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 22 | mid.residual1.conv1 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 23 | mid.residual1.norm2 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 24 | mid.residual1.silu2 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 25 | mid.residual1.conv2 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 26 | mid.residual1.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 27 | mid.residual1.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 28 | up0.residual0.norm1 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 29 | up0.residual0.silu1 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 30 | up0.residual0.conv1 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 31 | up0.residual0.norm2 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 32 | up0.residual0.silu2 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 33 | up0.residual0.conv2 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 34 | up0.residual0.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 35 | up0.residual0.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 36 | up0.residual1.norm1 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 37 | up0.residual1.silu1 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 38 | up0.residual1.conv1 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 39 | up0.residual1.norm2 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 40 | up0.residual1.silu2 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 41 | up0.residual1.conv2 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 42 | up0.residual1.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 43 | up0.residual1.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 44 | up0.residual2.norm1 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 45 | up0.residual2.silu1 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 46 | up0.residual2.conv1 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 47 | up0.residual2.norm2 (groupnorm) | 1×512×64×64 → 1×512×64×64 | 0 | 14,680,096 | {"rsqrt": 32} | 8,388,608 / 8,388,608 / 4,096 |
| 48 | up0.residual2.silu2 (silu) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {"sigmoid": 2097152} | 8,388,608 / 8,388,608 / 0 |
| 49 | up0.residual2.conv2 (conv2d) | 1×512×64×64 → 1×512×64×64 | 19,327,352,832 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 9,439,232 |
| 50 | up0.residual2.add (residual_add) | 1×512×64×64, 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 16,777,216 / 8,388,608 / 0 |
| 51 | up0.residual2.divide_by_one (residual_rescale) | 1×512×64×64 → 1×512×64×64 | 0 | 2,097,152 | {} | 8,388,608 / 8,388,608 / 0 |
| 52 | up0.nearest (nearest2d) | 1×512×64×64 → 1×512×128×128 | 0 | 0 | {} | 8,388,608 / 33,554,432 / 0 |
| 53 | up0.spatial_conv (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 54 | up1.residual0.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 55 | up1.residual0.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 56 | up1.residual0.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 57 | up1.residual0.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 58 | up1.residual0.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 59 | up1.residual0.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 60 | up1.residual0.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 67,108,864 / 33,554,432 / 0 |
| 61 | up1.residual0.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 0 |
| 62 | up1.residual1.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 63 | up1.residual1.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 64 | up1.residual1.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 65 | up1.residual1.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 66 | up1.residual1.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 67 | up1.residual1.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 68 | up1.residual1.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 67,108,864 / 33,554,432 / 0 |
| 69 | up1.residual1.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 0 |
| 70 | up1.residual2.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 71 | up1.residual2.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 72 | up1.residual2.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 73 | up1.residual2.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 33,554,432 / 33,554,432 / 4,096 |
| 74 | up1.residual2.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 33,554,432 / 33,554,432 / 0 |
| 75 | up1.residual2.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 9,439,232 |
| 76 | up1.residual2.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 67,108,864 / 33,554,432 / 0 |
| 77 | up1.residual2.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 33,554,432 / 0 |
| 78 | up1.nearest (nearest2d) | 1×512×128×128 → 1×512×256×256 | 0 | 0 | {} | 33,554,432 / 134,217,728 / 0 |
| 79 | up1.spatial_conv (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 9,439,232 |
| 80 | up2.residual0.norm1 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 4,096 |
| 81 | up2.residual0.silu1 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 82 | up2.residual0.conv1 (conv2d) | 1×512×256×256 → 1×256×256×256 | 154,618,822,656 | 16,777,216 | {} | 134,217,728 / 67,108,864 / 4,719,616 |
| 83 | up2.residual0.norm2 (groupnorm) | 1×256×256×256 → 1×256×256×256 | 0 | 117,440,544 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 84 | up2.residual0.silu2 (silu) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {"sigmoid": 16777216} | 67,108,864 / 67,108,864 / 0 |
| 85 | up2.residual0.conv2 (conv2d) | 1×256×256×256 → 1×256×256×256 | 77,309,411,328 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 2,360,320 |
| 86 | up2.residual0.shortcut (conv2d) | 1×512×256×256 → 1×256×256×256 | 17,179,869,184 | 16,777,216 | {} | 134,217,728 / 67,108,864 / 525,312 |
| 87 | up2.residual0.add (residual_add) | 1×256×256×256, 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 134,217,728 / 67,108,864 / 0 |
| 88 | up2.residual0.divide_by_one (residual_rescale) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 0 |
| 89 | up2.residual1.norm1 (groupnorm) | 1×256×256×256 → 1×256×256×256 | 0 | 117,440,544 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 90 | up2.residual1.silu1 (silu) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {"sigmoid": 16777216} | 67,108,864 / 67,108,864 / 0 |
| 91 | up2.residual1.conv1 (conv2d) | 1×256×256×256 → 1×256×256×256 | 77,309,411,328 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 2,360,320 |
| 92 | up2.residual1.norm2 (groupnorm) | 1×256×256×256 → 1×256×256×256 | 0 | 117,440,544 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 93 | up2.residual1.silu2 (silu) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {"sigmoid": 16777216} | 67,108,864 / 67,108,864 / 0 |
| 94 | up2.residual1.conv2 (conv2d) | 1×256×256×256 → 1×256×256×256 | 77,309,411,328 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 2,360,320 |
| 95 | up2.residual1.add (residual_add) | 1×256×256×256, 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 134,217,728 / 67,108,864 / 0 |
| 96 | up2.residual1.divide_by_one (residual_rescale) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 0 |
| 97 | up2.residual2.norm1 (groupnorm) | 1×256×256×256 → 1×256×256×256 | 0 | 117,440,544 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 98 | up2.residual2.silu1 (silu) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {"sigmoid": 16777216} | 67,108,864 / 67,108,864 / 0 |
| 99 | up2.residual2.conv1 (conv2d) | 1×256×256×256 → 1×256×256×256 | 77,309,411,328 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 2,360,320 |
| 100 | up2.residual2.norm2 (groupnorm) | 1×256×256×256 → 1×256×256×256 | 0 | 117,440,544 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 101 | up2.residual2.silu2 (silu) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {"sigmoid": 16777216} | 67,108,864 / 67,108,864 / 0 |
| 102 | up2.residual2.conv2 (conv2d) | 1×256×256×256 → 1×256×256×256 | 77,309,411,328 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 2,360,320 |
| 103 | up2.residual2.add (residual_add) | 1×256×256×256, 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 134,217,728 / 67,108,864 / 0 |
| 104 | up2.residual2.divide_by_one (residual_rescale) | 1×256×256×256 → 1×256×256×256 | 0 | 16,777,216 | {} | 67,108,864 / 67,108,864 / 0 |
| 105 | up2.nearest (nearest2d) | 1×256×256×256 → 1×256×512×512 | 0 | 0 | {} | 67,108,864 / 268,435,456 / 0 |
| 106 | up2.spatial_conv (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 268,435,456 / 268,435,456 / 2,360,320 |
| 107 | up3.residual0.norm1 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 2,048 |
| 108 | up3.residual0.silu1 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 268,435,456 / 268,435,456 / 0 |
| 109 | up3.residual0.conv1 (conv2d) | 1×256×512×512 → 1×128×512×512 | 154,618,822,656 | 33,554,432 | {} | 268,435,456 / 134,217,728 / 1,180,160 |
| 110 | up3.residual0.norm2 (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 111 | up3.residual0.silu2 (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 112 | up3.residual0.conv2 (conv2d) | 1×128×512×512 → 1×128×512×512 | 77,309,411,328 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 590,336 |
| 113 | up3.residual0.shortcut (conv2d) | 1×256×512×512 → 1×128×512×512 | 17,179,869,184 | 33,554,432 | {} | 268,435,456 / 134,217,728 / 131,584 |
| 114 | up3.residual0.add (residual_add) | 1×128×512×512, 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 268,435,456 / 134,217,728 / 0 |
| 115 | up3.residual0.divide_by_one (residual_rescale) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 0 |
| 116 | up3.residual1.norm1 (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 117 | up3.residual1.silu1 (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 118 | up3.residual1.conv1 (conv2d) | 1×128×512×512 → 1×128×512×512 | 77,309,411,328 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 590,336 |
| 119 | up3.residual1.norm2 (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 120 | up3.residual1.silu2 (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 121 | up3.residual1.conv2 (conv2d) | 1×128×512×512 → 1×128×512×512 | 77,309,411,328 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 590,336 |
| 122 | up3.residual1.add (residual_add) | 1×128×512×512, 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 268,435,456 / 134,217,728 / 0 |
| 123 | up3.residual1.divide_by_one (residual_rescale) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 0 |
| 124 | up3.residual2.norm1 (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 125 | up3.residual2.silu1 (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 126 | up3.residual2.conv1 (conv2d) | 1×128×512×512 → 1×128×512×512 | 77,309,411,328 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 590,336 |
| 127 | up3.residual2.norm2 (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 128 | up3.residual2.silu2 (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 129 | up3.residual2.conv2 (conv2d) | 1×128×512×512 → 1×128×512×512 | 77,309,411,328 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 590,336 |
| 130 | up3.residual2.add (residual_add) | 1×128×512×512, 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 268,435,456 / 134,217,728 / 0 |
| 131 | up3.residual2.divide_by_one (residual_rescale) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {} | 134,217,728 / 134,217,728 / 0 |
| 132 | decoder.output_norm (groupnorm) | 1×128×512×512 → 1×128×512×512 | 0 | 234,881,056 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 133 | decoder.output_silu (silu) | 1×128×512×512 → 1×128×512×512 | 0 | 33,554,432 | {"sigmoid": 33554432} | 134,217,728 / 134,217,728 / 0 |
| 134 | decoder.output (conv2d) | 1×128×512×512 → 1×3×512×512 | 1,811,939,328 | 786,432 | {} | 134,217,728 / 3,145,728 / 13,836 |

## 生命周期与复制接口

| 张量 | bytes | 产生步骤 | 最后使用步骤（含调用栈保留） |
|---|---:|---:|---:|
| latent | 524,288 | -1 | 135 |
| post_quant | 524,288 | 0 | 135 |
| decoder.input | 8,388,608 | 1 | 27 |
| mid.residual0.norm1 | 8,388,608 | 2 | 3 |
| mid.residual0.silu1 | 8,388,608 | 3 | 4 |
| mid.residual0.conv1 | 8,388,608 | 4 | 5 |
| mid.residual0.norm2 | 8,388,608 | 5 | 6 |
| mid.residual0.silu2 | 8,388,608 | 6 | 7 |
| mid.residual0.conv2 | 8,388,608 | 7 | 9 |
| mid.residual0.add | 8,388,608 | 8 | 9 |
| mid.residual0.divide_by_one | 8,388,608 | 9 | 19 |
| mid.attention.norm | 8,388,608 | 10 | 19 |
| mid.attention.q | 8,388,608 | 11 | 19 |
| mid.attention.k | 8,388,608 | 12 | 19 |
| mid.attention.v | 8,388,608 | 13 | 19 |
| mid.attention.qk | 67,108,864 | 14 | 15 |
| mid.attention.beta0_scratch | 67,108,864 | 14 | 14 |
| mid.attention.softmax | 67,108,864 | 15 | 19 |
| mid.attention.pv | 8,388,608 | 16 | 17 |
| mid.attention.out | 8,388,608 | 17 | 18 |
| mid.attention.add | 8,388,608 | 18 | 19 |
| mid.attention.divide_by_one | 8,388,608 | 19 | 27 |
| mid.residual1.norm1 | 8,388,608 | 20 | 21 |
| mid.residual1.silu1 | 8,388,608 | 21 | 22 |
| mid.residual1.conv1 | 8,388,608 | 22 | 23 |
| mid.residual1.norm2 | 8,388,608 | 23 | 24 |
| mid.residual1.silu2 | 8,388,608 | 24 | 25 |
| mid.residual1.conv2 | 8,388,608 | 25 | 27 |
| mid.residual1.add | 8,388,608 | 26 | 27 |
| mid.residual1.divide_by_one | 8,388,608 | 27 | 53 |
| up0.residual0.norm1 | 8,388,608 | 28 | 29 |
| up0.residual0.silu1 | 8,388,608 | 29 | 30 |
| up0.residual0.conv1 | 8,388,608 | 30 | 31 |
| up0.residual0.norm2 | 8,388,608 | 31 | 32 |
| up0.residual0.silu2 | 8,388,608 | 32 | 33 |
| up0.residual0.conv2 | 8,388,608 | 33 | 35 |
| up0.residual0.add | 8,388,608 | 34 | 35 |
| up0.residual0.divide_by_one | 8,388,608 | 35 | 43 |
| up0.residual1.norm1 | 8,388,608 | 36 | 37 |
| up0.residual1.silu1 | 8,388,608 | 37 | 38 |
| up0.residual1.conv1 | 8,388,608 | 38 | 39 |
| up0.residual1.norm2 | 8,388,608 | 39 | 40 |
| up0.residual1.silu2 | 8,388,608 | 40 | 41 |
| up0.residual1.conv2 | 8,388,608 | 41 | 43 |
| up0.residual1.add | 8,388,608 | 42 | 43 |
| up0.residual1.divide_by_one | 8,388,608 | 43 | 51 |
| up0.residual2.norm1 | 8,388,608 | 44 | 45 |
| up0.residual2.silu1 | 8,388,608 | 45 | 46 |
| up0.residual2.conv1 | 8,388,608 | 46 | 47 |
| up0.residual2.norm2 | 8,388,608 | 47 | 48 |
| up0.residual2.silu2 | 8,388,608 | 48 | 49 |
| up0.residual2.conv2 | 8,388,608 | 49 | 51 |
| up0.residual2.add | 8,388,608 | 50 | 51 |
| up0.residual2.divide_by_one | 8,388,608 | 51 | 53 |
| up0.nearest | 33,554,432 | 52 | 53 |
| up0.spatial_conv | 33,554,432 | 53 | 79 |
| up1.residual0.norm1 | 33,554,432 | 54 | 55 |
| up1.residual0.silu1 | 33,554,432 | 55 | 56 |
| up1.residual0.conv1 | 33,554,432 | 56 | 57 |
| up1.residual0.norm2 | 33,554,432 | 57 | 58 |
| up1.residual0.silu2 | 33,554,432 | 58 | 59 |
| up1.residual0.conv2 | 33,554,432 | 59 | 61 |
| up1.residual0.add | 33,554,432 | 60 | 61 |
| up1.residual0.divide_by_one | 33,554,432 | 61 | 69 |
| up1.residual1.norm1 | 33,554,432 | 62 | 63 |
| up1.residual1.silu1 | 33,554,432 | 63 | 64 |
| up1.residual1.conv1 | 33,554,432 | 64 | 65 |
| up1.residual1.norm2 | 33,554,432 | 65 | 66 |
| up1.residual1.silu2 | 33,554,432 | 66 | 67 |
| up1.residual1.conv2 | 33,554,432 | 67 | 69 |
| up1.residual1.add | 33,554,432 | 68 | 69 |
| up1.residual1.divide_by_one | 33,554,432 | 69 | 77 |
| up1.residual2.norm1 | 33,554,432 | 70 | 71 |
| up1.residual2.silu1 | 33,554,432 | 71 | 72 |
| up1.residual2.conv1 | 33,554,432 | 72 | 73 |
| up1.residual2.norm2 | 33,554,432 | 73 | 74 |
| up1.residual2.silu2 | 33,554,432 | 74 | 75 |
| up1.residual2.conv2 | 33,554,432 | 75 | 77 |
| up1.residual2.add | 33,554,432 | 76 | 77 |
| up1.residual2.divide_by_one | 33,554,432 | 77 | 79 |
| up1.nearest | 134,217,728 | 78 | 79 |
| up1.spatial_conv | 134,217,728 | 79 | 106 |
| up2.residual0.norm1 | 134,217,728 | 80 | 81 |
| up2.residual0.silu1 | 134,217,728 | 81 | 82 |
| up2.residual0.conv1 | 67,108,864 | 82 | 83 |
| up2.residual0.norm2 | 67,108,864 | 83 | 84 |
| up2.residual0.silu2 | 67,108,864 | 84 | 85 |
| up2.residual0.conv2 | 67,108,864 | 85 | 88 |
| up2.residual0.shortcut | 67,108,864 | 86 | 88 |
| up2.residual0.add | 67,108,864 | 87 | 88 |
| up2.residual0.divide_by_one | 67,108,864 | 88 | 96 |
| up2.residual1.norm1 | 67,108,864 | 89 | 90 |
| up2.residual1.silu1 | 67,108,864 | 90 | 91 |
| up2.residual1.conv1 | 67,108,864 | 91 | 92 |
| up2.residual1.norm2 | 67,108,864 | 92 | 93 |
| up2.residual1.silu2 | 67,108,864 | 93 | 94 |
| up2.residual1.conv2 | 67,108,864 | 94 | 96 |
| up2.residual1.add | 67,108,864 | 95 | 96 |
| up2.residual1.divide_by_one | 67,108,864 | 96 | 104 |
| up2.residual2.norm1 | 67,108,864 | 97 | 98 |
| up2.residual2.silu1 | 67,108,864 | 98 | 99 |
| up2.residual2.conv1 | 67,108,864 | 99 | 100 |
| up2.residual2.norm2 | 67,108,864 | 100 | 101 |
| up2.residual2.silu2 | 67,108,864 | 101 | 102 |
| up2.residual2.conv2 | 67,108,864 | 102 | 104 |
| up2.residual2.add | 67,108,864 | 103 | 104 |
| up2.residual2.divide_by_one | 67,108,864 | 104 | 106 |
| up2.nearest | 268,435,456 | 105 | 106 |
| up2.spatial_conv | 268,435,456 | 106 | 131 |
| up3.residual0.norm1 | 268,435,456 | 107 | 108 |
| up3.residual0.silu1 | 268,435,456 | 108 | 109 |
| up3.residual0.conv1 | 134,217,728 | 109 | 110 |
| up3.residual0.norm2 | 134,217,728 | 110 | 111 |
| up3.residual0.silu2 | 134,217,728 | 111 | 112 |
| up3.residual0.conv2 | 134,217,728 | 112 | 115 |
| up3.residual0.shortcut | 134,217,728 | 113 | 115 |
| up3.residual0.add | 134,217,728 | 114 | 115 |
| up3.residual0.divide_by_one | 134,217,728 | 115 | 123 |
| up3.residual1.norm1 | 134,217,728 | 116 | 117 |
| up3.residual1.silu1 | 134,217,728 | 117 | 118 |
| up3.residual1.conv1 | 134,217,728 | 118 | 119 |
| up3.residual1.norm2 | 134,217,728 | 119 | 120 |
| up3.residual1.silu2 | 134,217,728 | 120 | 121 |
| up3.residual1.conv2 | 134,217,728 | 121 | 123 |
| up3.residual1.add | 134,217,728 | 122 | 123 |
| up3.residual1.divide_by_one | 134,217,728 | 123 | 131 |
| up3.residual2.norm1 | 134,217,728 | 124 | 125 |
| up3.residual2.silu1 | 134,217,728 | 125 | 126 |
| up3.residual2.conv1 | 134,217,728 | 126 | 127 |
| up3.residual2.norm2 | 134,217,728 | 127 | 128 |
| up3.residual2.silu2 | 134,217,728 | 128 | 129 |
| up3.residual2.conv2 | 134,217,728 | 129 | 131 |
| up3.residual2.add | 134,217,728 | 130 | 131 |
| up3.residual2.divide_by_one | 134,217,728 | 131 | 132 |
| decoder.output_norm | 134,217,728 | 132 | 133 |
| decoder.output_silu | 134,217,728 | 133 | 134 |
| decoder.output | 3,145,728 | 134 | 135 |

| 上采样阶段 | 输入 bytes | contiguous 分支触发 | 实体复制 bytes |
|---:|---:|---|---:|
| 0 | 8,388,608 | False | 0 |
| 1 | 33,554,432 | False | 0 |
| 2 | 67,108,864 | False | 0 |

持久 decode cache：0 bytes；返回后调用方输入与输出：3,670,016 bytes。

## 适用范围

- Already denormalized/unpatchified VAE latent only: no DiT, BN inversion, latent unpacking, encoder, tokenizer, image postprocess or image file bytes.
- All decoder Conv2d/Linear/GN-affine weights enumerated, not entire AutoencoderKLFlux2 weights; no checkpoint-header parameter verification claimed.
- No slicing, tiling, checkpointing, training or offload. Dtype explicit; force_upcast config alone does not execute an FP32 conversion.
- PyTorch >=2.1 nearest BF16 path. Upsample contiguous branches expose input sizes and unknown materialized copy bytes when triggered; named-boundary peak excludes these copies and conditional budget is unavailable until layout is specified.
- Residual division by1 is retained. Default SDPA is noncausal one head; primitive algorithm and workspace unknown. Eager branch materializes scores for comparison.
- Boundary lifetime graph includes named tensor outputs and explicit caller/local holds; kernel-internal temporaries, allocator reuse/alignment and autograd are not inferred. Conditional budget is only with caller-supplied workspace, never measured peak.
- GroupNorm two-pass math is counted with affine and biased variance; reduction kernel algorithm unspecified. SiLU/softmax special operations are separate from matrix FLOPs.

## 固定来源

- [sources/image-generation/autoencoder_kl_flux2.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/autoencoder_kl_flux2.py)；SHA256 `7d9a976c1e4f42615e8c422f1643d86b49c4339221bd04b67f518b718ebd6c2d`。
- [sources/image-generation/attention_processor.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/attention_processor.py)；SHA256 `7158a23bff0ce5bb1c03d66e2441dfd8d169b3598b2d494d32c6f88a3301ea01`。
- [sources/image-generation/vae.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/autoencoders/vae.py)；SHA256 `8e6abad3bd7b7806dd9c6c451b2438641ef728d7884e6bfed37b867f719b98fc`。
- [sources/image-generation/unet_2d_blocks.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/unets/unet_2d_blocks.py)；SHA256 `545d158c9d98fb8971c501303117fd3e32d27ae28506b89005c65548404f7437`。
- [sources/image-generation/resnet.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/resnet.py)；SHA256 `329975c03ddf3baa5528ace0e2be62f4224746700be4fda57dcbabb209569e9c`。
- [sources/image-generation/upsampling.py](https://raw.githubusercontent.com/huggingface/diffusers/040c7cde626504d14caf63b13b8b25b6a9f62120/src/diffusers/models/upsampling.py)；SHA256 `d6410c71fa01c5363c6130784a709eb13b5be7e6b401dba7fa930f59b5e5559d`。
- [configs/models/flux2-klein-4b/vae/config.json](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/vae/config.json)；SHA256 `0d6dfb69ae95a5e2ac9836284bbb63d8b38ce67b25ba2dff380752b2a10ab948`。
