# 9-10 首请求存储读取但未有效命中：运行前机制消融

本项在startup封存后新开目录；不改旧结果。目标是定位入口、logprob返回和同前缀并发对有效KV命中的影响，不作共享GPU性能因果比较。

固定模型/1024token前缀/16token greedy强制输出/完整65文件缓存/SGLang0.5.13.post1/wait_complete及原attention配置。三入口native Engine不返回logprob、HTTP不返回logprob、HTTP返回logprob，分别1请求或8同前缀并发，两轮seed9102交错，共12组54请求。native使用已安装源码核实的Engine.async_generate，在Engine自身loop收集并发；HTTP使用同步门后线程并发。内部max_running_requests仍1，因此并发指客户端未完成请求，不是8个GPU同时decode。两入口的初始化/默认服务器warmup差异保留，不把差异全归于HTTP传输。

所有请求显式logprob_start_len=-1；HTTP返回logprob只是第三条件的变化，不能声称此前漏传了该字段。实际TokenizerManager源码在非stream完成分支也返回完整output_ids，所以HTTP不返回logprob仍要求完整ID；缺字段判失败，不以重分词文本冒充实际生成ID。

共存约49GiB的已有VLLM PID3614304及四原服务，全部保留。只读当前free约36GiB；旧mem_fraction_static0.4按本版本加载前可用内存作为基数，不适合当前余量。统一改0.75、max_total_tokens固定4096，启动日志/最终server-info要核实实际池容量，不能以比例推定。每组前记录GPU进程和free，低于30000MiB立即停止并保留，不杀原任务。当前重点机制而非速度，不与另一实验同时占GPU；原服务的动态负载仍可能共存。

每组新的完整缓存副本，逐文件SHA核验，准备开始/结束单列在cache-preparation。新引擎第一次正式请求/并发波前不主动执行本实验warmup请求，避免填充HBM；HTTP框架自身的默认预热通过原生日志保留。固定现有TVM JIT目录但不声称逐组所有JIT哈希相同。记录所有storage get/set和API cache字段，null不填0；首次发送/首次完成各依实际记录定位，不固定index0。

正确性：每次原生完整output_ids及text精确匹配封存9-8参考；不得放宽标准。成功get与有效缓存token分别统计，不能以get成功定义命中。server-info和原生日志保存实际配置；若入口/缓存数未形成预期，照样保留为机制结果，不为得到命中替换输出。

HTTP准备240秒上限、请求120秒、future150秒；native异步整波120秒；外层worker全生命周期600秒上限。每组独立进程组，finally只清理自建组并wait，worker、server、控制器退出码分开记录；失败条件保留并继续其他可执行条件。资源不足则停止新增条件。

运行：在本目录独立副本执行专用SGLang环境的python run.py --output results。输出存在拒绝覆盖。--cache可指定同一65文件来源，默认只读9-8/storage-v3；源码/配置/输入/参考独立放在本目录。

不调用calculations，不作教学模拟；不开始全书最终跨session审计，也不改正文/共享进展。尚未执行时不填结果。
