# 9-6：直接读取实际专家分配与padding缓冲

新增一次完整Qwen3-VL-30B-A3B FP8运行，仍为原四道固定检索题；原TRITON函数照常执行，返回后同步读取分配结果，再原样返回原tuple。**四题输出token、文本、正常stop及全部路由数组均与既有基线相同**，因此保留其4/4精确JSON结果。读取增加同步/CPU复制/压缩开销，不能用此次墙钟测后端性能。

## 实际返回值

共9408条记录，每题2352条，覆盖48层及每题7280个实际消费位置。逐条用原生路由切片SHA和128个专家计数核对输入：层号按串行48层调用顺序映射，再用完整切片哈希校验；观察器没有直接记录层号，不能将此方法推广到并行或重排执行。

| 输入token数 | 记录数 | 实际路径 | BLOCK_SIZE_M | 返回post-padded计数范围 | 已分配sorted缓冲元素数 |
|---:|---:|---|---:|---:|---:|
| 2048 | 576 | aligned | 64 | 18304–22016 | 24448 |
| 1091 | 192 | aligned | 64 | 12352–13952 | 16792 |
| 1 | 8640 | naive | 16 | 128 | 无sorted缓冲 |

这些计数直接来自真实返回tensor，不是离线按公式估算。768条aligned记录中，**11,112,960个有效assignment全部恰好出现一次**，且每个有效位置指向的专家与它所在块的expert ID相同；只读取post-padded有效前缀，没有把已分配缓冲尾部当有效数据。观察到的post-padded计数小于sorted缓冲容量，二者不可互换。

单token路径返回`sorted_token_ids=None`，expert块ID直接等于实际top8，返回post-padded标量128。它是源码中的正常直分配分支，不是缺失采集或运行失败。这也解释了此前profiler中排列算子仅出现768次，而非9408次。

post-padded标量、缓冲分配容量和实际GPU发射/执行工作不同。Triton可能按更大的缓冲网格启动并在kernel内检查有效范围；本轮没有测量每个block实际执行的指令或FLOP，不能把表中的数直接换成倍率、吞吐或复制收益。实际padding字节/数量级预算仍归C49，本目录不重复计算。

## 原件与方法

`observer.py`仅包装已安装TRITON模块引用的`_prepare_expert_assignment`，不改输入、权重、路由和返回值；在每个请求状态标记生效后记录，初始化/预热没有列入正式记录。读取会同步GPU，这是有干扰的观察实验。`runtime-sources/`保存原分配、排列与专家调用源码。

`runs/observe-001/output/*-assignments.jsonl.gz`保留9408个原始记录，包括实际topk切片SHA/专家计数、参数、post-padded标量、缓冲分配元素数、有效sorted索引以及expert块ID；gzip是逐记录追加成员，Python gzip可顺序读取。完整原生路由数组和模型响应也保存。`reference/`复制此前single-gpu/native-001原件，仅用于核对，未重新运行基线。

主运行14069 exit0，guard无原因、无存活后代，墙钟33.624秒包含初始化、观察和压缩。使用固定revision `d9748a51ae66354c4dad665aab2c71f26cf2c8cd`、完整48层、TRITON FP8 MoE、单请求、2048分块、16384上下文、4GiB KV、greedy/128输出预算及原生路由返回；关闭EP/EPLB/DBO、图、APC、异步调度。模型为VL的文本输入变体，不冒充纯文本Qwen3。

## 独立复现

```sh
/home/ubuntu/vllm023-venv/bin/python -B resource_guard.py --out runs/observe-new -- \
  /home/ubuntu/vllm023-venv/bin/python -B run.py \
  --model /path/to/fixed-model --out runs/observe-new/output
python3 -m pip install numpy
python3 analyze.py
```

需要固定Linux环境与模型缓存，run.py/observer.py必须放在同一目录。重跑用新输出名并更新分析器的run选择；`python3 analyze.py /tmp/assignment-review`可将封存原件的报告重放到独立目录。源码、输入、参考、结果均在此目录，不导入其他实验代码。guard沿用96GiB RSS求和、64GiB自身GPU、全局24GiB剩余和3600秒轮询限制，不是硬隔离。

完整多设备放置/复制、暴露通信与DBO/TBO仍未完成；本轮只补实际单卡分配路径和缓冲正确性，9-6保持部分完成。calculations未修改。
