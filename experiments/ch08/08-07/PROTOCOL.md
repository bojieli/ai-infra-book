# 8-7 Mac Qwen3-8B MLX 实际生成与独立KV槽

运行前固定官方Qwen/Qwen3-8B-MLX-4bit revision383413e909f3bc5303ce195ebbdf0339c5a1a2a3；实际权重4,351,884,216 bytes。先核查本地模型缓存无对应MLX权重，磁盘可用约33GiB后下载一次，校验实际SHA与Hub LFS SHA。隔离mlx-lm环境，GPU M2Max96GiB。不是235B/R1运行。

4固定题：两道给定键值精确检索、两道小整数运算，要求仅输出指定答案。greedy temperature0、enable_thinking=False、最多64输出token，strip后字符串精确相等才通过；长度截断和错误保留，不能改答案门槛。

先4次短提示生成记录模型加载和自然输出；再两重复的1槽和4槽案例（固定打乱顺序seed807）。槽内容独立，长提示精确8192个有效token，使用固定模板、题目和重复中性填充token，保留完整输入IDs和解码文本。逐槽真实prefill前8191token（512一块），全部槽同时保留，再分别用剩余1token真实生成。记录各层KV shape、dtype、offset和实际nbytes；比较1槽/4槽真实保留容量，不将串行构造/生成称为并发吞吐。

加载/eval、prefill块、首token、全部生成用同步实际时刻。MLX active/peak/cache为框架分配器视角，不是系统内存或磁盘换入量；同时保存vm_stat与进程resource峰值做边界依据。KV不量化、无自动前缀共享、不offload。1槽每重复用题0，4槽用全部四题，不能直接把两条件总正确率当公平质量策略比较；可比较题0跨槽设置输出一致性。
