# 9-10：Native子进程存储观测补测

四组18请求全部执行完成并通过独立分析，远端控制器exit0、四worker exit0、传输exit0。每个实际文件读取PID都出现在模块级钩子安装记录和控制器观察到的子进程集合中。原cache-mechanism的54请求不改写，原native缺失的计数字段仍是null。

| 条件（每项两轮） | 每轮成功get | 唯一key | get文件字节累计 | 首个完成请求缓存 |
|---|---:|---:|---:|---:|
| native单请求 | 64 | 64 | 144MiB | storage1008 tokens |
| native 8请求波 | 256 | 64 | 576MiB | 0，详情null |

所有18个完整输出ID及text逐一等于原固定参考。并发波两次均index4先完成；不能默认index0。内部max_running_requests=1，实际KV池4096位置由runtime server-info双字段验证；这里的并发是未完成客户端请求波，不是8个GPU同时decode。字节累计包括重复get，不是独立文件容量或物理磁盘I/O。

原worker只在native主入口内安装补丁；本补测在模块加载时安装，从而覆盖spawn重导入的主模块。实际记录显示每组3个安装PID，其中1个子进程执行get，区别于控制器启动的worker PID。这支持修正仪器覆盖范围，不能把以前不存在的trace补写成以前已测量。

新观察与原API结果及HTTP文件trace一致，说明“文件get成功”和“首个请求有效命中”是不同量。首请求未命中的具体prefetch限额、就绪检查或重复前缀归属分支尚未直接记录，不能宣称根因已确定。

## 固定条件与复现

baseline.json记录旧代码身份。除只选native条件、模块级安装和安装PID记录外，模型、输入、输出、缓存manifest和引擎配置保持；分析逐项hash校验。每组从固定65文件缓存源复制并校验，使用独立新engine；greedy16个强制输出只验证输出一致性，不评价自然答案质量。

GPU与原四服务及约49GiB服务共存。gpu-final显示原五服务均保留，本实验进程已消失；不比较共享GPU时延。组前显存不足30000MiB即停止，组间只等待自己退出的PID释放。没有因显存问题终止原服务。

在新独立副本、results不存在且同固定环境可用时运行：

```sh
/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python run.py --output results
python3 analyze.py
```

run.py的--cache可指定相同65文件来源；默认只读9-8/storage-v3。config.json固定模型快照路径。代码、完整输入/参考、来源manifest均在本目录，不依赖相邻实验代码；运行所需固定SGLang环境与模型同原协议。不要覆盖封存results。

每组原始安装记录、get/set事件、输出/API缓存详情、实际配置、缓存副本、资源与PID所有权、退出及全部日志保留。execution-observation.json记录主agent确认的控制器和传输终止。analyze.py只需标准库，核验18输出、runtime容量、65文件准备及真实get PID。原缺失与原分析失败仍在相邻实验保存。

本轮仅补9-10机制实验的native文件观测，不等同全部部署/启动实验完成；没有运行calculations或开始最终跨session论文审计。
