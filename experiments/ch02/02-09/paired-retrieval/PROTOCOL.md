# 同消息检索质量对照：执行前协议

复用2-5完整43层V4 Flash八道冻结消息及原成功响应，不重跑V4。仅新增固定Qwen3-8B b968826d9c46dd6066d109eabc6255188de91218八请求。system/user字符串逐字相同；各自使用原生tokenizer/chat模板，不强行令token数量相同。V4原chat模式，Qwen enable_thinking=False。两个答案×前/后位置×两长度，原V4实际501/2036token。

两模型均greedy、top_p1、top_k1、最大32输出、允许自然EOS。主质量规则text.strip()==原answer且正常stop；保留所有回答，不事后改题/宽松评分/重试。Qwen BF16权重/KV、TRITON_ATTN、eager、单请求、chunk256、APC关闭、2GiB KV。V4原MXFP4专家fallback、FP8 KV、CPUoffload110GiB及私有bias别名适配完整披露。

只比较固定八题的答案质量。两者时间来自不同日期/引擎/部署/观察区间，不做速度、资源或性价比排名；这不是相同精度的纯模型因果对照。Qwen不预热同题，首请求可能含编译。V4 Pro/K3没有本地匹配原始响应则报告缺失，不能沿用Flash或其他模型分数。八题很窄，无总体优劣结论。

成功标准是实际请求记录完整且可独立评分，并非预设所有答案必须正确。数值门槛与一般任务质量不因检索通过而放行。calculations只读；没有调用其模型成本计算。
