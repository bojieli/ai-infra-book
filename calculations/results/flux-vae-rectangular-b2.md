# FLUX2 Klein VAE 解码算子账

输入 `[2, 32, 64, 96]` → RGB `[2, 3, 512, 768]`；dtype=bf16，attention=sdpa。

解码权重 49,620,259 参数 / 99,240,518 bytes；dense matrix/conv 7,598,292,074,496 FLOPs，有效非 padding 7,557,534,717,952 FLOPs，标量算术 14,083,020,672。特殊函数另列。

命名张量边界峰值 1,209,532,416 bytes，位于 `up3.residual0.silu1`。条件权重+边界+指定 workspace：1,845,643,846 bytes。

以下接口 bytes 不是 HBM 实测；边界峰值不含 primitive 内部临时量、未知 layout 复制和分配器开销。实际运行峰值未知，不能据此直接宣称设备可运行。

| 步 | 算子 | 输入形状 → 输出形状 | matrix FLOPs | scalar | 特殊函数 | 读 / 写 / 权重 bytes |
|---:|---|---|---:|---:|---|---|
| 0 | post_quant (conv2d) | 2×32×64×96 → 2×32×64×96 | 25,165,824 | 393,216 | {} | 786,432 / 786,432 / 2,112 |
| 1 | decoder.input (conv2d) | 2×32×64×96 → 2×512×64×96 | 3,623,878,656 | 6,291,456 | {} | 786,432 / 12,582,912 / 295,936 |
| 2 | mid.residual0.norm1 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 3 | mid.residual0.silu1 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 4 | mid.residual0.conv1 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 5 | mid.residual0.norm2 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 6 | mid.residual0.silu2 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 7 | mid.residual0.conv2 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 8 | mid.residual0.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 9 | mid.residual0.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 10 | mid.attention.norm (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 11 | mid.attention.q (linear_1x1) | 2×512×64×96 → 2×512×64×96 | 6,442,450,944 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 525,312 |
| 12 | mid.attention.k (linear_1x1) | 2×512×64×96 → 2×512×64×96 | 6,442,450,944 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 525,312 |
| 13 | mid.attention.v (linear_1x1) | 2×512×64×96 → 2×512×64×96 | 6,442,450,944 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 525,312 |
| 14 | mid.attention.sdpa (sdpa) | 2×512×64×96, 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 154,618,822,656 | 301,977,600 | {"exp": 75497472, "max_comparisons": 75485184} | 37,748,736 / 12,582,912 / 0 |
| 15 | mid.attention.out (linear_1x1) | 2×512×64×96 → 2×512×64×96 | 6,442,450,944 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 525,312 |
| 16 | mid.attention.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 17 | mid.attention.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 18 | mid.residual1.norm1 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 19 | mid.residual1.silu1 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 20 | mid.residual1.conv1 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 21 | mid.residual1.norm2 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 22 | mid.residual1.silu2 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 23 | mid.residual1.conv2 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 24 | mid.residual1.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 25 | mid.residual1.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 26 | up0.residual0.norm1 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 27 | up0.residual0.silu1 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 28 | up0.residual0.conv1 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 29 | up0.residual0.norm2 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 30 | up0.residual0.silu2 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 31 | up0.residual0.conv2 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 32 | up0.residual0.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 33 | up0.residual0.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 34 | up0.residual1.norm1 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 35 | up0.residual1.silu1 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 36 | up0.residual1.conv1 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 37 | up0.residual1.norm2 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 38 | up0.residual1.silu2 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 39 | up0.residual1.conv2 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 40 | up0.residual1.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 41 | up0.residual1.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 42 | up0.residual2.norm1 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 43 | up0.residual2.silu1 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 44 | up0.residual2.conv1 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 45 | up0.residual2.norm2 (groupnorm) | 2×512×64×96 → 2×512×64×96 | 0 | 44,040,256 | {"rsqrt": 64} | 12,582,912 / 12,582,912 / 2,048 |
| 46 | up0.residual2.silu2 (silu) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {"sigmoid": 6291456} | 12,582,912 / 12,582,912 / 0 |
| 47 | up0.residual2.conv2 (conv2d) | 2×512×64×96 → 2×512×64×96 | 57,982,058,496 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 4,719,616 |
| 48 | up0.residual2.add (residual_add) | 2×512×64×96, 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 25,165,824 / 12,582,912 / 0 |
| 49 | up0.residual2.divide_by_one (residual_rescale) | 2×512×64×96 → 2×512×64×96 | 0 | 6,291,456 | {} | 12,582,912 / 12,582,912 / 0 |
| 50 | up0.nearest (nearest2d) | 2×512×64×96 → 2×512×128×192 | 0 | 0 | {} | 12,582,912 / 50,331,648 / 0 |
| 51 | up0.spatial_conv (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 52 | up1.residual0.norm1 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 53 | up1.residual0.silu1 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 54 | up1.residual0.conv1 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 55 | up1.residual0.norm2 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 56 | up1.residual0.silu2 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 57 | up1.residual0.conv2 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 58 | up1.residual0.add (residual_add) | 2×512×128×192, 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 100,663,296 / 50,331,648 / 0 |
| 59 | up1.residual0.divide_by_one (residual_rescale) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 0 |
| 60 | up1.residual1.norm1 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 61 | up1.residual1.silu1 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 62 | up1.residual1.conv1 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 63 | up1.residual1.norm2 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 64 | up1.residual1.silu2 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 65 | up1.residual1.conv2 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 66 | up1.residual1.add (residual_add) | 2×512×128×192, 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 100,663,296 / 50,331,648 / 0 |
| 67 | up1.residual1.divide_by_one (residual_rescale) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 0 |
| 68 | up1.residual2.norm1 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 69 | up1.residual2.silu1 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 70 | up1.residual2.conv1 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 71 | up1.residual2.norm2 (groupnorm) | 2×512×128×192 → 2×512×128×192 | 0 | 176,160,832 | {"rsqrt": 64} | 50,331,648 / 50,331,648 / 2,048 |
| 72 | up1.residual2.silu2 (silu) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {"sigmoid": 25165824} | 50,331,648 / 50,331,648 / 0 |
| 73 | up1.residual2.conv2 (conv2d) | 2×512×128×192 → 2×512×128×192 | 231,928,233,984 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 4,719,616 |
| 74 | up1.residual2.add (residual_add) | 2×512×128×192, 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 100,663,296 / 50,331,648 / 0 |
| 75 | up1.residual2.divide_by_one (residual_rescale) | 2×512×128×192 → 2×512×128×192 | 0 | 25,165,824 | {} | 50,331,648 / 50,331,648 / 0 |
| 76 | up1.nearest (nearest2d) | 2×512×128×192 → 2×512×256×384 | 0 | 0 | {} | 50,331,648 / 201,326,592 / 0 |
| 77 | up1.spatial_conv (conv2d) | 2×512×256×384 → 2×512×256×384 | 927,712,935,936 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 4,719,616 |
| 78 | up2.residual0.norm1 (groupnorm) | 2×512×256×384 → 2×512×256×384 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 2,048 |
| 79 | up2.residual0.silu1 (silu) | 2×512×256×384 → 2×512×256×384 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 80 | up2.residual0.conv1 (conv2d) | 2×512×256×384 → 2×256×256×384 | 463,856,467,968 | 50,331,648 | {} | 201,326,592 / 100,663,296 / 2,359,808 |
| 81 | up2.residual0.norm2 (groupnorm) | 2×256×256×384 → 2×256×256×384 | 0 | 352,321,600 | {"rsqrt": 64} | 100,663,296 / 100,663,296 / 1,024 |
| 82 | up2.residual0.silu2 (silu) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {"sigmoid": 50331648} | 100,663,296 / 100,663,296 / 0 |
| 83 | up2.residual0.conv2 (conv2d) | 2×256×256×384 → 2×256×256×384 | 231,928,233,984 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 1,180,160 |
| 84 | up2.residual0.shortcut (conv2d) | 2×512×256×384 → 2×256×256×384 | 51,539,607,552 | 50,331,648 | {} | 201,326,592 / 100,663,296 / 262,656 |
| 85 | up2.residual0.add (residual_add) | 2×256×256×384, 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 201,326,592 / 100,663,296 / 0 |
| 86 | up2.residual0.divide_by_one (residual_rescale) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 0 |
| 87 | up2.residual1.norm1 (groupnorm) | 2×256×256×384 → 2×256×256×384 | 0 | 352,321,600 | {"rsqrt": 64} | 100,663,296 / 100,663,296 / 1,024 |
| 88 | up2.residual1.silu1 (silu) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {"sigmoid": 50331648} | 100,663,296 / 100,663,296 / 0 |
| 89 | up2.residual1.conv1 (conv2d) | 2×256×256×384 → 2×256×256×384 | 231,928,233,984 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 1,180,160 |
| 90 | up2.residual1.norm2 (groupnorm) | 2×256×256×384 → 2×256×256×384 | 0 | 352,321,600 | {"rsqrt": 64} | 100,663,296 / 100,663,296 / 1,024 |
| 91 | up2.residual1.silu2 (silu) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {"sigmoid": 50331648} | 100,663,296 / 100,663,296 / 0 |
| 92 | up2.residual1.conv2 (conv2d) | 2×256×256×384 → 2×256×256×384 | 231,928,233,984 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 1,180,160 |
| 93 | up2.residual1.add (residual_add) | 2×256×256×384, 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 201,326,592 / 100,663,296 / 0 |
| 94 | up2.residual1.divide_by_one (residual_rescale) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 0 |
| 95 | up2.residual2.norm1 (groupnorm) | 2×256×256×384 → 2×256×256×384 | 0 | 352,321,600 | {"rsqrt": 64} | 100,663,296 / 100,663,296 / 1,024 |
| 96 | up2.residual2.silu1 (silu) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {"sigmoid": 50331648} | 100,663,296 / 100,663,296 / 0 |
| 97 | up2.residual2.conv1 (conv2d) | 2×256×256×384 → 2×256×256×384 | 231,928,233,984 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 1,180,160 |
| 98 | up2.residual2.norm2 (groupnorm) | 2×256×256×384 → 2×256×256×384 | 0 | 352,321,600 | {"rsqrt": 64} | 100,663,296 / 100,663,296 / 1,024 |
| 99 | up2.residual2.silu2 (silu) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {"sigmoid": 50331648} | 100,663,296 / 100,663,296 / 0 |
| 100 | up2.residual2.conv2 (conv2d) | 2×256×256×384 → 2×256×256×384 | 231,928,233,984 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 1,180,160 |
| 101 | up2.residual2.add (residual_add) | 2×256×256×384, 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 201,326,592 / 100,663,296 / 0 |
| 102 | up2.residual2.divide_by_one (residual_rescale) | 2×256×256×384 → 2×256×256×384 | 0 | 50,331,648 | {} | 100,663,296 / 100,663,296 / 0 |
| 103 | up2.nearest (nearest2d) | 2×256×256×384 → 2×256×512×768 | 0 | 0 | {} | 100,663,296 / 402,653,184 / 0 |
| 104 | up2.spatial_conv (conv2d) | 2×256×512×768 → 2×256×512×768 | 927,712,935,936 | 201,326,592 | {} | 402,653,184 / 402,653,184 / 1,180,160 |
| 105 | up3.residual0.norm1 (groupnorm) | 2×256×512×768 → 2×256×512×768 | 0 | 1,409,286,208 | {"rsqrt": 64} | 402,653,184 / 402,653,184 / 1,024 |
| 106 | up3.residual0.silu1 (silu) | 2×256×512×768 → 2×256×512×768 | 0 | 201,326,592 | {"sigmoid": 201326592} | 402,653,184 / 402,653,184 / 0 |
| 107 | up3.residual0.conv1 (conv2d) | 2×256×512×768 → 2×128×512×768 | 463,856,467,968 | 100,663,296 | {} | 402,653,184 / 201,326,592 / 590,080 |
| 108 | up3.residual0.norm2 (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 109 | up3.residual0.silu2 (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 110 | up3.residual0.conv2 (conv2d) | 2×128×512×768 → 2×128×512×768 | 231,928,233,984 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 295,168 |
| 111 | up3.residual0.shortcut (conv2d) | 2×256×512×768 → 2×128×512×768 | 51,539,607,552 | 100,663,296 | {} | 402,653,184 / 201,326,592 / 65,792 |
| 112 | up3.residual0.add (residual_add) | 2×128×512×768, 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 402,653,184 / 201,326,592 / 0 |
| 113 | up3.residual0.divide_by_one (residual_rescale) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 0 |
| 114 | up3.residual1.norm1 (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 115 | up3.residual1.silu1 (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 116 | up3.residual1.conv1 (conv2d) | 2×128×512×768 → 2×128×512×768 | 231,928,233,984 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 295,168 |
| 117 | up3.residual1.norm2 (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 118 | up3.residual1.silu2 (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 119 | up3.residual1.conv2 (conv2d) | 2×128×512×768 → 2×128×512×768 | 231,928,233,984 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 295,168 |
| 120 | up3.residual1.add (residual_add) | 2×128×512×768, 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 402,653,184 / 201,326,592 / 0 |
| 121 | up3.residual1.divide_by_one (residual_rescale) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 0 |
| 122 | up3.residual2.norm1 (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 123 | up3.residual2.silu1 (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 124 | up3.residual2.conv1 (conv2d) | 2×128×512×768 → 2×128×512×768 | 231,928,233,984 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 295,168 |
| 125 | up3.residual2.norm2 (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 126 | up3.residual2.silu2 (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 127 | up3.residual2.conv2 (conv2d) | 2×128×512×768 → 2×128×512×768 | 231,928,233,984 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 295,168 |
| 128 | up3.residual2.add (residual_add) | 2×128×512×768, 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 402,653,184 / 201,326,592 / 0 |
| 129 | up3.residual2.divide_by_one (residual_rescale) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {} | 201,326,592 / 201,326,592 / 0 |
| 130 | decoder.output_norm (groupnorm) | 2×128×512×768 → 2×128×512×768 | 0 | 704,643,136 | {"rsqrt": 64} | 201,326,592 / 201,326,592 / 512 |
| 131 | decoder.output_silu (silu) | 2×128×512×768 → 2×128×512×768 | 0 | 100,663,296 | {"sigmoid": 100663296} | 201,326,592 / 201,326,592 / 0 |
| 132 | decoder.output (conv2d) | 2×128×512×768 → 2×3×512×768 | 5,435,817,984 | 2,359,296 | {} | 201,326,592 / 4,718,592 / 6,918 |

## 生命周期与复制接口

| 张量 | bytes | 产生步骤 | 最后使用步骤（含调用栈保留） |
|---|---:|---:|---:|
| latent | 786,432 | -1 | 133 |
| post_quant | 786,432 | 0 | 133 |
| decoder.input | 12,582,912 | 1 | 25 |
| mid.residual0.norm1 | 12,582,912 | 2 | 3 |
| mid.residual0.silu1 | 12,582,912 | 3 | 4 |
| mid.residual0.conv1 | 12,582,912 | 4 | 5 |
| mid.residual0.norm2 | 12,582,912 | 5 | 6 |
| mid.residual0.silu2 | 12,582,912 | 6 | 7 |
| mid.residual0.conv2 | 12,582,912 | 7 | 9 |
| mid.residual0.add | 12,582,912 | 8 | 9 |
| mid.residual0.divide_by_one | 12,582,912 | 9 | 17 |
| mid.attention.norm | 12,582,912 | 10 | 17 |
| mid.attention.q | 12,582,912 | 11 | 17 |
| mid.attention.k | 12,582,912 | 12 | 17 |
| mid.attention.v | 12,582,912 | 13 | 17 |
| mid.attention.sdpa | 12,582,912 | 14 | 15 |
| mid.attention.out | 12,582,912 | 15 | 16 |
| mid.attention.add | 12,582,912 | 16 | 17 |
| mid.attention.divide_by_one | 12,582,912 | 17 | 25 |
| mid.residual1.norm1 | 12,582,912 | 18 | 19 |
| mid.residual1.silu1 | 12,582,912 | 19 | 20 |
| mid.residual1.conv1 | 12,582,912 | 20 | 21 |
| mid.residual1.norm2 | 12,582,912 | 21 | 22 |
| mid.residual1.silu2 | 12,582,912 | 22 | 23 |
| mid.residual1.conv2 | 12,582,912 | 23 | 25 |
| mid.residual1.add | 12,582,912 | 24 | 25 |
| mid.residual1.divide_by_one | 12,582,912 | 25 | 51 |
| up0.residual0.norm1 | 12,582,912 | 26 | 27 |
| up0.residual0.silu1 | 12,582,912 | 27 | 28 |
| up0.residual0.conv1 | 12,582,912 | 28 | 29 |
| up0.residual0.norm2 | 12,582,912 | 29 | 30 |
| up0.residual0.silu2 | 12,582,912 | 30 | 31 |
| up0.residual0.conv2 | 12,582,912 | 31 | 33 |
| up0.residual0.add | 12,582,912 | 32 | 33 |
| up0.residual0.divide_by_one | 12,582,912 | 33 | 41 |
| up0.residual1.norm1 | 12,582,912 | 34 | 35 |
| up0.residual1.silu1 | 12,582,912 | 35 | 36 |
| up0.residual1.conv1 | 12,582,912 | 36 | 37 |
| up0.residual1.norm2 | 12,582,912 | 37 | 38 |
| up0.residual1.silu2 | 12,582,912 | 38 | 39 |
| up0.residual1.conv2 | 12,582,912 | 39 | 41 |
| up0.residual1.add | 12,582,912 | 40 | 41 |
| up0.residual1.divide_by_one | 12,582,912 | 41 | 49 |
| up0.residual2.norm1 | 12,582,912 | 42 | 43 |
| up0.residual2.silu1 | 12,582,912 | 43 | 44 |
| up0.residual2.conv1 | 12,582,912 | 44 | 45 |
| up0.residual2.norm2 | 12,582,912 | 45 | 46 |
| up0.residual2.silu2 | 12,582,912 | 46 | 47 |
| up0.residual2.conv2 | 12,582,912 | 47 | 49 |
| up0.residual2.add | 12,582,912 | 48 | 49 |
| up0.residual2.divide_by_one | 12,582,912 | 49 | 51 |
| up0.nearest | 50,331,648 | 50 | 51 |
| up0.spatial_conv | 50,331,648 | 51 | 77 |
| up1.residual0.norm1 | 50,331,648 | 52 | 53 |
| up1.residual0.silu1 | 50,331,648 | 53 | 54 |
| up1.residual0.conv1 | 50,331,648 | 54 | 55 |
| up1.residual0.norm2 | 50,331,648 | 55 | 56 |
| up1.residual0.silu2 | 50,331,648 | 56 | 57 |
| up1.residual0.conv2 | 50,331,648 | 57 | 59 |
| up1.residual0.add | 50,331,648 | 58 | 59 |
| up1.residual0.divide_by_one | 50,331,648 | 59 | 67 |
| up1.residual1.norm1 | 50,331,648 | 60 | 61 |
| up1.residual1.silu1 | 50,331,648 | 61 | 62 |
| up1.residual1.conv1 | 50,331,648 | 62 | 63 |
| up1.residual1.norm2 | 50,331,648 | 63 | 64 |
| up1.residual1.silu2 | 50,331,648 | 64 | 65 |
| up1.residual1.conv2 | 50,331,648 | 65 | 67 |
| up1.residual1.add | 50,331,648 | 66 | 67 |
| up1.residual1.divide_by_one | 50,331,648 | 67 | 75 |
| up1.residual2.norm1 | 50,331,648 | 68 | 69 |
| up1.residual2.silu1 | 50,331,648 | 69 | 70 |
| up1.residual2.conv1 | 50,331,648 | 70 | 71 |
| up1.residual2.norm2 | 50,331,648 | 71 | 72 |
| up1.residual2.silu2 | 50,331,648 | 72 | 73 |
| up1.residual2.conv2 | 50,331,648 | 73 | 75 |
| up1.residual2.add | 50,331,648 | 74 | 75 |
| up1.residual2.divide_by_one | 50,331,648 | 75 | 77 |
| up1.nearest | 201,326,592 | 76 | 77 |
| up1.spatial_conv | 201,326,592 | 77 | 104 |
| up2.residual0.norm1 | 201,326,592 | 78 | 79 |
| up2.residual0.silu1 | 201,326,592 | 79 | 80 |
| up2.residual0.conv1 | 100,663,296 | 80 | 81 |
| up2.residual0.norm2 | 100,663,296 | 81 | 82 |
| up2.residual0.silu2 | 100,663,296 | 82 | 83 |
| up2.residual0.conv2 | 100,663,296 | 83 | 86 |
| up2.residual0.shortcut | 100,663,296 | 84 | 86 |
| up2.residual0.add | 100,663,296 | 85 | 86 |
| up2.residual0.divide_by_one | 100,663,296 | 86 | 94 |
| up2.residual1.norm1 | 100,663,296 | 87 | 88 |
| up2.residual1.silu1 | 100,663,296 | 88 | 89 |
| up2.residual1.conv1 | 100,663,296 | 89 | 90 |
| up2.residual1.norm2 | 100,663,296 | 90 | 91 |
| up2.residual1.silu2 | 100,663,296 | 91 | 92 |
| up2.residual1.conv2 | 100,663,296 | 92 | 94 |
| up2.residual1.add | 100,663,296 | 93 | 94 |
| up2.residual1.divide_by_one | 100,663,296 | 94 | 102 |
| up2.residual2.norm1 | 100,663,296 | 95 | 96 |
| up2.residual2.silu1 | 100,663,296 | 96 | 97 |
| up2.residual2.conv1 | 100,663,296 | 97 | 98 |
| up2.residual2.norm2 | 100,663,296 | 98 | 99 |
| up2.residual2.silu2 | 100,663,296 | 99 | 100 |
| up2.residual2.conv2 | 100,663,296 | 100 | 102 |
| up2.residual2.add | 100,663,296 | 101 | 102 |
| up2.residual2.divide_by_one | 100,663,296 | 102 | 104 |
| up2.nearest | 402,653,184 | 103 | 104 |
| up2.spatial_conv | 402,653,184 | 104 | 129 |
| up3.residual0.norm1 | 402,653,184 | 105 | 106 |
| up3.residual0.silu1 | 402,653,184 | 106 | 107 |
| up3.residual0.conv1 | 201,326,592 | 107 | 108 |
| up3.residual0.norm2 | 201,326,592 | 108 | 109 |
| up3.residual0.silu2 | 201,326,592 | 109 | 110 |
| up3.residual0.conv2 | 201,326,592 | 110 | 113 |
| up3.residual0.shortcut | 201,326,592 | 111 | 113 |
| up3.residual0.add | 201,326,592 | 112 | 113 |
| up3.residual0.divide_by_one | 201,326,592 | 113 | 121 |
| up3.residual1.norm1 | 201,326,592 | 114 | 115 |
| up3.residual1.silu1 | 201,326,592 | 115 | 116 |
| up3.residual1.conv1 | 201,326,592 | 116 | 117 |
| up3.residual1.norm2 | 201,326,592 | 117 | 118 |
| up3.residual1.silu2 | 201,326,592 | 118 | 119 |
| up3.residual1.conv2 | 201,326,592 | 119 | 121 |
| up3.residual1.add | 201,326,592 | 120 | 121 |
| up3.residual1.divide_by_one | 201,326,592 | 121 | 129 |
| up3.residual2.norm1 | 201,326,592 | 122 | 123 |
| up3.residual2.silu1 | 201,326,592 | 123 | 124 |
| up3.residual2.conv1 | 201,326,592 | 124 | 125 |
| up3.residual2.norm2 | 201,326,592 | 125 | 126 |
| up3.residual2.silu2 | 201,326,592 | 126 | 127 |
| up3.residual2.conv2 | 201,326,592 | 127 | 129 |
| up3.residual2.add | 201,326,592 | 128 | 129 |
| up3.residual2.divide_by_one | 201,326,592 | 129 | 130 |
| decoder.output_norm | 201,326,592 | 130 | 131 |
| decoder.output_silu | 201,326,592 | 131 | 132 |
| decoder.output | 4,718,592 | 132 | 133 |

| 上采样阶段 | 输入 bytes | contiguous 分支触发 | 实体复制 bytes |
|---:|---:|---|---:|
| 0 | 12,582,912 | False | 0 |
| 1 | 50,331,648 | False | 0 |
| 2 | 100,663,296 | False | 0 |

持久 decode cache：0 bytes；返回后调用方输入与输出：5,505,024 bytes。

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
