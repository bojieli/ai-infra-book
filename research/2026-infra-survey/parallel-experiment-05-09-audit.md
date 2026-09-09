# 实验 5-9 原始请求与 Nsight 记录的独立审计

审计快照：2026-09-09T06:34:27.161748+00:00。只读用户新建的实验目录；只运行本文附带的 Python 标准库核算，SQLite 使用 `mode=ro&immutable=1`。没有运行实验的 worker、collector、analyzer、框架、模型或 GPU 工作，没有修改实验、大纲、案例、共享脚本，也没有 Git 操作。已检查仓库及本任务路径的 AGENTS.md，未发现适用文件。

原件足以支持“同一固定输入已有 11 对完整请求记录，另有两个模式各一次覆盖该请求的 trace；候选缩短了本次 decode 激活 kernel，但没有建立稳定部署收益”。重新计算的客户端指标、逐步热点计数和 GPU 活动区间并集均与现有摘要一致，未发现这些数字的算术错误。这里的“完整请求”指这条强制 32-token 请求从计时开始到交付结束，不能扩张为任务自然完成、所有 GPU 活动无漏采、独占环境或完整实验目标已完成。

**建议保留 partial。** 本次发现的是早期状态文字与后来补入记录没有同步，不应删除用户对稳定性、其他形状/并发和成本摊销的保留。以下判断来自逐条 JSON 与 SQLite 记录，未把 README 或 `status: passed` 当作验收依据。

## 1. 请求身份、预热与正式配对

输入来自 [input.json](../../experiments/ch05/05-09/input.json)，实际数组含 7,239 个 prompt token。配置 [engine-config.json](../../experiments/ch05/05-09/engine-config.json) 指向 Qwen3-8B 固定缓存目录 `b968826d9c46dd6066d109eabc6255188de91218`，指定 BF16、eager、APC 关闭、12 GiB KV 预算、并发实验为 1；引擎允许的 `max_num_seqs=4` 不是此次实际并发。vLLM 0.23 来自实验记录所用环境标识，本审计未访问远端安装环境或重哈希实际模型权重，不能把缓存路径当成对运行中权重的独立校验。

- [raw.json](../../experiments/ch05/05-09/results/paired-eager-v1/raw.json) 的 `requests` 是 26 条：两模式各 2 次预热和 11 次正式请求；`audits` 另有两模式各 1 次、每次 2-token 的审计，共 28 条请求记录。所有预热均在正式测量之前，28 条请求按同一记录时钟排序后互不重叠。
- [requests.jsonl](../../experiments/ch05/05-09/results/paired-eager-v1/requests.jsonl) 的全部 22 行，与 raw 中 `phase=measure` 的 22 个对象逐字段相同，包括顺序字段，不只是条数相同。
- 每个 trial 0–10 恰有 native 和 schedule 各一次。模式次序为 NS、SN、SN、SN、SN、NS、NS、NS、NS、SN、NS；保留退化轮次。它们是一个约 30.2 秒进程中的 11 个配对，不能写成 11 次独立启动实验。
- 26 条预热/正式请求都输出同一组 32 个 token ID；两条审计输出与该数组前两项一致，即 `[4913,74]`。全部正式 token ID 逐位一致，每条请求的 32 个客户端事件累计计数依次为 1–32，时间严格递增，首事件等于记录的 TTFT，末事件不晚于请求完成。
- 每模式的审计有 72 条记录：36 层均有一次 `[7239,24576]` prefill 和一次 `[1,24576]` decode，dtype 均为 `torch.bfloat16`。24 份切换记录各包含同一组 36 层，记录的方法身份分别为原生 `SiluAndMul.forward_cuda` 和 `candidate.run`，且 `audit=false`。这证明记录中的绑定/形状相互一致；不等于测量时逐层数值位同。
- raw 的 6 个源码/输入哈希、两份 profile run 各 6 个哈希均与当前字节相符。`candidate.py` 与选择来源中的 5-6 `schedule.py` 哈希相同，另外四个选择依据哈希也匹配。没有把候选称为本次 Agent 新生成的实现。

固定长度使用 `ignore_eos=true`、temperature 0；这条输出被强制截在 32 token，仅能证明本提示两路径的输出一致，不能证明自然任务成功、通用质量或所有输入的数值正确性。输入、输出、配置及源哈希把两份 profile 与正式实验连起来，但它们不是同一次物理执行，也没有一个跨进程共享的原始请求 ID 可用来合并两类时钟。

## 2. 无 profile 的客户端计时复算

逐请求使用 `ttft_s`、`latency_s` 及客户端累计事件重算；没有用热点 kernel 时间倒推这些数字。

| 口径 | native | schedule |
|---|---:|---:|
| TTFT 中位数（ms） | 435.674034990 | 436.353133991 |
| 请求完成时间中位数（ms） | 816.639983095 | 815.405752975 |
| 每请求平均客户端 ITL 的中位数（ms） | 12.293385259 | 12.249868033 |
| 每请求输出速率的中位数（token/s） | 39.184953789 | 39.244265672 |

平均客户端 ITL 使用 `(末事件时间−首事件时间)/31`。输出速率使用 `32/请求完成时间`，其中包含 prefill/首 token 等待；这是单请求交付速率，既不是 decode-only 吞吐，也不是饱和服务吞吐。客户端 32 个输出事件也不能直接替代 32 个 GPU decode 步。

先在每个 trial 内计算 native−schedule，再取中位数，TTFT 节省为 **−0.058502890 ms**，4/11 为正；请求时延节省为 **1.342880074 ms**，9/11 为正。后者不等于两组时延中位数之差 1.234230120 ms。本次逐条重算与 [results/summary.json](../../experiments/ch05/05-09/results/summary.json) 对应数字一致；差异很小，记录没有建立连续独占或跨独立运行的稳定性，因此不据 9/11 正向配对宣布稳定部署收益。GPU 活动日志本次只核哈希，未把采样文件存在当作独占证明。

## 3. 两份 profile 的进程、窗口和 GPU 关联

[原生命令](../../experiments/ch05/05-09/profiles/native/command.json)和[候选命令](../../experiments/ch05/05-09/profiles/schedule/command.json)记录 Nsight Systems 2026.4.1.191，`--trace=cuda,nvtx`、跟踪 fork、`--capture-range=cudaProfilerApi`，没有 CPU sampling/context-switch 采样。两份 run 的配置除 trace worker 类外与正式实验一致，输出 32 个 token 与正式实验一致。profile run 没有逐条保存两次预热请求，本次只读 JSON/SQLite 能核正式捕获请求，不能独立重建 README 所述两次 profile 预热的执行过程。

| 独立核对项 | native | schedule |
|---|---:|---:|
| worker PID | 2283869 | 2284861 |
| NVTX 请求窗口开始（ns） | 93,502,219 | 28,642,872 |
| NVTX 请求窗口结束（ns） | 944,351,208 | 886,898,864 |
| 请求窗口长度（ms） | 850.848989 | 858.255992 |
| Runtime API 行数 | 29,471 | 28,319 |
| kernel 行数 / 成功 launch 关联 | 16,703 / 16,703 | 16,703 / 16,703 |
| memcpy 行数 / 成功 API 关联 | 134 / 134 | 134 / 134 |
| 已记录 memcpy 字节总数 | 31,936 | 31,936 |
| NVTX 行数 | 35 | 35 |

两份 SQLite 的 GPU 均为 NVIDIA RTX PRO 6000 Blackwell Workstation Edition，同一 GPU UUID，记录总显存 101,973,491,712 字节、188 个 SM、compute capability 12.0。这里只转述采集文件中的硬件身份，不把它变成其他型号或多卡实验。

关联采用 `(globalPid, correlationId)`，而不是单独用可复用的 correlation ID；Runtime 的 globalTid 清除低 24 位得到进程标识，再与 `PROCESSES` 的 PID 和 `TARGET_INFO_CUDA_CONTEXT_INFO.processId` 交叉核对。每个 kernel 均匹配唯一 launch API，返回值为 0；每个 copy 匹配唯一成功的 `cudaMemcpyAsync_v3020`。它们及其 API 均位于各自请求窗口，kernel 不能早于对应 API 的开始，但可以在 API 返回之前启动。

逐步归属使用 launch API 的 CPU 开始时间和线程，落入 `model-step-N` 的 host NVTX 区间。**没有按 GPU 结束时间截断 host 范围。** 例如 native prefill 的 host step 0 在 115,699,110 ns 已返回，但它关联的 GPU kernel 最晚延续到 537,523,567 ns；若仅取 host NVTX 内的 GPU 活动，会漏掉大部分异步 prefill 执行。

33 个 host step 中，前 32 个每步恰有 36 个激活热点；step 0 是 prefill，steps 1–31 是后续 decode；step 32 没有 kernel。因此实际是 **1 次 prefill + 31 次 decode 产生 32 个输出**。两份都另有 352 个 kernel 的 launch 在 host model-step 范围外，但仍位于整个请求窗口：11 种名称各出现 32 次，包括输出 GEMV、采样、index/copy 与状态更新。不能把它们当作丢失或删掉再算请求活动。

候选热点的名称仅为通用 `kernel`，本审计没有只靠这个名字做身份判断：还核对 36 层绑定记录、每有效步 36 次、其他 kernel 名称及计数两模式完全相同，以及 prefill/decode 的 launch grid。原生分别为 gridX/blockX = 7239/768、1/1024；候选为 347472/128、48/128，与 12,288 列、block256、4 warps 的已记录布局一致。仍未重建 JIT 二进制与 Python 函数的完整来源映射，不能把计数一致升级为二进制形式验证。

## 4. GPU 活动并集、阶段占比和可用结论

时间先保持整数 ns，再在表中换算 ms。对请求窗口内每条 kernel 和 memcpy 的 `[start,end]` 排序、合并所有重叠区间得到并集；两份数据库均没有 MEMSET 表，因此本次“kernel/copy/memset 并集”实际只含已记录的 kernel 和 copy。kernel 位于 stream 7，copy 位于 streams 7 与 13；不能将各 stream 时间直接相加。

| 独立复算 | native（ms） | schedule（ms） |
|---|---:|---:|
| Prefill 激活热点，36 次 | 11.218659 | 11.244366 |
| 31 步 decode 激活热点，1,116 次 | 2.369803 | 0.920376 |
| 激活热点总和，1,152 次 | 13.588462 | 12.164742 |
| 所有 kernel 时间之和 | 794.304335 | 795.635030 |
| kernel/copy 活动区间并集 | 794.342607 | 795.671638 |
| NVTX 请求窗口未被上述活动覆盖 | 56.506382 | 62.584354 |
| 热点与本进程其余已采活动的交集 | 0 | 0 |

热点占各自请求窗口 1.597047440% 与 1.417379210%。本轮候选 prefill 热点增加 0.025707 ms，decode 热点减少 1.449427 ms，合计减少 1.423720 ms。这支持“本次局部节省主要来自 decode 激活”；它**不直接解释**无 profile 配对请求中位数节省 1.342880 ms。两个 profile 各一次且独立启动，整体窗口反而相差 +7.407003 ms，不能把这个差直接当作候选的回归结论。

若教学上额外固定所有其他时间，并假定可把原生热点 13.588462 ms 完全消除，则本窗口的条件比值为：

```text
850.848989 / (850.848989 − 13.588462) = 1.016229669932
```

该假设不等于已经验证的依赖关键路径，也没有计入可否消除 host 提交开销；保留 README 的条件化说法即可。热点与其余已采 GPU 区间交集为 0，只能说明本请求记录中的这一类重叠没有出现，不能证明其他服务无干扰。

“未被已记录 GPU 活动覆盖”不能解释成 CPU/Python 时间、通信等待或整张 GPU 空闲。采样只覆盖被跟踪的进程树，而且 CPU 采样关闭。未采到的其他服务活动、GPU 争用和主机等待成因都不能从这个差值自动还原。

## 5. 诊断警告与记录完整性的边界

每份 `DIAGNOSTIC_EVENT` 有 21 行，已逐行按进程核对。父 Python 进程的“No CUDA events collected”“CUDA profiling might have not been started correctly”不能直接当成实际 worker 没有采到 CUDA；worker 的成功 profiler API、CUDA context 及数万条活动另有明确记录。但实际 worker 也各有“Not all CUDA events might have been collected”和“Not all NVTX events might have been collected”警告，报告保留它们，不能声明采集工具保证所有事件绝无遗漏。

native 的 worker 警告时间约 65.393–65.396 ms，早于本窗口；schedule 的约 66.103–66.106 ms 位于窗口内。不能统一声称“这些都发生在捕获前”。采集记录没有给出警告对应的具体丢失范围。本次能证明已记录请求的边界闭合、期望热点次数成立、全部 GPU 事件均找到成功 API 关联，以及诊断中的 CUDA 行计数与 Runtime+kernel+copy 行数一致；这些是内部一致性证据，**不能证明没有未留下记录的事件**。

此外，metadata 的 `CUDA_FLUSH_ON_CUDA_PROFILER_STOP=false` 与 worker 的提示“Buffers ... will be flushed on CudaProfilerStop”表述不完全一致。这里不根据其中任一个字段推定 flush 行为或丢失情况。没有执行 Nsight 重新导出，`.nsys-rep` 本次仅核 SHA-256；SQLite 与二进制报告之间的逐事件等价未独立重导验证。

因此适合的表述是“有两份包含完整固定请求区间、可重算调用与活动并集的已采 trace”。不宜写“整个进程全量无漏采”或用“完整”省略捕获范围。这并不推翻现有测量数字，而是规定它们能支持的判断。

## 6. 最小修正建议

1. **README 第 28 行，状态漂移。** 原文：“当前还缺同口径32-token替换前后完整Nsight trace、阶段占比/等待解释、并发与其他形状、基于稳态收益的成本摊销，因此5-9保持partial。”建议短句：“固定32-token替换前后trace及阶段热点占比已补入；等待成因、其他形状/并发、跨独立运行稳定性和稳态成本摊销仍待验证，因此保持partial。”这与第 43–75 行和当前原件对齐，保留未测条件。
2. **第 5 章第 295 行，正文旧状态。** 原文：“实验5-9同引擎替换前后记录尚缺，因此本图仅为分析，不声明真实请求收益。”建议短句：“实验5-9已有固定负载替换前后记录；本图仍采用教学时长，尚未用真实并发和资源依赖校准，不声明该图预测了请求收益。”第 305 行已有部分实测说明，可保留。
3. **生成源 outline.py 第 488 行，同句会回生。** 原文与上一条相同，建议同步使用同一句修订。否则下一次生成大纲会恢复旧状态。PLAN 第 110 行的“校准仍待补”仍有依据；PROGRESS 第 448 行若是历史日志，应补后续说明而非改写历史。

定位：[README](../../experiments/ch05/05-09/README.md)、[第 5 章](../../outlines/05-算子与运行时.md)、[outline.py](../../calculations/src/infra_calc/outline.py)。以上均交给用户/主代理统一修改，本审计不动原文件。

C31 教学 DAG 的 `actual_measured_request_ns=null` 继续保留；不能拿这次约 817 ms 请求给一个 80 μs 教学 DAG 填“实测”。不将本次 fixed-shape/eager、单请求局部实验外推到 CUDA Graph、Agent 自动优化、饱和服务、其他形状或全书核心实验已完成。README 关于没有稳定端到端收益、单轮 profile 不归因配对时延的保留是正确的，无须改成强结论。

上述行号及状态以本报告哈希快照为准；主代理/用户可能并发修正，交付后应按哈希和定位文本核对，不覆盖后来内容。

## 7. 读取与复算范围

- 完整阅读实验 README 1–75 行、engine-config 1–18 行、paired protocol 1–13 行、两份 profile command 各 1–20 行。大纲只读取 283–312 行；生成源/PLAN/PROGRESS/request_dag 仅搜索并定位本文所引行，没有扩读计算器实现。
- 完整解析 input、raw、requests.jsonl、selection-provenance、两个 manifest、两个 profile run 的 JSON 数据。input 的自然语言消息不作为任务质量评测；token 数组用于长度/身份，未调用 tokenizer。raw 的 28 条请求、全部 836 个客户端事件、144 个审计形状记录、24×36 个切换方法身份均程序核对。profile run 两份各 32 个事件核对。836 = 26×32 + 2×2。
- results/summary、profiles/analysis 完整解析后，仅交叉核对本文列出的客户端数字、阶段计数、热点时间与 GPU 并集；没有验证其所有高层分类、图像或分析器实现。`passed` 字段不参与通过条件。
- SQLite：两份数据库全量读取 StringIds、Runtime（29,471/28,319）、kernel（各 16,703）、memcpy（各 134）、NVTX（各 35）、DIAGNOSTIC_EVENT（各 21）；读取 PROCESSES、GPU、CUDA context 的身份行和 capture metadata 相关字段。CUDA_EVENT（各 134）、SYNCHRONIZATION（各 136）只核表/行数，未逐行解释。没有 MEMSET 表。未重导 `.nsys-rep`。
- manifest 所列 35 个文件全部存在且当前字节 SHA-256 匹配；源码、运行日志、SVG/PNG、二进制报告中未另列语义读取范围者只做哈希，不称为源码审计、日志因果分析或图片目视验收。额外 5 个相邻 5-6 选择来源仅核哈希。
- 以下保留可移植核算代码、机器可读结果和完整输入哈希。代码在仓库根目录以 Python 3 标准库执行；它只读取文件与 immutable SQLite，不调用仓库的 analyzer 或框架。结果里的“关联成功”指已记录事件与 API 的匹配，不表示重新执行成功。

## 8. 独立核算代码

代码块字节（UTF-8，不含围栏及末尾换行）SHA-256：`f55796cbd2b6d2c68bd8cad838f8f60b525af3951184b7ed2f2a03f17cb947dc`。最终版本已执行通过；后续展示的结果与其使用的同一批原件一致。

```python
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
from statistics import median
import json,sqlite3,math
p=Path('experiments/ch05/05-09')
raw=json.loads((p/'results/paired-eager-v1/raw.json').read_text())
protocol=json.loads((p/'results/paired-eager-v1/protocol.json').read_text())
inp=json.loads((p/'input.json').read_text())
jl=[json.loads(l) for l in (p/'results/paired-eager-v1/requests.jsonl').read_text().splitlines()]
reqs=raw['requests']; measured=[x for x in reqs if x['phase']=='measure']
assert len(reqs)==26 and len(raw['audits'])==2 and len(measured)==22 and len(jl)==22
assert raw['protocol']==protocol
assert len(inp['prompt_token_ids'])==7239
assert jl==measured
assert Counter((x['phase'],x['mode']) for x in reqs)=={('measure','native'):11,('measure','schedule'):11,('warmup','native'):2,('warmup','schedule'):2}
assert max(x['start_s']+x['latency_s'] for x in reqs if x['phase']=='warmup')<=min(x['start_s'] for x in measured)
source_checks=[]
for name,h in raw['source_hashes'].items():
 actual=sha256((p/name).read_bytes()).hexdigest()
 source_checks.append({'file':name,'expected':h,'actual':actual,'match':h==actual})
assert all(x['match'] for x in source_checks)
allreq=sorted(reqs+raw['audits'],key=lambda x:x['start_s'])
for x in allreq:
 n=x['output_tokens']
 assert x['prompt_tokens']==7239 and len(x['output_ids'])==n and len(x['events'])==n
 assert [e['token_count'] for e in x['events']]==list(range(1,n+1))
 t=[e['elapsed_s'] for e in x['events']]
 assert all(a<b for a,b in zip(t,t[1:]))
 assert t[0]==x['ttft_s'] and t[-1]<=x['latency_s']
for a,b in zip(allreq,allreq[1:]):
 assert a['start_s']+a['latency_s']<=b['start_s']
expected=measured[0]['output_ids']
assert all(x['output_ids']==expected for x in measured)
assert all(x['output_ids']==expected[:x['output_tokens']] for x in allreq)
audit_shapes=[]
for a in raw['audits']:
 records=[x for worker in a['records'] for x in worker]
 assert len(records)==72
 shape=Counter((tuple(x['shape']),x['dtype']) for x in records)
 assert shape=={((7239,24576),'torch.bfloat16'):36,((1,24576),'torch.bfloat16'):36}
 assert Counter(x['layer'] for x in records)=={f'model.layers.{i}.mlp.act_fn':2 for i in range(36)}
 audit_shapes.append({'mode':a['mode'],'records':len(records),'shape_counts':[[list(k[0]),k[1],v] for k,v in shape.items()]})
for sw in raw['switches']:
 assert len(sw)==1
 sw=sw[0];assert sw['layers']==36 and sw['audit']==False
 assert len(sw['methods'])==36
 assert {x['layer'] for x in sw['methods']}=={f'model.layers.{i}.mlp.act_fn' for i in range(36)}
 expected_method=('candidate','run') if sw['mode']=='schedule' else ('vllm.model_executor.layers.activation','SiluAndMul.forward_cuda')
 assert all((x['module'],x['name'])==expected_method for x in sw['methods'])
pairs=[]; metrics=[]
for trial in range(11):
 a=[x for x in measured if x['trial']==trial]
 assert len(a)==2 and {x['mode'] for x in a}=={'native','schedule'}
 by={x['mode']:x for x in a}
 pairs.append({'trial':trial,'order':[x['mode'] for x in a],
 'ttft_saving_ms':1000*(by['native']['ttft_s']-by['schedule']['ttft_s']),
 'latency_saving_ms':1000*(by['native']['latency_s']-by['schedule']['latency_s'])})
for mode in ['native','schedule']:
 xs=[x for x in measured if x['mode']==mode]
 metrics.append({'mode':mode,'ttft_median_ms':1000*median(x['ttft_s'] for x in xs),
 'latency_median_ms':1000*median(x['latency_s'] for x in xs),
 'client_mean_itl_median_ms':1000*median((x['events'][-1]['elapsed_s']-x['events'][0]['elapsed_s'])/(x['output_tokens']-1) for x in xs),
 'output_rate_median':median(x['output_tokens']/x['latency_s'] for x in xs)})
def union(intervals):
 out=[]
 for a,b in sorted(intervals):
  assert a<=b
  if a==b:continue
  if out and a<=out[-1][1]:out[-1][1]=max(b,out[-1][1])
  else:out.append([a,b])
 return out
def dur(xs):return sum(b-a for a,b in xs)
def intersection(a,b):
 i=j=0;total=0
 while i<len(a) and j<len(b):
  total+=max(0,min(a[i][1],b[j][1])-max(a[i][0],b[j][0]))
  if a[i][1]<b[j][1]:i+=1
  else:j+=1
 return total
reports=[];remaining_names=[]
for mode in ['native','schedule']:
 run=json.loads((p/'profiles'/mode/'run.json').read_text())
 assert run['request']['output_ids']==expected
 assert [e['tokens'] for e in run['request']['events']]==list(range(1,33))
 assert all(a['elapsed_s']<b['elapsed_s'] for a,b in zip(run['request']['events'],run['request']['events'][1:]))
 hashes=[]
 for n,h in run['source_hashes'].items():
  actual=sha256((p/n).read_bytes()).hexdigest();assert actual==h
  hashes.append({'file':n,'sha256':actual})
 cfg=dict(run['config']);cfg.pop('worker_extension_cls')
 old=dict(raw['config']);old.pop('worker_extension_cls');assert cfg==old
 db=p/'profiles'/f'{mode}.sqlite';c=sqlite3.connect(f'file:{db.resolve()}?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row
 strings={x['id']:x['value'] for x in c.execute('select * from StringIds')}
 nvs=[dict(x) for x in c.execute('select * from NVTX_EVENTS')]
 windows=[x for x in nvs if x['text']==f'replacement-{mode}-7239-32'];assert len(windows)==1
 window=windows[0];start,end=window['start'],window['end'];tid=window['globalTid'];pidmask=tid&~((1<<24)-1)
 pidrec=dict(c.execute('select * from PROCESSES where globalPid=?',(pidmask,)).fetchone())
 ctx=dict(c.execute('select * from TARGET_INFO_CUDA_CONTEXT_INFO').fetchone())
 assert pidrec['pid']==ctx['processId']
 steps=sorted([x for x in nvs if (x['text']or'').startswith('model-step-')],key=lambda x:int(x['text'].split('-')[-1]))
 assert len(steps)==33 and [x['text'] for x in steps]==[f'model-step-{i}' for i in range(33)]
 assert all(x['globalTid']==tid and start<=x['start']<=x['end']<=end for x in steps)
 runt=[dict(x) for x in c.execute('select * from CUPTI_ACTIVITY_KIND_RUNTIME')]
 launch={}
 for r in runt:
  if 'launch' in strings[r['nameId']].lower():
   key=(r['globalTid']&~((1<<24)-1),r['correlationId'])
   assert key not in launch
   launch[key]=r
 kernels=[dict(x) for x in c.execute('select * from CUPTI_ACTIVITY_KIND_KERNEL')]
 copies=[dict(x) for x in c.execute('select * from CUPTI_ACTIVITY_KIND_MEMCPY')]
 for x in copies:
  rs=[r for r in runt if r['correlationId']==x['correlationId'] and (r['globalTid']&~((1<<24)-1))==x['globalPid']]
  assert len(rs)==1 and rs[0]['returnValue']==0 and strings[rs[0]['nameId']]=='cudaMemcpyAsync_v3020'
  assert start<=rs[0]['start']<=rs[0]['end']<=end and rs[0]['start']<=x['start']
 hot=[];others=[];perstep=Counter();hotsteps=Counter();grids=defaultdict(set);outsteps=[];launch_before_end=0
 for k in kernels:
  key=k['globalPid'],k['correlationId'];assert key in launch
  r=launch[key];assert r['returnValue']==0
  assert r['start']<=k['start']<=k['end']
  assert k['globalPid']==pidmask and k['deviceId']==0
  assert start<=k['start']<=k['end']<=end and start<=r['start']<=r['end']<=end
  candidates=[i for i,s in enumerate(steps) if r['globalTid']==s['globalTid'] and s['start']<=r['start']<=s['end']]
  assert len(candidates)<=1
  ix=candidates[0] if candidates else None;perstep[ix]+=1
  if ix is None:outsteps.append(strings[k['demangledName']])
  name=strings[k['demangledName']]
  ishot=('vllm::act_and_mul_kernel' in name and 'silu_kernel' in name) if mode=='native' else name=='kernel'
  if ishot:
   hot.append(k);hotsteps[ix]+=1;grids[ix].add((k['gridX'],k['blockX']))
  else:others.append(k)
  if k['start']<r['end']:launch_before_end+=1
 assert len(launch)==len(kernels)==16703 and len(hot)==1152
 assert len({(k['globalPid'],k['correlationId']) for k in kernels})==len(kernels)
 assert {(k['globalPid'],k['correlationId']) for k in kernels}==set(launch)
 assert hotsteps=={i:36 for i in range(32)}
 assert perstep[32]==0 and perstep[None]==352
 assert all(start<=x['start']<=x['end']<=end and x['globalPid']==pidmask for x in copies)
 hu=union((x['start'],x['end']) for x in hot)
 ou=union((x['start'],x['end']) for x in others+copies)
 allu=union(hu+ou)
 stepdetail=[{'step':i,'host_start_ns':x['start'],'host_end_ns':x['end'],'kernels':perstep[i],'hotspots':hotsteps[i],
 'hotspot_ns':sum(k['end']-k['start'] for k in hot if launch[(k['globalPid'],k['correlationId'])]['globalTid']==x['globalTid'] and x['start']<=launch[(k['globalPid'],k['correlationId'])]['start']<=x['end']),
 'hotspot_gridX_blockX':sorted(grids[i])} for i,x in enumerate(steps)]
 diag=[dict(x) for x in c.execute('select timestamp,source,severity,text,globalPid from DIAGNOSTIC_EVENT')]
 for d in diag:
  rec=c.execute('select pid,name from PROCESSES where globalPid=?',(d['globalPid'],)).fetchone()
  d['process']=dict(rec) if rec else None
 report={'mode':mode,'sqlite_sha256':sha256(db.read_bytes()).hexdigest(),'target_pid':pidrec['pid'],'target_globalPid':pidmask,'target_globalTid':tid,
 'gpu':dict(c.execute('select id,name,totalMemory,smCount,computeMajor,computeMinor,uuid from TARGET_INFO_GPU').fetchone()),
 'window_start_end_ns':[start,end],'range_ns':end-start,'kernels':len(kernels),'launches':len(launch),'unique_successful_launch_associations':len(kernels),
 'runtime_rows':len(runt),'nvtx_rows':len(nvs),'copies':len(copies),'copy_bytes':sum(x['bytes'] for x in copies),'copy_streams':sorted(set(x['streamId'] for x in copies)),'successful_copy_associations':len(copies),'memset_table_exists':bool(c.execute("select 1 from sqlite_master where type='table' and name='CUPTI_ACTIVITY_KIND_MEMSET'").fetchone()),
 'hotspots':len(hot),'hotspot_sum_ns':sum(k['end']-k['start'] for k in hot),'kernel_sum_ns':sum(k['end']-k['start'] for k in kernels),
 'gpu_union_ns':dur(allu),'range_without_recorded_gpu_activity_ns':end-start-dur(allu),'hotspot_other_intersection_ns':intersection(hu,ou),
 'gpu_streams':sorted(set(k['streamId'] for k in kernels)),'hotspot_streams':sorted(set(k['streamId'] for k in hot)),
 'kernels_outside_host_step':len(outsteps),'outside_host_step_kernel_names':dict(Counter(outsteps)),
 'step_details':stepdetail,'trace_run_source_hashes':hashes,'diagnostics':diag,
 'profile_api_records':[{'name':strings[r['nameId']],'start':r['start'],'end':r['end'],'returnValue':r['returnValue'],'globalTid':r['globalTid']} for r in runt if 'Profiler' in strings[r['nameId']]],
 'events_all_inside_request_window':True,'config_matches_unprofiled_except_worker':True,'output_matches_unprofiled':True}
 remaining_names.append(Counter(strings[k['demangledName']] for k in others))
 reports.append(report);c.close()
assert remaining_names[0]==remaining_names[1]
summary=json.loads((p/'results/summary.json').read_text())
for m in metrics:
 a=next(x for x in summary['rows'] if x['mode']==m['mode'])
 for key,other in [('ttft_median_ms','median_ttft_ms'),('latency_median_ms','median_latency_ms'),('client_mean_itl_median_ms','median_client_mean_itl_ms'),('output_rate_median','median_request_output_tokens_per_s')]:
  assert math.isclose(m[key],a[other],abs_tol=1e-9)
recorded=json.loads((p/'profiles/analysis.json').read_text())
for r in reports:
 a=next(x for x in recorded['reports'] if x['mode']==r['mode'])
 for key,other in [('range_ns','range_ms'),('kernel_sum_ns','kernel_sum_ms'),('gpu_union_ns','observed_gpu_activity_union_ms'),('range_without_recorded_gpu_activity_ns','range_without_observed_gpu_activity_ms'),('hotspot_sum_ns','swiglu_sum_ms')]:
  assert math.isclose(r[key]/1e6,a[other],abs_tol=1e-9)
 assert r['kernels']==a['kernel_count']
 for s,t in zip(r['step_details'],a['steps']):
  assert s['step']==t['step'] and s['kernels']==t['kernel_count'] and s['hotspots']==t['swiglu_count']
  assert math.isclose(s['hotspot_ns']/1e6,t['swiglu_sum_ms'],abs_tol=1e-9)
manifest_checks=0
for mf in ['results/manifest.json','profiles/manifest.json']:
 for f,h in json.loads((p/mf).read_text())['files'].items():
  assert sha256((p/f).read_bytes()).hexdigest()==h
  manifest_checks+=1
assert manifest_checks==35
for f,h in json.loads((p/'selection-provenance.json').read_text()).items():
 assert sha256(Path(f).read_bytes()).hexdigest()==h
print(json.dumps({'request_audit':{'counts':{str(k):v for k,v in Counter((x['phase'],x['mode']) for x in allreq).items()},
 'jsonl_formal_records_identical_to_raw':True,'nonoverlap_order':True,'output_and_event_checks':True,'prompt_token_count':len(inp['prompt_token_ids']),
 'audit_shapes':audit_shapes,'source_checks':source_checks,'switch_records':len(raw['switches']),'metrics':metrics,'pairs':pairs,
 'paired_median_ttft_saving_ms':median(x['ttft_saving_ms'] for x in pairs),'paired_median_latency_saving_ms':median(x['latency_saving_ms'] for x in pairs),
 'positive_ttft_pairs':sum(x['ttft_saving_ms']>0 for x in pairs),'positive_latency_pairs':sum(x['latency_saving_ms']>0 for x in pairs)},
 'profile_audit':reports,'non_hotspot_kernel_name_counts_equal':True},ensure_ascii=False))
```

## 9. 机器可读核算结果

```json
{
  "request_audit": {
    "counts": {
      "('audit', 'native')": 1,
      "('warmup', 'native')": 2,
      "('audit', 'schedule')": 1,
      "('warmup', 'schedule')": 2,
      "('measure', 'native')": 11,
      "('measure', 'schedule')": 11
    },
    "jsonl_formal_records_identical_to_raw": true,
    "nonoverlap_order": true,
    "output_and_event_checks": true,
    "prompt_token_count": 7239,
    "audit_shapes": [
      {
        "mode": "native",
        "records": 72,
        "shape_counts": [
          [
            [
              7239,
              24576
            ],
            "torch.bfloat16",
            36
          ],
          [
            [
              1,
              24576
            ],
            "torch.bfloat16",
            36
          ]
        ]
      },
      {
        "mode": "schedule",
        "records": 72,
        "shape_counts": [
          [
            [
              7239,
              24576
            ],
            "torch.bfloat16",
            36
          ],
          [
            [
              1,
              24576
            ],
            "torch.bfloat16",
            36
          ]
        ]
      }
    ],
    "source_checks": [
      {
        "file": "run.py",
        "expected": "4f71b05db103f7420a92eb2dc4fb53d11018203e82881c63c2d853f34ef3a0a8",
        "actual": "4f71b05db103f7420a92eb2dc4fb53d11018203e82881c63c2d853f34ef3a0a8",
        "match": true
      },
      {
        "file": "replacement_worker.py",
        "expected": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499",
        "actual": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499",
        "match": true
      },
      {
        "file": "candidate.py",
        "expected": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
        "actual": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
        "match": true
      },
      {
        "file": "input.json",
        "expected": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8",
        "actual": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8",
        "match": true
      },
      {
        "file": "engine-config.json",
        "expected": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
        "actual": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
        "match": true
      },
      {
        "file": "selection-provenance.json",
        "expected": "a5639c6b7a2685d470026df61e2e4184ee79a4733c245b3651f2d1714f276277",
        "actual": "a5639c6b7a2685d470026df61e2e4184ee79a4733c245b3651f2d1714f276277",
        "match": true
      }
    ],
    "switch_records": 24,
    "metrics": [
      {
        "mode": "native",
        "ttft_median_ms": 435.6740349903703,
        "latency_median_ms": 816.6399830952287,
        "client_mean_itl_median_ms": 12.293385259146172,
        "output_rate_median": 39.184953789200485
      },
      {
        "mode": "schedule",
        "ttft_median_ms": 436.35313399136066,
        "latency_median_ms": 815.4057529754937,
        "client_mean_itl_median_ms": 12.249868032672712,
        "output_rate_median": 39.244265671696496
      }
    ],
    "pairs": [
      {
        "trial": 0,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.021861866116523743,
        "latency_saving_ms": 0.7492841687053442
      },
      {
        "trial": 1,
        "order": [
          "schedule",
          "native"
        ],
        "ttft_saving_ms": 0.48010190948843956,
        "latency_saving_ms": 2.4775280617177486
      },
      {
        "trial": 2,
        "order": [
          "schedule",
          "native"
        ],
        "ttft_saving_ms": 0.1200181432068348,
        "latency_saving_ms": 1.5088040381669998
      },
      {
        "trial": 3,
        "order": [
          "schedule",
          "native"
        ],
        "ttft_saving_ms": 0.5634061526507139,
        "latency_saving_ms": 1.3428800739347935
      },
      {
        "trial": 4,
        "order": [
          "schedule",
          "native"
        ],
        "ttft_saving_ms": -0.058502890169620514,
        "latency_saving_ms": 2.7885129675269127
      },
      {
        "trial": 5,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.6790990009903908,
        "latency_saving_ms": 0.12510502710938454
      },
      {
        "trial": 6,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.8492728229612112,
        "latency_saving_ms": -2.448658924549818
      },
      {
        "trial": 7,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.2853779587894678,
        "latency_saving_ms": -0.5395410116761923
      },
      {
        "trial": 8,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.7886409293860197,
        "latency_saving_ms": 4.614958772435784
      },
      {
        "trial": 9,
        "order": [
          "schedule",
          "native"
        ],
        "ttft_saving_ms": 1.399381784722209,
        "latency_saving_ms": 3.6393830087035894
      },
      {
        "trial": 10,
        "order": [
          "native",
          "schedule"
        ],
        "ttft_saving_ms": -0.32755802385509014,
        "latency_saving_ms": 1.0749988723546267
      }
    ],
    "paired_median_ttft_saving_ms": -0.058502890169620514,
    "paired_median_latency_saving_ms": 1.3428800739347935,
    "positive_ttft_pairs": 4,
    "positive_latency_pairs": 9
  },
  "profile_audit": [
    {
      "mode": "native",
      "sqlite_sha256": "2af0ce8efbec1167c6383cbe87f6674ca37b251fe929b36182c866707671f67a",
      "target_pid": 2283869,
      "target_globalPid": 319791940239360,
      "target_globalTid": 319791942523229,
      "window_start_end_ns": [
        93502219,
        944351208
      ],
      "range_ns": 850848989,
      "kernels": 16703,
      "launches": 16703,
      "unique_successful_launch_associations": 16703,
      "runtime_rows": 29471,
      "nvtx_rows": 35,
      "copies": 134,
      "copy_bytes": 31936,
      "copy_streams": [
        7,
        13
      ],
      "successful_copy_associations": 134,
      "memset_table_exists": false,
      "hotspots": 1152,
      "hotspot_sum_ns": 13588462,
      "kernel_sum_ns": 794304335,
      "gpu_union_ns": 794342607,
      "range_without_recorded_gpu_activity_ns": 56506382,
      "hotspot_other_intersection_ns": 0,
      "gpu_streams": [
        7
      ],
      "hotspot_streams": [
        7
      ],
      "kernels_outside_host_step": 352,
      "trace_run_source_hashes": [
        {
          "file": "profile_run.py",
          "sha256": "398328f90be2a099a31fd8bfed981a90e45dc5cdd28227418d73aeb0c348a7b6"
        },
        {
          "file": "trace_worker.py",
          "sha256": "1753509eb77c0417665c8601f867af895b9f09822318cd3ba04c4542a51ae8cb"
        },
        {
          "file": "replacement_worker.py",
          "sha256": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499"
        },
        {
          "file": "candidate.py",
          "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a"
        },
        {
          "file": "input.json",
          "sha256": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8"
        },
        {
          "file": "engine-config.json",
          "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84"
        }
      ],
      "profile_api_records": [
        {
          "name": "cuProfilerStart",
          "start": 93406287,
          "end": 93412844,
          "returnValue": 0,
          "globalTid": 319791942523229
        }
      ],
      "events_all_inside_request_window": true,
      "config_matches_unprofiled_except_worker": true,
      "output_matches_unprofiled": true,
      "gpu": {
        "id": 0,
        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        "totalMemory": 101973491712,
        "smCount": 188,
        "computeMajor": 12,
        "computeMinor": 0,
        "uuid": "not repeated; identical in the two original SQLite files"
      },
      "prefill_hotspot_ns": 11218659,
      "decode_hotspot_ns": 2369803,
      "each_effective_step_hotspot_count": 36,
      "effective_steps": 32,
      "last_host_step_kernel_count": 0,
      "diagnostics_rows": 21,
      "target_warning_texts": [
        "Not all NVTX events might have been collected.",
        "Not all CUDA events might have been collected."
      ],
      "profiled_client_ns": 850040737.0738685
    },
    {
      "mode": "schedule",
      "sqlite_sha256": "8664c28e5b3090760a2435352fb795e26e9fe1f0e35f9aae46ba3a31dc9cee2e",
      "target_pid": 2284861,
      "target_globalPid": 319808583237632,
      "target_globalTid": 319808585522493,
      "window_start_end_ns": [
        28642872,
        886898864
      ],
      "range_ns": 858255992,
      "kernels": 16703,
      "launches": 16703,
      "unique_successful_launch_associations": 16703,
      "runtime_rows": 28319,
      "nvtx_rows": 35,
      "copies": 134,
      "copy_bytes": 31936,
      "copy_streams": [
        7,
        13
      ],
      "successful_copy_associations": 134,
      "memset_table_exists": false,
      "hotspots": 1152,
      "hotspot_sum_ns": 12164742,
      "kernel_sum_ns": 795635030,
      "gpu_union_ns": 795671638,
      "range_without_recorded_gpu_activity_ns": 62584354,
      "hotspot_other_intersection_ns": 0,
      "gpu_streams": [
        7
      ],
      "hotspot_streams": [
        7
      ],
      "kernels_outside_host_step": 352,
      "trace_run_source_hashes": [
        {
          "file": "profile_run.py",
          "sha256": "398328f90be2a099a31fd8bfed981a90e45dc5cdd28227418d73aeb0c348a7b6"
        },
        {
          "file": "trace_worker.py",
          "sha256": "1753509eb77c0417665c8601f867af895b9f09822318cd3ba04c4542a51ae8cb"
        },
        {
          "file": "replacement_worker.py",
          "sha256": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499"
        },
        {
          "file": "candidate.py",
          "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a"
        },
        {
          "file": "input.json",
          "sha256": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8"
        },
        {
          "file": "engine-config.json",
          "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84"
        }
      ],
      "profile_api_records": [
        {
          "name": "cuProfilerStart",
          "start": 28574819,
          "end": 28579789,
          "returnValue": 0,
          "globalTid": 319808585522493
        }
      ],
      "events_all_inside_request_window": true,
      "config_matches_unprofiled_except_worker": true,
      "output_matches_unprofiled": true,
      "gpu": {
        "id": 0,
        "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        "totalMemory": 101973491712,
        "smCount": 188,
        "computeMajor": 12,
        "computeMinor": 0,
        "uuid": "not repeated; identical in the two original SQLite files"
      },
      "prefill_hotspot_ns": 11244366,
      "decode_hotspot_ns": 920376,
      "each_effective_step_hotspot_count": 36,
      "effective_steps": 32,
      "last_host_step_kernel_count": 0,
      "diagnostics_rows": 21,
      "target_warning_texts": [
        "Not all NVTX events might have been collected.",
        "Not all CUDA events might have been collected."
      ],
      "profiled_client_ns": 857566010.9054297
    }
  ],
  "non_hotspot_kernel_name_counts_equal": true
}
```

## 10. 输入哈希与读取快照

```json
{
  "snapshot_utc": "2026-09-09T06:34:27.161748+00:00",
  "manifest_entry_count": 35,
  "manifest_checks": [
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/analyze.py",
      "sha256": "4d6df3d1e6b5af21168de22a5dc9f443efe58c27079b51c321a5186335e0805a",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/candidate.py",
      "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/engine-config.json",
      "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/input.json",
      "sha256": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/paired-eager-v1.log",
      "sha256": "7517b3297a57579f22a5c26afe2585cf51eaa10214336c5b9a37b83c3ec4e36b",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/plot.py",
      "sha256": "ccf4260bae9dd547b7d85f66f4e499133f9d8423623bb9343ec112ab27a23721",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/replacement_worker.py",
      "sha256": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/comparison.png",
      "sha256": "7af75134bfaee829bb988e140dc123e4a0038c5f030b04214071518959ef9c75",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/comparison.svg",
      "sha256": "a7c557bb8f3f160621a04c6a61947301eca86dd365162425576d67ae04aed7fe",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/paired-eager-v1/gpu-activity.log",
      "sha256": "dfe877a611a9d80d6e71c2fb459f07330d3a7878ec4d6cfce82294df25f5141f",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/paired-eager-v1/protocol.json",
      "sha256": "a0bf0745d209729586d85d7c99ab96bfe9ba37bc919b442bec0355e005ad6039",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/paired-eager-v1/raw.json",
      "sha256": "7fa6f902e2329b082de9ebac2eb031689d9699bf0d7ac20259e99f107cf425ca",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/paired-eager-v1/requests.jsonl",
      "sha256": "55e2f8dab56782725d8f1d48ed5116e56007d649b8ce34eefa77d904f4b3fb58",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/results/summary.json",
      "sha256": "f133e9a7421a805d4232d10ecbd381ce0b567a3dc7332a6de4d99e8354c8b160",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/run.py",
      "sha256": "4f71b05db103f7420a92eb2dc4fb53d11018203e82881c63c2d853f34ef3a0a8",
      "matches": true
    },
    {
      "manifest": "results/manifest.json",
      "path": "experiments/ch05/05-09/selection-provenance.json",
      "sha256": "a5639c6b7a2685d470026df61e2e4184ee79a4733c245b3651f2d1714f276277",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/analyze_profiles.py",
      "sha256": "0a742d7596e4b7ebb39a876da27873240cdddc88031ffd4a3b813de7d06c2890",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/collect-profiles.log",
      "sha256": "ad190619ae1cb898ccb73c133439de6647e99cdf3e819877ffec2ba94f4bafa5",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/collect_profiles.py",
      "sha256": "80f6a6259cee3c341c5f63c44b0903d82a766026c17db95bbb2a208c6f8aa2e8",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/plot_profiles.py",
      "sha256": "66f7dec05c893eead4d599c85a0a714986a6d71dbaeb011bb27b01ae38ba6d53",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profile_run.py",
      "sha256": "398328f90be2a099a31fd8bfed981a90e45dc5cdd28227418d73aeb0c348a7b6",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/analysis.json",
      "sha256": "1c0b0783360f51a6a72db855ddb8032b70e2998fc298d8882907a32cb71fdc9b",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/comparison.png",
      "sha256": "63cd9bbe10a917cf4b1ca3ae986778ef2738b06f10579c8950a16a736ab0eccf",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/comparison.svg",
      "sha256": "9fc888cb9996e093b4136677989acc32215eefba2fd712db22ac8fcb339d4825",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/native/command.json",
      "sha256": "cf1e90e81f8dbabfd61bf6382934296cad76b91f31056a4856fb61b5a47ff250",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/native/run.json",
      "sha256": "b9a18c3ec5d83e0edcf1b0766434929ef8c5f4bd7bffaf3307f56dbec05a6575",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/native.log",
      "sha256": "f38508bf2983ff2d815bb6d0b15620b3eb58dec0771101b8df39327828523535",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/native.nsys-rep",
      "sha256": "323074193d287221c04253a0f756bcc5ca5dffe814f632485863795b19f5c47e",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/native.sqlite",
      "sha256": "2af0ce8efbec1167c6383cbe87f6674ca37b251fe929b36182c866707671f67a",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/schedule/command.json",
      "sha256": "a79e66efb80c23d6a6081cbaef40aba9f7a20aab2624e56ca09adbb45e316064",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/schedule/run.json",
      "sha256": "a63f208e7b3b6afc2c2b3d625f9a13e8eb7d6cdc0b10e75df8419fe3c7d05111",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/schedule.log",
      "sha256": "a5c598c0a52b73b91a62252b3433c315dff3c8fcc1a9ef336e80aa36abc9193d",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/schedule.nsys-rep",
      "sha256": "6fa7be3ede58bd406496f9d1468bdc8c49419006d8ae24dd4eae70ef68f5647c",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/profiles/schedule.sqlite",
      "sha256": "8664c28e5b3090760a2435352fb795e26e9fe1f0e35f9aae46ba3a31dc9cee2e",
      "matches": true
    },
    {
      "manifest": "profiles/manifest.json",
      "path": "experiments/ch05/05-09/trace_worker.py",
      "sha256": "1753509eb77c0417665c8601f867af895b9f09822318cd3ba04c4542a51ae8cb",
      "matches": true
    }
  ],
  "files": {
    "experiments/ch05/05-09/analyze.py": {
      "sha256": "4d6df3d1e6b5af21168de22a5dc9f443efe58c27079b51c321a5186335e0805a",
      "bytes": 3269,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/candidate.py": {
      "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
      "bytes": 545,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/engine-config.json": {
      "sha256": "987ec2ae698844783f6285d19df8307de5c53e755d19525028aa63a996eadd84",
      "bytes": 607,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/input.json": {
      "sha256": "0d1002b29cdb5b8c22d874ab2b79be39e9d70d87c4c05dc31a27848f5d6560e8",
      "bytes": 68255,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/paired-eager-v1.log": {
      "sha256": "7517b3297a57579f22a5c26afe2585cf51eaa10214336c5b9a37b83c3ec4e36b",
      "bytes": 11585,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/plot.py": {
      "sha256": "ccf4260bae9dd547b7d85f66f4e499133f9d8423623bb9343ec112ab27a23721",
      "bytes": 1424,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/replacement_worker.py": {
      "sha256": "4ffec5fbb9eceed2aef6833a65450a10d7765d415ead7427c35accd65e97a499",
      "bytes": 1365,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/comparison.png": {
      "sha256": "7af75134bfaee829bb988e140dc123e4a0038c5f030b04214071518959ef9c75",
      "bytes": 177410,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/comparison.svg": {
      "sha256": "a7c557bb8f3f160621a04c6a61947301eca86dd365162425576d67ae04aed7fe",
      "bytes": 90596,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/paired-eager-v1/gpu-activity.log": {
      "sha256": "dfe877a611a9d80d6e71c2fb459f07330d3a7878ec4d6cfce82294df25f5141f",
      "bytes": 15138,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/paired-eager-v1/protocol.json": {
      "sha256": "a0bf0745d209729586d85d7c99ab96bfe9ba37bc919b442bec0355e005ad6039",
      "bytes": 454,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/paired-eager-v1/raw.json": {
      "sha256": "7fa6f902e2329b082de9ebac2eb031689d9699bf0d7ac20259e99f107cf425ca",
      "bytes": 275157,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/paired-eager-v1/requests.jsonl": {
      "sha256": "55e2f8dab56782725d8f1d48ed5116e56007d649b8ce34eefa77d904f4b3fb58",
      "bytes": 47410,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/results/summary.json": {
      "sha256": "f133e9a7421a805d4232d10ecbd381ce0b567a3dc7332a6de4d99e8354c8b160",
      "bytes": 2767,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/run.py": {
      "sha256": "4f71b05db103f7420a92eb2dc4fb53d11018203e82881c63c2d853f34ef3a0a8",
      "bytes": 4336,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/selection-provenance.json": {
      "sha256": "a5639c6b7a2685d470026df61e2e4184ee79a4733c245b3651f2d1714f276277",
      "bytes": 602,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/analyze_profiles.py": {
      "sha256": "0a742d7596e4b7ebb39a876da27873240cdddc88031ffd4a3b813de7d06c2890",
      "bytes": 6125,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/collect-profiles.log": {
      "sha256": "ad190619ae1cb898ccb73c133439de6647e99cdf3e819877ffec2ba94f4bafa5",
      "bytes": 16288,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/collect_profiles.py": {
      "sha256": "80f6a6259cee3c341c5f63c44b0903d82a766026c17db95bbb2a208c6f8aa2e8",
      "bytes": 977,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/plot_profiles.py": {
      "sha256": "66f7dec05c893eead4d599c85a0a714986a6d71dbaeb011bb27b01ae38ba6d53",
      "bytes": 1336,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profile_run.py": {
      "sha256": "398328f90be2a099a31fd8bfed981a90e45dc5cdd28227418d73aeb0c348a7b6",
      "bytes": 2062,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/analysis.json": {
      "sha256": "1c0b0783360f51a6a72db855ddb8032b70e2998fc298d8882907a32cb71fdc9b",
      "bytes": 15129175,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/comparison.png": {
      "sha256": "63cd9bbe10a917cf4b1ca3ae986778ef2738b06f10579c8950a16a736ab0eccf",
      "bytes": 82610,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/comparison.svg": {
      "sha256": "9fc888cb9996e093b4136677989acc32215eefba2fd712db22ac8fcb339d4825",
      "bytes": 69258,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/native/command.json": {
      "sha256": "cf1e90e81f8dbabfd61bf6382934296cad76b91f31056a4856fb61b5a47ff250",
      "bytes": 733,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/native/run.json": {
      "sha256": "b9a18c3ec5d83e0edcf1b0766434929ef8c5f4bd7bffaf3307f56dbec05a6575",
      "bytes": 12079,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/native.log": {
      "sha256": "f38508bf2983ff2d815bb6d0b15620b3eb58dec0771101b8df39327828523535",
      "bytes": 11422,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/native.nsys-rep": {
      "sha256": "323074193d287221c04253a0f756bcc5ca5dffe814f632485863795b19f5c47e",
      "bytes": 1200812,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/native.sqlite": {
      "sha256": "2af0ce8efbec1167c6383cbe87f6674ca37b251fe929b36182c866707671f67a",
      "bytes": 3215360,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/schedule/command.json": {
      "sha256": "a79e66efb80c23d6a6081cbaef40aba9f7a20aab2624e56ca09adbb45e316064",
      "bytes": 739,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/schedule/run.json": {
      "sha256": "a63f208e7b3b6afc2c2b3d625f9a13e8eb7d6cdc0b10e75df8419fe3c7d05111",
      "bytes": 10352,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/schedule.log": {
      "sha256": "a5c598c0a52b73b91a62252b3433c315dff3c8fcc1a9ef336e80aa36abc9193d",
      "bytes": 11609,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/schedule.nsys-rep": {
      "sha256": "6fa7be3ede58bd406496f9d1468bdc8c49419006d8ae24dd4eae70ef68f5647c",
      "bytes": 1200145,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/profiles/schedule.sqlite": {
      "sha256": "8664c28e5b3090760a2435352fb795e26e9fe1f0e35f9aae46ba3a31dc9cee2e",
      "bytes": 3174400,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/trace_worker.py": {
      "sha256": "1753509eb77c0417665c8601f867af895b9f09822318cd3ba04c4542a51ae8cb",
      "bytes": 786,
      "scope": "hash-only unless detailed below"
    },
    "experiments/ch05/05-09/README.md": {
      "sha256": "84faec3de675a49eba17e845d503bd5c72f194829ff5a05076bb6193c2d1433f",
      "bytes": 7371,
      "lines": 75,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "experiments/ch05/05-09/results/manifest.json": {
      "sha256": "7d3a59c8be862012233fd22d3f12fd9dd277d326fcfb53196881fe93f842b59e",
      "bytes": 1575,
      "lines": 20,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "experiments/ch05/05-09/profiles/manifest.json": {
      "sha256": "6873c148072ba41d756096ea66bc572e0691d849bd7adbe3e8e73985af06ba2d",
      "bytes": 1879,
      "lines": 23,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "outlines/05-算子与运行时.md": {
      "sha256": "c6b49e705243e90ae37158f5eafed3afffffd1d1e0ce4d554ae37f19ce9d4b7c",
      "bytes": 51015,
      "lines": 349,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "calculations/src/infra_calc/outline.py": {
      "sha256": "c75d303fece275c44139c9856e72453749aeaeea231f43628a2805e0d3b05009",
      "bytes": 186524,
      "lines": 853,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "calculations/PLAN.md": {
      "sha256": "c1974d670885580fb31463ba4c2a2961a01124f936708f412d47f86c64e081da",
      "bytes": 62093,
      "lines": 251,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "calculations/PROGRESS.md": {
      "sha256": "5f3a0e8467ad730a08eeb0da51cd335778ad9f8b5e5fa8571cd534d3b9f3fc55",
      "bytes": 193791,
      "lines": 1354,
      "scope": "targeted lines or full JSON according to reading ranges"
    },
    "calculations/src/infra_calc/topics/request_dag.py": {
      "sha256": "eb1ef1af3b241aa67581b2ab4dd22b7b9bad67a32c3f257055b5f84fdd56b63c",
      "bytes": 6645,
      "lines": 86,
      "scope": "targeted lines or full JSON according to reading ranges"
    }
  },
  "selection_source_hash_checks": [
    {
      "path": "experiments/ch05/05-06/schedule.py",
      "sha256": "6a8ca69e1d23c6dd60ec5e1f9725fce18c889d69ff66ccc13453694444271d0a",
      "bytes": 545,
      "match": true,
      "scope": "hash-only; no execution or source semantics claimed"
    },
    {
      "path": "experiments/ch05/05-06/protocol.json",
      "sha256": "893989ea9e1ce8950315e0f2c7f45848fa165d7f75301c458defa02171988c62",
      "bytes": 1255,
      "match": true,
      "scope": "hash-only; no execution or source semantics claimed"
    },
    {
      "path": "experiments/ch05/05-06/results/schedule-summary.json",
      "sha256": "85e49da5c5a240a51647bb32a8f871ae3fb75786995eb5ddce78f00e09d7eed2",
      "bytes": 3719,
      "match": true,
      "scope": "hash-only; no execution or source semantics claimed"
    },
    {
      "path": "experiments/ch05/05-06/results/schedule-heldout.json",
      "sha256": "9138e4876e8c53f2a1272081afabdbd544a88714571a0b4b0d0c49400e76ab19",
      "bytes": 2329,
      "match": true,
      "scope": "hash-only; no execution or source semantics claimed"
    },
    {
      "path": "experiments/ch05/05-06/results/interleaved-summary.json",
      "sha256": "eb8369e30af72a25894825064cf46f68262b9dcb6f22a3b04214fc9013970ec1",
      "bytes": 8103,
      "match": true,
      "scope": "hash-only; no execution or source semantics claimed"
    }
  ]
}
```
