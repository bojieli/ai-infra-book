# 原生路由基础实验

两个独立SGLang0.5.13.post1/Qwen3-8B BF16 HTTP worker共用一张RTX PRO。Router0.3.2独立环境，round_robin/cache_aware/power_of_two按固定顺序各重放12轮实际Agent输入，逐请求串行，强制1输出token。该Agent原任务失败，这里只复用输入轨迹，不重做工具或宣称任务质量成功。

每策略前清理两个worker的前缀缓存，并新建router；不把router预测命中当真实KV命中。完整响应、worker原生JSON请求日志、路由日志和metrics一起保存；由rid关联实际worker，再统计token加权/请求命中及复用间隔。用原tokenizer解码后重新编码必须逐token相等。

这是同GPU低负载基础验证，不能当跨机器吞吐、排队策略优劣、远端取回p95或完成时间预测实验。队列压力、重复随机顺序、Chat轨迹、预测完成时间、缓存淘汰/重启偏差继续待做。所有服务只监听loopback，退出时只清理自建进程组。
