# 6-2 JAX TP/SP 实际 CPU 路径：运行前协议

本实验执行 JAX shard_map 和 XLA CPU collective，不实现拓扑/流量估算，不使用 calculations。四个 CPU logical devices 属于同一 M2 Max，不能作为四张 GPU、跨机网络或八卡吞吐的证据。

固定 Qwen3-8B FFN hidden=4096、intermediate=12288（本地官方 config 副本）；随机 FP32 权重，非训练权重，不能评估模型质量。执行 gate/up、SiLU、逐元素乘、down 的完整 FFN 子层；不含 attention/RMSNorm/整个 Transformer 层。输入 token 数 8/32，TP 2/4。TP 保持输入复制、列切 gate/up、行切 down 后 psum；SP 输入按 token 切、先 all_gather，投影后 psum_scatter，最终输出仍按 token 切。

NumPy FP64 未分片 FFN 为独立数值参考；固定 atol=0.0001、rtol=0.001，验证全部元素并保存输出、最大误差、相对 L2。随机种子 602，输入与三权重原件保存，可独立复算。不能因观测结果改阈值。

先微型 smoke（hidden64/intermediate192），保留成功或失败；正式形状另目录。每配置显式记录每个 addressable shard 的 device/index/shape/nbytes；编译后的 HLO 和 StableHLO 保留用于检查实际 collective，不能把逻辑张量字节当真实链路流量。编译与一次 warmup 后执行五次阻塞完成计时，固定随机顺序。输入放置、编译和输出搬回分别位于计时外。时间仅为本机实现观测，不评价 GPU 网络或 TP/SP 优劣。

正式 CPU 执行等待同时运行的 Mac 32K 生成结束。不改封存实验或运行中的 GPU 服务。任意错误保留日志、failure.json 和非零退出。

官方实现参考：https://docs.jax.dev/en/latest/notebooks/shard_map.html 。安装版本与源文件 SHA 在运行时保存；参考原语语义，脚本自行实现上述 FFN。
