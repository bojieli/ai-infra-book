# FLUX2 Klein VAE 解码算子账

输入 `[1, 32, 128, 128]` → RGB `[1, 3, 1024, 1024]`；dtype=bf16，attention=eager。

解码权重 49,620,259 参数 / 99,240,518 bytes；dense matrix/conv 10,474,653,483,008 FLOPs，有效非 padding 10,442,021,800,960 FLOPs，标量算术 19,448,447,936。特殊函数另列。

命名张量边界峰值 2,250,244,096 bytes，位于 `mid.attention.softmax`。条件权重+边界+指定 workspace：未知 / 未提供 bytes。

以下接口 bytes 不是 HBM 实测；边界峰值不含 primitive 内部临时量、未知 layout 复制和分配器开销。实际运行峰值未知，不能据此直接宣称设备可运行。

| 步 | 算子 | 输入形状 → 输出形状 | matrix FLOPs | scalar | 特殊函数 | 读 / 写 / 权重 bytes |
|---:|---|---|---:|---:|---|---|
| 0 | post_quant (conv2d) | 1×32×128×128 → 1×32×128×128 | 33,554,432 | 524,288 | {} | 1,048,576 / 1,048,576 / 2,112 |
| 1 | decoder.input (conv2d) | 1×32×128×128 → 1×512×128×128 | 4,831,838,208 | 8,388,608 | {} | 1,048,576 / 16,777,216 / 295,936 |
| 2 | mid.residual0.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 3 | mid.residual0.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 4 | mid.residual0.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 5 | mid.residual0.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 6 | mid.residual0.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 7 | mid.residual0.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 8 | mid.residual0.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 9 | mid.residual0.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 10 | mid.attention.norm (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 11 | mid.attention.q (linear_1x1) | 1×512×128×128 → 1×512×128×128 | 8,589,934,592 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 525,312 |
| 12 | mid.attention.k (linear_1x1) | 1×512×128×128 → 1×512×128×128 | 8,589,934,592 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 525,312 |
| 13 | mid.attention.v (linear_1x1) | 1×512×128×128 → 1×512×128×128 | 8,589,934,592 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 525,312 |
| 14 | mid.attention.qk (attention_qk) | 1×512×128×128, 1×512×128×128 → 1×16384×16384 | 274,877,906,944 | 268,435,456 | {} | 33,554,432 / 536,870,912 / 0 |
| 15 | mid.attention.upcast (cast) | 1×16384×16384 → 1×16384×16384 | 0 | 0 | {} | 536,870,912 / 1,073,741,824 / 0 |
| 16 | mid.attention.softmax (softmax) | 1×16384×16384 → 1×16384×16384 | 0 | 805,289,984 | {"exp": 268435456, "max_comparisons": 268419072} | 1,073,741,824 / 1,073,741,824 / 0 |
| 17 | mid.attention.probability_cast (cast) | 1×16384×16384 → 1×16384×16384 | 0 | 0 | {} | 1,073,741,824 / 536,870,912 / 0 |
| 18 | mid.attention.pv (attention_pv) | 1×16384×16384, 1×512×128×128 → 1×512×128×128 | 274,877,906,944 | 0 | {} | 553,648,128 / 16,777,216 / 0 |
| 19 | mid.attention.out (linear_1x1) | 1×512×128×128 → 1×512×128×128 | 8,589,934,592 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 525,312 |
| 20 | mid.attention.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 21 | mid.attention.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 22 | mid.residual1.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 23 | mid.residual1.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 24 | mid.residual1.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 25 | mid.residual1.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 26 | mid.residual1.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 27 | mid.residual1.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 28 | mid.residual1.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 29 | mid.residual1.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 30 | up0.residual0.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 31 | up0.residual0.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 32 | up0.residual0.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 33 | up0.residual0.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 34 | up0.residual0.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 35 | up0.residual0.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 36 | up0.residual0.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 37 | up0.residual0.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 38 | up0.residual1.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 39 | up0.residual1.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 40 | up0.residual1.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 41 | up0.residual1.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 42 | up0.residual1.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 43 | up0.residual1.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 44 | up0.residual1.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 45 | up0.residual1.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 46 | up0.residual2.norm1 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 47 | up0.residual2.silu1 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 48 | up0.residual2.conv1 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 49 | up0.residual2.norm2 (groupnorm) | 1×512×128×128 → 1×512×128×128 | 0 | 58,720,288 | {"rsqrt": 32} | 16,777,216 / 16,777,216 / 2,048 |
| 50 | up0.residual2.silu2 (silu) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {"sigmoid": 8388608} | 16,777,216 / 16,777,216 / 0 |
| 51 | up0.residual2.conv2 (conv2d) | 1×512×128×128 → 1×512×128×128 | 77,309,411,328 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 4,719,616 |
| 52 | up0.residual2.add (residual_add) | 1×512×128×128, 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 33,554,432 / 16,777,216 / 0 |
| 53 | up0.residual2.divide_by_one (residual_rescale) | 1×512×128×128 → 1×512×128×128 | 0 | 8,388,608 | {} | 16,777,216 / 16,777,216 / 0 |
| 54 | up0.nearest (nearest2d) | 1×512×128×128 → 1×512×256×256 | 0 | 0 | {} | 16,777,216 / 67,108,864 / 0 |
| 55 | up0.spatial_conv (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 56 | up1.residual0.norm1 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 57 | up1.residual0.silu1 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 58 | up1.residual0.conv1 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 59 | up1.residual0.norm2 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 60 | up1.residual0.silu2 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 61 | up1.residual0.conv2 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 62 | up1.residual0.add (residual_add) | 1×512×256×256, 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 134,217,728 / 67,108,864 / 0 |
| 63 | up1.residual0.divide_by_one (residual_rescale) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 0 |
| 64 | up1.residual1.norm1 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 65 | up1.residual1.silu1 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 66 | up1.residual1.conv1 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 67 | up1.residual1.norm2 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 68 | up1.residual1.silu2 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 69 | up1.residual1.conv2 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 70 | up1.residual1.add (residual_add) | 1×512×256×256, 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 134,217,728 / 67,108,864 / 0 |
| 71 | up1.residual1.divide_by_one (residual_rescale) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 0 |
| 72 | up1.residual2.norm1 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 73 | up1.residual2.silu1 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 74 | up1.residual2.conv1 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 75 | up1.residual2.norm2 (groupnorm) | 1×512×256×256 → 1×512×256×256 | 0 | 234,881,056 | {"rsqrt": 32} | 67,108,864 / 67,108,864 / 2,048 |
| 76 | up1.residual2.silu2 (silu) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {"sigmoid": 33554432} | 67,108,864 / 67,108,864 / 0 |
| 77 | up1.residual2.conv2 (conv2d) | 1×512×256×256 → 1×512×256×256 | 309,237,645,312 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 4,719,616 |
| 78 | up1.residual2.add (residual_add) | 1×512×256×256, 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 134,217,728 / 67,108,864 / 0 |
| 79 | up1.residual2.divide_by_one (residual_rescale) | 1×512×256×256 → 1×512×256×256 | 0 | 33,554,432 | {} | 67,108,864 / 67,108,864 / 0 |
| 80 | up1.nearest (nearest2d) | 1×512×256×256 → 1×512×512×512 | 0 | 0 | {} | 67,108,864 / 268,435,456 / 0 |
| 81 | up1.spatial_conv (conv2d) | 1×512×512×512 → 1×512×512×512 | 1,236,950,581,248 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 4,719,616 |
| 82 | up2.residual0.norm1 (groupnorm) | 1×512×512×512 → 1×512×512×512 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 2,048 |
| 83 | up2.residual0.silu1 (silu) | 1×512×512×512 → 1×512×512×512 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 84 | up2.residual0.conv1 (conv2d) | 1×512×512×512 → 1×256×512×512 | 618,475,290,624 | 67,108,864 | {} | 268,435,456 / 134,217,728 / 2,359,808 |
| 85 | up2.residual0.norm2 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 86 | up2.residual0.silu2 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 134,217,728 / 134,217,728 / 0 |
| 87 | up2.residual0.conv2 (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 1,180,160 |
| 88 | up2.residual0.shortcut (conv2d) | 1×512×512×512 → 1×256×512×512 | 68,719,476,736 | 67,108,864 | {} | 268,435,456 / 134,217,728 / 262,656 |
| 89 | up2.residual0.add (residual_add) | 1×256×512×512, 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 268,435,456 / 134,217,728 / 0 |
| 90 | up2.residual0.divide_by_one (residual_rescale) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 0 |
| 91 | up2.residual1.norm1 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 92 | up2.residual1.silu1 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 134,217,728 / 134,217,728 / 0 |
| 93 | up2.residual1.conv1 (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 1,180,160 |
| 94 | up2.residual1.norm2 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 95 | up2.residual1.silu2 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 134,217,728 / 134,217,728 / 0 |
| 96 | up2.residual1.conv2 (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 1,180,160 |
| 97 | up2.residual1.add (residual_add) | 1×256×512×512, 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 268,435,456 / 134,217,728 / 0 |
| 98 | up2.residual1.divide_by_one (residual_rescale) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 0 |
| 99 | up2.residual2.norm1 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 100 | up2.residual2.silu1 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 134,217,728 / 134,217,728 / 0 |
| 101 | up2.residual2.conv1 (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 1,180,160 |
| 102 | up2.residual2.norm2 (groupnorm) | 1×256×512×512 → 1×256×512×512 | 0 | 469,762,080 | {"rsqrt": 32} | 134,217,728 / 134,217,728 / 1,024 |
| 103 | up2.residual2.silu2 (silu) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {"sigmoid": 67108864} | 134,217,728 / 134,217,728 / 0 |
| 104 | up2.residual2.conv2 (conv2d) | 1×256×512×512 → 1×256×512×512 | 309,237,645,312 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 1,180,160 |
| 105 | up2.residual2.add (residual_add) | 1×256×512×512, 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 268,435,456 / 134,217,728 / 0 |
| 106 | up2.residual2.divide_by_one (residual_rescale) | 1×256×512×512 → 1×256×512×512 | 0 | 67,108,864 | {} | 134,217,728 / 134,217,728 / 0 |
| 107 | up2.nearest (nearest2d) | 1×256×512×512 → 1×256×1024×1024 | 0 | 0 | {} | 134,217,728 / 536,870,912 / 0 |
| 108 | up2.spatial_conv (conv2d) | 1×256×1024×1024 → 1×256×1024×1024 | 1,236,950,581,248 | 268,435,456 | {} | 536,870,912 / 536,870,912 / 1,180,160 |
| 109 | up3.residual0.norm1 (groupnorm) | 1×256×1024×1024 → 1×256×1024×1024 | 0 | 1,879,048,224 | {"rsqrt": 32} | 536,870,912 / 536,870,912 / 1,024 |
| 110 | up3.residual0.silu1 (silu) | 1×256×1024×1024 → 1×256×1024×1024 | 0 | 268,435,456 | {"sigmoid": 268435456} | 536,870,912 / 536,870,912 / 0 |
| 111 | up3.residual0.conv1 (conv2d) | 1×256×1024×1024 → 1×128×1024×1024 | 618,475,290,624 | 134,217,728 | {} | 536,870,912 / 268,435,456 / 590,080 |
| 112 | up3.residual0.norm2 (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 113 | up3.residual0.silu2 (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 114 | up3.residual0.conv2 (conv2d) | 1×128×1024×1024 → 1×128×1024×1024 | 309,237,645,312 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 295,168 |
| 115 | up3.residual0.shortcut (conv2d) | 1×256×1024×1024 → 1×128×1024×1024 | 68,719,476,736 | 134,217,728 | {} | 536,870,912 / 268,435,456 / 65,792 |
| 116 | up3.residual0.add (residual_add) | 1×128×1024×1024, 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 536,870,912 / 268,435,456 / 0 |
| 117 | up3.residual0.divide_by_one (residual_rescale) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 0 |
| 118 | up3.residual1.norm1 (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 119 | up3.residual1.silu1 (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 120 | up3.residual1.conv1 (conv2d) | 1×128×1024×1024 → 1×128×1024×1024 | 309,237,645,312 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 295,168 |
| 121 | up3.residual1.norm2 (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 122 | up3.residual1.silu2 (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 123 | up3.residual1.conv2 (conv2d) | 1×128×1024×1024 → 1×128×1024×1024 | 309,237,645,312 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 295,168 |
| 124 | up3.residual1.add (residual_add) | 1×128×1024×1024, 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 536,870,912 / 268,435,456 / 0 |
| 125 | up3.residual1.divide_by_one (residual_rescale) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 0 |
| 126 | up3.residual2.norm1 (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 127 | up3.residual2.silu1 (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 128 | up3.residual2.conv1 (conv2d) | 1×128×1024×1024 → 1×128×1024×1024 | 309,237,645,312 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 295,168 |
| 129 | up3.residual2.norm2 (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 130 | up3.residual2.silu2 (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 131 | up3.residual2.conv2 (conv2d) | 1×128×1024×1024 → 1×128×1024×1024 | 309,237,645,312 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 295,168 |
| 132 | up3.residual2.add (residual_add) | 1×128×1024×1024, 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 536,870,912 / 268,435,456 / 0 |
| 133 | up3.residual2.divide_by_one (residual_rescale) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {} | 268,435,456 / 268,435,456 / 0 |
| 134 | decoder.output_norm (groupnorm) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 939,524,128 | {"rsqrt": 32} | 268,435,456 / 268,435,456 / 512 |
| 135 | decoder.output_silu (silu) | 1×128×1024×1024 → 1×128×1024×1024 | 0 | 134,217,728 | {"sigmoid": 134217728} | 268,435,456 / 268,435,456 / 0 |
| 136 | decoder.output (conv2d) | 1×128×1024×1024 → 1×3×1024×1024 | 7,247,757,312 | 3,145,728 | {} | 268,435,456 / 6,291,456 / 6,918 |

## 生命周期与复制接口

| 张量 | bytes | 产生步骤 | 最后使用步骤（含调用栈保留） |
|---|---:|---:|---:|
| latent | 1,048,576 | -1 | 137 |
| post_quant | 1,048,576 | 0 | 137 |
| decoder.input | 16,777,216 | 1 | 29 |
| mid.residual0.norm1 | 16,777,216 | 2 | 3 |
| mid.residual0.silu1 | 16,777,216 | 3 | 4 |
| mid.residual0.conv1 | 16,777,216 | 4 | 5 |
| mid.residual0.norm2 | 16,777,216 | 5 | 6 |
| mid.residual0.silu2 | 16,777,216 | 6 | 7 |
| mid.residual0.conv2 | 16,777,216 | 7 | 9 |
| mid.residual0.add | 16,777,216 | 8 | 9 |
| mid.residual0.divide_by_one | 16,777,216 | 9 | 21 |
| mid.attention.norm | 16,777,216 | 10 | 21 |
| mid.attention.q | 16,777,216 | 11 | 21 |
| mid.attention.k | 16,777,216 | 12 | 21 |
| mid.attention.v | 16,777,216 | 13 | 21 |
| mid.attention.qk | 536,870,912 | 14 | 15 |
| mid.attention.beta0_scratch | 536,870,912 | 14 | 14 |
| mid.attention.upcast | 1,073,741,824 | 15 | 16 |
| mid.attention.softmax | 1,073,741,824 | 16 | 17 |
| mid.attention.probability_cast | 536,870,912 | 17 | 21 |
| mid.attention.pv | 16,777,216 | 18 | 19 |
| mid.attention.out | 16,777,216 | 19 | 20 |
| mid.attention.add | 16,777,216 | 20 | 21 |
| mid.attention.divide_by_one | 16,777,216 | 21 | 29 |
| mid.residual1.norm1 | 16,777,216 | 22 | 23 |
| mid.residual1.silu1 | 16,777,216 | 23 | 24 |
| mid.residual1.conv1 | 16,777,216 | 24 | 25 |
| mid.residual1.norm2 | 16,777,216 | 25 | 26 |
| mid.residual1.silu2 | 16,777,216 | 26 | 27 |
| mid.residual1.conv2 | 16,777,216 | 27 | 29 |
| mid.residual1.add | 16,777,216 | 28 | 29 |
| mid.residual1.divide_by_one | 16,777,216 | 29 | 55 |
| up0.residual0.norm1 | 16,777,216 | 30 | 31 |
| up0.residual0.silu1 | 16,777,216 | 31 | 32 |
| up0.residual0.conv1 | 16,777,216 | 32 | 33 |
| up0.residual0.norm2 | 16,777,216 | 33 | 34 |
| up0.residual0.silu2 | 16,777,216 | 34 | 35 |
| up0.residual0.conv2 | 16,777,216 | 35 | 37 |
| up0.residual0.add | 16,777,216 | 36 | 37 |
| up0.residual0.divide_by_one | 16,777,216 | 37 | 45 |
| up0.residual1.norm1 | 16,777,216 | 38 | 39 |
| up0.residual1.silu1 | 16,777,216 | 39 | 40 |
| up0.residual1.conv1 | 16,777,216 | 40 | 41 |
| up0.residual1.norm2 | 16,777,216 | 41 | 42 |
| up0.residual1.silu2 | 16,777,216 | 42 | 43 |
| up0.residual1.conv2 | 16,777,216 | 43 | 45 |
| up0.residual1.add | 16,777,216 | 44 | 45 |
| up0.residual1.divide_by_one | 16,777,216 | 45 | 53 |
| up0.residual2.norm1 | 16,777,216 | 46 | 47 |
| up0.residual2.silu1 | 16,777,216 | 47 | 48 |
| up0.residual2.conv1 | 16,777,216 | 48 | 49 |
| up0.residual2.norm2 | 16,777,216 | 49 | 50 |
| up0.residual2.silu2 | 16,777,216 | 50 | 51 |
| up0.residual2.conv2 | 16,777,216 | 51 | 53 |
| up0.residual2.add | 16,777,216 | 52 | 53 |
| up0.residual2.divide_by_one | 16,777,216 | 53 | 55 |
| up0.nearest | 67,108,864 | 54 | 55 |
| up0.spatial_conv | 67,108,864 | 55 | 81 |
| up1.residual0.norm1 | 67,108,864 | 56 | 57 |
| up1.residual0.silu1 | 67,108,864 | 57 | 58 |
| up1.residual0.conv1 | 67,108,864 | 58 | 59 |
| up1.residual0.norm2 | 67,108,864 | 59 | 60 |
| up1.residual0.silu2 | 67,108,864 | 60 | 61 |
| up1.residual0.conv2 | 67,108,864 | 61 | 63 |
| up1.residual0.add | 67,108,864 | 62 | 63 |
| up1.residual0.divide_by_one | 67,108,864 | 63 | 71 |
| up1.residual1.norm1 | 67,108,864 | 64 | 65 |
| up1.residual1.silu1 | 67,108,864 | 65 | 66 |
| up1.residual1.conv1 | 67,108,864 | 66 | 67 |
| up1.residual1.norm2 | 67,108,864 | 67 | 68 |
| up1.residual1.silu2 | 67,108,864 | 68 | 69 |
| up1.residual1.conv2 | 67,108,864 | 69 | 71 |
| up1.residual1.add | 67,108,864 | 70 | 71 |
| up1.residual1.divide_by_one | 67,108,864 | 71 | 79 |
| up1.residual2.norm1 | 67,108,864 | 72 | 73 |
| up1.residual2.silu1 | 67,108,864 | 73 | 74 |
| up1.residual2.conv1 | 67,108,864 | 74 | 75 |
| up1.residual2.norm2 | 67,108,864 | 75 | 76 |
| up1.residual2.silu2 | 67,108,864 | 76 | 77 |
| up1.residual2.conv2 | 67,108,864 | 77 | 79 |
| up1.residual2.add | 67,108,864 | 78 | 79 |
| up1.residual2.divide_by_one | 67,108,864 | 79 | 81 |
| up1.nearest | 268,435,456 | 80 | 81 |
| up1.spatial_conv | 268,435,456 | 81 | 108 |
| up2.residual0.norm1 | 268,435,456 | 82 | 83 |
| up2.residual0.silu1 | 268,435,456 | 83 | 84 |
| up2.residual0.conv1 | 134,217,728 | 84 | 85 |
| up2.residual0.norm2 | 134,217,728 | 85 | 86 |
| up2.residual0.silu2 | 134,217,728 | 86 | 87 |
| up2.residual0.conv2 | 134,217,728 | 87 | 90 |
| up2.residual0.shortcut | 134,217,728 | 88 | 90 |
| up2.residual0.add | 134,217,728 | 89 | 90 |
| up2.residual0.divide_by_one | 134,217,728 | 90 | 98 |
| up2.residual1.norm1 | 134,217,728 | 91 | 92 |
| up2.residual1.silu1 | 134,217,728 | 92 | 93 |
| up2.residual1.conv1 | 134,217,728 | 93 | 94 |
| up2.residual1.norm2 | 134,217,728 | 94 | 95 |
| up2.residual1.silu2 | 134,217,728 | 95 | 96 |
| up2.residual1.conv2 | 134,217,728 | 96 | 98 |
| up2.residual1.add | 134,217,728 | 97 | 98 |
| up2.residual1.divide_by_one | 134,217,728 | 98 | 106 |
| up2.residual2.norm1 | 134,217,728 | 99 | 100 |
| up2.residual2.silu1 | 134,217,728 | 100 | 101 |
| up2.residual2.conv1 | 134,217,728 | 101 | 102 |
| up2.residual2.norm2 | 134,217,728 | 102 | 103 |
| up2.residual2.silu2 | 134,217,728 | 103 | 104 |
| up2.residual2.conv2 | 134,217,728 | 104 | 106 |
| up2.residual2.add | 134,217,728 | 105 | 106 |
| up2.residual2.divide_by_one | 134,217,728 | 106 | 108 |
| up2.nearest | 536,870,912 | 107 | 108 |
| up2.spatial_conv | 536,870,912 | 108 | 133 |
| up3.residual0.norm1 | 536,870,912 | 109 | 110 |
| up3.residual0.silu1 | 536,870,912 | 110 | 111 |
| up3.residual0.conv1 | 268,435,456 | 111 | 112 |
| up3.residual0.norm2 | 268,435,456 | 112 | 113 |
| up3.residual0.silu2 | 268,435,456 | 113 | 114 |
| up3.residual0.conv2 | 268,435,456 | 114 | 117 |
| up3.residual0.shortcut | 268,435,456 | 115 | 117 |
| up3.residual0.add | 268,435,456 | 116 | 117 |
| up3.residual0.divide_by_one | 268,435,456 | 117 | 125 |
| up3.residual1.norm1 | 268,435,456 | 118 | 119 |
| up3.residual1.silu1 | 268,435,456 | 119 | 120 |
| up3.residual1.conv1 | 268,435,456 | 120 | 121 |
| up3.residual1.norm2 | 268,435,456 | 121 | 122 |
| up3.residual1.silu2 | 268,435,456 | 122 | 123 |
| up3.residual1.conv2 | 268,435,456 | 123 | 125 |
| up3.residual1.add | 268,435,456 | 124 | 125 |
| up3.residual1.divide_by_one | 268,435,456 | 125 | 133 |
| up3.residual2.norm1 | 268,435,456 | 126 | 127 |
| up3.residual2.silu1 | 268,435,456 | 127 | 128 |
| up3.residual2.conv1 | 268,435,456 | 128 | 129 |
| up3.residual2.norm2 | 268,435,456 | 129 | 130 |
| up3.residual2.silu2 | 268,435,456 | 130 | 131 |
| up3.residual2.conv2 | 268,435,456 | 131 | 133 |
| up3.residual2.add | 268,435,456 | 132 | 133 |
| up3.residual2.divide_by_one | 268,435,456 | 133 | 134 |
| decoder.output_norm | 268,435,456 | 134 | 135 |
| decoder.output_silu | 268,435,456 | 135 | 136 |
| decoder.output | 6,291,456 | 136 | 137 |

| 上采样阶段 | 输入 bytes | contiguous 分支触发 | 实体复制 bytes |
|---:|---:|---|---:|
| 0 | 16,777,216 | False | 0 |
| 1 | 67,108,864 | False | 0 |
| 2 | 134,217,728 | False | 0 |

持久 decode cache：0 bytes；返回后调用方输入与输出：7,340,032 bytes。

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
