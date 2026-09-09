# 8-7 32K实际上下文与匹配任务混合

固定既有官方Qwen3-8B-MLX-4bit缓存revision383413e909f3bc5303ce195ebbdf0339c5a1a2a3，复用不重新下载。M2Max96GiB，运行前盘空约27GiB、空闲页约15GiB且inactive约38GiB。最多2槽，实际BF16 KV预期每槽4.5GiB（这是运行前预算，结果必须以真实数组验证）。设置MLX memory_limit24GiB、cache_limit1GiB，每prefill块前active超过20GiB则报错停止，不主动耗尽内存。

固定两题lookup-a与integer-b，与8K实验内容相同；1槽条件先完整prefill/生成第一题、销毁其缓存，再做第二题。2槽条件独立prefill两题并同时保留，再依次生成。两条件每重复均执行完全相同两题；两重复×两条件，共8个真实输出，seed80732打乱条件顺序。

输入长32768token，每槽实际分块512预填充32767token，再送最后1token自然生成。中性填充方法与旧实验相同。greedy、no-thinking、最多64token，strip后精确字符串相等才通过；保留算术错误、格式错误和截断。任务总耗时、逐槽prefill、续写TTFT分开；串行构建不是并发调度吞吐。

每层真实KV shape/dtype/offset/nbytes，MLX active/peak/cache，vm_stat和进程高水位RSS分别保存。每块立即落盘，失败不丢已完成部分。24GiB分配器上限不是对整个主机物理内存的保证；出现框架内存错误则保留原始失败，不提高上限硬跑。缓存池设置与旧8K实验不同，不能把新旧时间差全部归因于上下文长度。不是235B、磁盘offload或模型质量通过。

API语义核对补注（运行中，未改参数）：安装版本说明set_memory_limit只是graph evaluation的内存使用指导值，并不是24GiB硬分配上限。实际主动停止措施是每块前active>20GiB的代码检查，单块临时峰值可能超过检查时的active；因此必须看原始peak，不可宣传框架硬限额。allocator-api.txt保留原说明。
