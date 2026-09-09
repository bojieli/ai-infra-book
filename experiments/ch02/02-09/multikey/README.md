# 2-9多键检索：实际V4编码与启动条件准备

四道512行多键检索文档已由固定V4原生编码器实际编码：**每题4148token**，Qwen原记录每题7239token。加128输出预算需要4276位置，原V44096配置不够，提出context/max_total_tokens5120。两模型分词不同，不能用Qwen长度直接代入V4容量。

`prepare.py`使用固定revision `7872f01b1d1fe23eabc4c98b48bffcef5a386062`的`encoding/encoding_dsv4.py` chat模式与tokenizer，四题encode/decode全文一致；`prepared/cases.json`保存全部消息、文本、token、期望JSON、源SHA和输出预算。仅CPU编码，无权重读取或模型推理。

`check_capacity.py`实际调用固定私有SGLang的ServerArgs解析5120候选，**不创建Engine**。实际KV池数量、FP8状态和长输入前向仍需实跑验证。保留原完整V4的140GiB主存启动门槛；本轮回收已确认的旧共享池后，主存仍未满足该门槛，故没有启动模型。状态见capacity-check.json，不把参数可解析当作可运行。

原Qwen BF16串行repeat0四响应由上一实验提案逐字复制，已知3/4；新V4响应不存在。后续只新增四个V4请求，质量门槛仍为精确三键JSON、自然stop、拒绝额外键/重复键和解释。不是盲测选题，也不作速度排名。与成功2-5同revision的完整模型、110GiB CPUoffload及私有bias适配仍是拟采用配置；本目录已补独立执行入口，但当前只有输入/条件准备，不是四题推理完成。

复现编码需要固定模型缓存的tokenizer与encoding文件、Transformers；配置检查另需原私有SGLang环境。两脚本独立，不调用calculations或其他实验脚本：

```sh
/path/to/runtime-python -B prepare.py --model /path/to/fixed-V4 --out prepared-new
/path/to/runtime-python -B check_capacity.py
```

check_capacity.py读取prepared/cases.json且以RTX固定模型缓存路径解析，迁移机器需更新该路径。第一次prepare句柄41599 exit0，四输入均4148；配置检查无模型启动。所有结果按manifest封存。

## 独立执行入口与最新预检

`reproduce.py` 默认只做预检：检查固定运行库版本/源码SHA、48分片原路径/大小/mtime、模型小文件SHA、输入/采样参数、5120配置解析、端口与资源门槛。分片检查复用此前版本身份，不冒充本轮完整权重SHA。RTX实际预检32979 exit0；可用主存141115932672bytes低于150323855360bytes，显存门槛通过，没有创建Engine或请求。

```sh
/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python -B reproduce.py
# 条件满足后，以下命令仍会重新检查门槛，再执行四个固定请求：
/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python -B reproduce.py --execute --name multikey-001
```

执行脚本、评分器、私有offload适配和来源快照均在本目录，不导入或运行另一实验目录的代码。固定运行环境和模型缓存是外部资源；迁移机器需在common.py更新路径。新运行使用独立缓存，不复制权重。`launch.py`保留原140GiB主存与80GiB显存启动门槛、运行期资源/超时监督及PID出生时间/pidfd终止保护，只处理本次登记进程；采样不是硬内存限制，命名共享资源需在实际退出后另查。此监督版本主要通过继承的独特环境token登记子进程，未证明覆盖清除token的任意后代，不把它称为通用进程隔离。

`run.py`先保存完整原响应，再由`score.py`验证输入、采样、输出ID、自然stop和精确JSON对象；没有模型响应时不能得到成功。`scorer-review.json`只重评原Qwen四响应（仍3/4），并确认重复键、代码围栏、附加解释等5个反例被拒绝，没有生成或伪造V4输出。既有小矩阵数值门槛未被本任务解除，正确检索也不代表整体数值或模型质量验证。

`runtime-reference/`保存此前成功V4的依赖/权重元数据和源码原件，`origins.json`注明代码复制来源SHA；这不是本轮模型加载证据。最新`execution-readiness.json`保存实际共享主机快照。旧`capacity-check.json`为较早参数解析证据，两者都不是失败的模型运行。
