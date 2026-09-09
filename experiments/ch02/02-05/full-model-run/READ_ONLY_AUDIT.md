# 只读源码、metadata 与资源核对

最终资源时间：2026-09-09T05:31:52.462639+00:00。这是瞬时共享状态，不是容量通过证据。原始数据：[resources-current.json](read-only-final/resources-current.json)。

MemAvailable **125.689 GiB**；候选建议启动门槛124GiB，当前不满足。

```text
0, GPU-592644b2-d169-3424-56fd-98aea433ef09, NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 97887, 60956, 36294, 0
5875, /home/ubuntu/OpenRealtime/.runtime/sensevoice/bin/python, 1192
1953199, /home/ubuntu/OpenRealtime/.runtime/fish-env/bin/python, 6666
1970308, /home/ubuntu/OpenRealtime/.runtime/sensevoice/bin/python, 1718
1219611, /home/ubuntu/OpenRealtime/.runtime/sensevoice/bin/python, 1684
3614304, VLLM::EngineCore, 49664
```

GPU空闲36,294MiB，低于建议启动门槛71,680MiB。上述PID显存是实测快照；不等于可无条件释放的内存。本准备未发送任何信号，也未调用服务控制。没有用资源快照推断其他session的RL已经结束。

| PID | 进程 | RSS GiB | anon GiB |
|---:|---|---:|---:|
| 3204383 | openroad | 23.014 | 22.955 |
| 1953199 | python | 19.067 | 18.993 |
| 3614304 | VLLM::EngineCor | 3.087 | 2.921 |
| 1970308 | python | 2.824 | 2.751 |
| 1219611 | python | 1.599 | 1.530 |
| 5875 | python | 1.553 | 1.473 |
| 1816705 | queqiaod | 1.329 | 1.321 |
| 3613078 | python | 0.989 | 0.975 |
| 3455821 | claude | 0.697 | 0.631 |
| 2388395 | codex | 0.580 | 0.527 |

OpenROAD的RSS/anon仅作系统余量解释，不操作其进程、文件或服务。vLLM/Fish是否释放由root决定；即便释放它们，也不能保证达到124GiB主存门槛。RSS/anon和MemAvailable之间不能简单相加当容量证明。

## Cached模型metadata

固定revision `7872f01b1d1fe23eabc4c98b48bffcef5a386062`；43层、48分片；stat文件大小合计 **166,886,535,336 bytes = 155.425198 GiB**。st_blocks磁盘分配合计166,886,813,696 bytes另存原始json。完整config的compress_ratios为46项，保留原样。

仅读取config/index/tokenizer/encoder及stat，不读取分片tensor数据、复制权重、下载或重算模型参数账。只对小metadata、tokenizer、源码和少量编译缓存做SHA。分片记录包含真实symlink目标、大小、mtime；这些不替代完整payload哈希。

## 私有依赖与源码路径

- Python：`/home/ubuntu/ai-infra-book-experiments/tools/sglang0513-venv/bin/python`（实际3.10）。
- SGLang0.5.13.post1；torch运行版本2.11.0+cu130（distribution版本2.11.0）；Transformers5.8.1；TileLang0.1.8；apache-tvm-ffi0.1.9；Triton3.6.0；FlashInfer0.6.12。完整发行包版本见prepared/resolved-serverargs.json。
- 私有CUDA_HOME=`tools/flashinfer-cuda130/nvidia/cu13`，实测nvcc13.0.88。venv同时存在13.2版nvcc发行包；本候选显式选13.0根，不能笼统把venv全部CUDA组件称13.0。
- CCCL使用venv现有`nvidia/cu13/include/cccl`；原native include-overlay指向一致；nv/target和12个成功TVM/TileLang种子文件均有SHA。

6份实际源码均与安装wheel RECORD匹配：server_args、deepseek_v4_hook、offloader、deepseek_v4模型、pool_configurator、engine。源码副本在prepared/sources；完整路径、SHA、RECORD比对在read-only-final/toolchain-audit.json。

| 核对点 | 实际源码依据 | 含义 |
|---|---|---|
| OffloaderV1 | utils/offloader.py:64–155 | cpu_offload_gb>0走官方V1；逐参数CPU存储，forward设备复制；预算不是精确RSS |
| V4/SM120配置 | server_args.py:2109–2120；arg_groups/deepseek_v4_hook.py | dsv4/page256/fp8 KV，SM120使用marlin并关闭不支持特化 |
| DSV4池 | model_executor/pool_configurator.py:_compute_dsv4_sizes、_to_config | full按page对齐，SWA按ratio；状态池按模型参数创建；需看真实运行日志 |
| 实际请求 | entrypoints/engine.py:generate | 本包使用input_ids，原始response包含output_ids/text/finish的先例来自attempt05 |
| no-thinking | metadata/encoding/encoding_dsv4.py:encode_messages、encoding/README.md | chat模式官方关闭thinking，原tokenizer无HF chat_template |

准备在实际私有环境进行了ServerArgs构造与原tokenizer加载，但没有Engine构造。最终ServerArgs确认context4096、max_total_tokens4096、ratio1.0、dsv4、marlin、page256、fp8_e4m3，完整requested/resolved全部保存。运行时默认处理仍以ready/server_info及完整引擎日志为准。

## 未确定项

完整模型加载峰值、最终实际池、全部43层真实输出、首题编译耗时、共享状态变化、CPUoffload独立传输/增量耗时均未实测。默认护栏可能保守拒绝；不能称96GiB为最低需求。M8严格数值门槛10/32768失败不被本准备或未来答对覆盖。
