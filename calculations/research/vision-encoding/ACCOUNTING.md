# Qwen3-VL-4B静态图视觉编码预算

固定Transformers commit `cbc1651a032b923da7f4b44b3d0e6f68e6ba6b55`原件及官方模型config；输入是预处理后图像，尺寸校验和EC几何复用multimodal_cache。模型forward输出final和三个DeepStack，不包含语言prefill。JPEG/resize/像素标准化尚无CPU运行实测。

单图P=(H/16)(W/16)，融合后M=P/4。静态图复制到temporal patch=2，但只有一个temporal grid。patch是K=3×2×16×16=1536到1024的非重叠Conv3d。全部24层有QKV/O、非因果P² QK/PV、1024→4096→1024 MLP、两个LayerNorm与两个残差；每图独立attention，N图总平方项为N×P²，不是(NP)²。

Final merger在[P,1024]做norm后reshape；DeepStack三路在[M,4096]做norm。四个merger每个均4096→4096→2560，两个Linear有bias，使用默认exact GELU；块内使用gelu_pytorch_tanh。深层抽取索引5/11/17，每路只执行一次，不把其加成语言token长度或再执行视觉block。

参考scalar约定（不宣称实际kernel指令）：两遍LayerNorm每行宽d采用mean、center、variance、eps、rsqrt、affine，总adds=4d−1、muls=3d+2、rsqrt=1；tanh GELU每元素6mul+2add+tanh；exact GELU每元素3mul+1add+erf。softmax每行p含max(p−1) comparisons、p subtract、p exp、p−1 sum-add、p division；另算score scaling p mul。RoPE对Q/K每元素2mul+1add，半维符号翻转独立negation。

矩阵2MNK与bias-add分开，特殊函数按调用数单列，不将一个exp等同一个FLOP。logical tensor read/write只表语义操作数，不能当HBM流量或算子实际峰值。LayerNorm/softmax/RoPE的FP32中间量与模型BF16驻留不能混为所有算子统一低精度算力。
