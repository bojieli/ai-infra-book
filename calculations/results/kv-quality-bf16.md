# kv-quality — 

输入：`{"run": "bf16"}`

容量、输出和时间来自封存KV实验；自然质量与固定输出计时分开，含Q精度控制。

| 结果 | 值 |
| --- | ---: |
| distinct_tasks | 8 |
| formal_requests | 64 |
| natural_executions | 32 |
| natural_correct | 28 |
| natural_output_lengths | `[46]` |
| natural_length_stops | 0 |
| natural_stop_reasons | `["stop"]` |
| blocks | 5,461 |
| token_slots | 87,376 |
| storage_bytes | 12,884,115,456 |
| bytes_per_token | 147,456 |

| 文档行 | 并发 | 模式 | 正确／请求 | 输出token | 自然截断 | 中位完成秒 | 批次窗口秒 | 输出token/s |
| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: |
| 128 | 1 | natural | 8/8 | 368 | 0 | 1.5190279595553875 | 12.377959392033517 | 29.730263959085665 |
| 128 | 1 | fixed | None/8 | 512 | None | 2.149120555142872 | 17.15030735102482 | 29.85369238700001 |
| 128 | 4 | natural | 8/8 | 368 | 0 | 1.7494611075380817 | 3.5010416011791676 | 105.11157590245595 |
| 128 | 4 | fixed | None/8 | 512 | None | 2.4017993960296735 | 4.840127383824438 | 105.78233988450155 |
| 512 | 1 | natural | 6/8 | 368 | 0 | 1.8844503849977627 | 15.256827051984146 | 24.120349450519708 |
| 512 | 1 | fixed | None/8 | 512 | None | 2.4984601074829698 | 19.896142257144675 | 25.73363184594951 |
| 512 | 4 | natural | 6/8 | 368 | 0 | 3.312515419907868 | 6.660100067034364 | 55.254425053085505 |
| 512 | 4 | fixed | None/8 | 512 | None | 3.553782845963724 | 7.141652578022331 | 71.69209008789157 |

计量条件：

- 导入实验8-8三条件的原始manifest封存文件，核对配置、源码、输入文档与答案、实际KV张量、独立校准与冻结scale。没有重跑GPU或替换错误输出。
- 自然检索答案严格JSON判定，拒绝重复键／多余文字／错误值；固定64输出只计工作与时长，不以其后续文本评价自然答案。每格式32次自然执行仅八个不同任务，不能当作32个独立质量样本。
- BF16／FP8／FP8+BF16 Q都保持BF16权重；原FP8引擎路径同时改变Q量化，后续控制组实际观察36层Q为BF16且KV scales匹配。不能将原两组差异全部归于KV位宽。
- 固定12GiB KV预算，BF165461块、FP810922块，唯一storage字节相同；较小元素换更多token槽，不是实际分配减半，也未实测最大可接纳并发或DRAM流量。
- 时间为同批次起止区间，统计自然和固定长度分开；格式顺序运行、共享GPU、仅两轮，Q观察控制组另有Python回调开销，不用于确定微小速度排名。没有重试，错误请求的时间不含修正答案成本。

固定来源：

- [sources/kv-quality/results/raw-manifest.json](../../experiments/ch08/08-08/results/raw-manifest.json)，SHA256 `44551151662c0afe261e956c20c9eb6cdfe85772ab3fd103112c436631f5ee25`。
- [sources/kv-quality/bf16.log](../../experiments/ch08/08-08/bf16.log)，SHA256 `e41df171ab01e1dfdeadd51ba094ecfc8ac89df33aa7c5940af856bdb61d53ce`。
- [sources/kv-quality/fp8.log](../../experiments/ch08/08-08/fp8.log)，SHA256 `1c92b613166ad03959f79efc1c1d191ed0d3108b890ccfd9a5c5fb1357473139`。
- [sources/kv-quality/probe.py](../../experiments/ch08/08-08/probe.py)，SHA256 `49871f42c485f91e411419713ffb952532703d642973e352f8e4eb1d48c3019b`。
- [sources/kv-quality/results/bf16/batches.jsonl](../../experiments/ch08/08-08/results/bf16/batches.jsonl)，SHA256 `be1810ee98e0eb310303d819295998c43e055817cb47bcf8ed0583dcec019260`。
- [sources/kv-quality/results/bf16/environment.json](../../experiments/ch08/08-08/results/bf16/environment.json)，SHA256 `e0b6926200f0eb14669ff4049c29f1362270a7f9f468c10b4802200efc69dd29`。
- [sources/kv-quality/results/bf16/inputs.json](../../experiments/ch08/08-08/results/bf16/inputs.json)，SHA256 `266d2962df37194fa68c6e7417236767897ea78a97710227e0a29fe24685debe`。
- [sources/kv-quality/results/bf16/kv-snapshots.json](../../experiments/ch08/08-08/results/bf16/kv-snapshots.json)，SHA256 `198925af4c9979c679391ec88a79ca62e1b4d58f085ec4f5e06c8c1a8a98d45e`。
- [sources/kv-quality/results/bf16/requests.jsonl](../../experiments/ch08/08-08/results/bf16/requests.jsonl)，SHA256 `49499b415abb3bb478c5cb98feca17e894e579fc44a105dd7febbc34baae4db4`。
- [sources/kv-quality/results/fp8/batches.jsonl](../../experiments/ch08/08-08/results/fp8/batches.jsonl)，SHA256 `633d74269c0c94453a9548d85f4df722ce3796bd1ecc80a993d00dcef1e300bb`。
- [sources/kv-quality/results/fp8/environment.json](../../experiments/ch08/08-08/results/fp8/environment.json)，SHA256 `f14fb3210ebc4e9db76e41380dc8f647cc2d765f4241f8813f0346ed5e221c1a`。
- [sources/kv-quality/results/fp8/inputs.json](../../experiments/ch08/08-08/results/fp8/inputs.json)，SHA256 `266d2962df37194fa68c6e7417236767897ea78a97710227e0a29fe24685debe`。
- [sources/kv-quality/results/fp8/kv-snapshots.json](../../experiments/ch08/08-08/results/fp8/kv-snapshots.json)，SHA256 `37e08e23ddccb8114d8e93269a35ca9ff20398cf37239976fb648505a948a94f`。
- [sources/kv-quality/results/fp8/requests.jsonl](../../experiments/ch08/08-08/results/fp8/requests.jsonl)，SHA256 `8bf33e62a7c83777027ff46f324de54b2cfd4133b31dff6d51dfcc1a064fbec5`。
- [sources/kv-quality/results/native-source-manifest.json](../../experiments/ch08/08-08/results/native-source-manifest.json)，SHA256 `de14235bd017296ec72fcf13b6334cc0c5e749d0c69e0dd04308db35267debfc`。
- [sources/kv-quality/run.py](../../experiments/ch08/08-08/run.py)，SHA256 `aaa00d392950029319bfde669861b0663976bf46472e6b1c70578405f30af998`。
- [sources/kv-quality/results/followup-manifest.json](../../experiments/ch08/08-08/results/followup-manifest.json)，SHA256 `05fa0381a5a72a4eed8c9e343eb782185737b3859d7f3e0db007ce975de25c2a`。
- [sources/kv-quality/fp8_qbf16.log](../../experiments/ch08/08-08/fp8_qbf16.log)，SHA256 `7b8306707827064b70714bb8e89820e40fa0b9605dc0569f4b47409e2becbf45`。
- [sources/kv-quality/probe_qbf16.py](../../experiments/ch08/08-08/probe_qbf16.py)，SHA256 `b2490beeb349e8ba2f6704ab8aa2c69770f94c989be65b34785d6b5a81f7aa30`。
- [sources/kv-quality/results/fp8_qbf16/batches.jsonl](../../experiments/ch08/08-08/results/fp8_qbf16/batches.jsonl)，SHA256 `236c48f05fc91965089862a0dfe81a74032285f4ad302f0153908f10647957a1`。
- [sources/kv-quality/results/fp8_qbf16/environment.json](../../experiments/ch08/08-08/results/fp8_qbf16/environment.json)，SHA256 `a291f76546d819e780af09316d7ecb1220edec9894dd59af15b8e69ed388cf7e`。
- [sources/kv-quality/results/fp8_qbf16/inputs.json](../../experiments/ch08/08-08/results/fp8_qbf16/inputs.json)，SHA256 `266d2962df37194fa68c6e7417236767897ea78a97710227e0a29fe24685debe`。
- [sources/kv-quality/results/fp8_qbf16/kv-snapshots.json](../../experiments/ch08/08-08/results/fp8_qbf16/kv-snapshots.json)，SHA256 `e4932aa1bee686346c08a408ff807c4482b02aae297e6f254fd819d74aee9749`。
- [sources/kv-quality/results/fp8_qbf16/requests.jsonl](../../experiments/ch08/08-08/results/fp8_qbf16/requests.jsonl)，SHA256 `9c0f969025c7fea6c3d63cd1706b2fb534b9baaca4154cf45f2d2e60b2655f7e`。
- [sources/kv-quality/run_qbf16.py](../../experiments/ch08/08-08/run_qbf16.py)，SHA256 `a135ad6cde07916b08d25a2f0c771abc8e608f76c91825a70b2684d49a04fcfc`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
