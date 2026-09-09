# 实验9-6：热门专家的放置与复制

新增[真实单卡MoE路由基线](single-gpu/README.md)：完整Qwen3-VL-30B-A3B FP8四题，原生采集与关闭采集各4/4正确、输出逐token一致；保存11,182,080次真实专家选择及两张分层图。尚无分段计时或多设备放置收益结论。

[MARLIN后端对照](backend-compare/README.md)新增四次生成：答案及输出token与TRITON相同，但约59.4%的token-layer专家集合不同。MoE路径从W8A8变为W8A16，不能当作相同数值格式的纯速度比较。

[CPU/CUDA完整轨迹](profile/README.md)已取得221648次真实kernel执行，四题输出与路由均和无profiler基线相同。原始事件可继续用于严格分段归因，目前不按名字猜测dispatch/GEMM/combine时间。

[提交关联分析](phase-attribution/README.md)已将两次专家GEMM分别关联到9408个MoE调用，CUDA记录时间之和353.578/203.660ms；全部77568个MoE kernel已按CPU算子关联，最终本地求和9408次/37.074ms；通信对照仍待。

[实际分配缓冲观测](assignment-observation/README.md)新增四题，输出/路由同基线；768个长输入排列记录的有效assignment逐个核验，8640个单token调用正常走无sorted缓冲的直分配路径。返回padding计数和已分配容量不同，不据此推断实际GPU工作或通信收益。

已完成[当前RTX单卡后端配置检查](backend-readiness/README.md)。vLLM 0.23.0实际接受基线配置，但拒绝TP=1/DP=1的EPLB，以及默认all-to-all后端下的DBO。当前不能把这几个开关组合列为本机可运行对照。

原6-3完整V4路由采集已有真实专家ID/权重，不重复运行；它没有dispatch/GEMM/combine分段计时或多设备放置对照，不能替代本实验。现有缓存的Qwen3-VL-30B-A3B是视觉语言MoE变体，也不能冒充纯文本Qwen3 MoE。9-6仍未完成：需要实际受支持的模型运行、路由/阶段计时、专家放置和复制、后端/重叠单变量对照与质量/尾延迟证据。C49计算任务未动。
