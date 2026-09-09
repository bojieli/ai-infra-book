# Native存储观测补测：运行前协议

原cache-mechanism12组54请求保留；native四组没有storage.jsonl，因此不能从API命中反推文件get次数。本目录另做native单请求/8同前缀请求波各两轮，共4组18请求。新增实验只补实际子进程观测，不取代原记录，也不声称与原批耗时可直接比较。

只改变worker.py在模块顶层安装存储钩子，并记录每个实际安装PID/PPID；原生Engine运行时spawn重导入主模块，主入口内安装可能无法传播。钩子调用原get/set并原样返回，结果验证不放宽。通过installation文件与真正get事件的PID对应验证，不能只凭源代码认为钩子生效。

保持同模型/1024输入/16强制输出、greedy、wait_complete、4096实际KV池、mem_fraction_static0.75、max_running_requests1、固定65文件缓存。每组独立engine和校验后的缓存副本；每次完整输出ID和text必须等于原参考。并发指客户端未完成请求波，非8请求同时GPUdecode。两轮顺序seed9102。

额外观察会改变执行开销，故不比较性能。GPU保留全部原服务；组前剩余显存低于30000MiB则停止；等待自己的已结束进程释放显存并保留边界，禁止杀原服务。600秒worker上限、120秒请求波上限不变。

必需证据：实际runtime server-info的pool容量；每请求完整输出/API缓存详情；storage.jsonl非空；get事件PID确有安装记录；文件身份与所有失败/退出。不将missing计零，若钩子仍缺失则保留失败并排查，不盲目重复请求。

独立复制本目录至RTX后，用已固定SGLang环境python run.py --output results；--cache可指定同65文件来源。源码变更前身份见baseline.json，不运行calculations，不开始全书最终论文审计。
