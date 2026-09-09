# kv-trace — 

输入：`{"run": "large"}`

KV块与调度来自封存引擎记录，字节容量按官方模型配置复算。

| 结果 | 值 |
| --- | ---: |
| run | `"large"` |
| total_blocks | 910 |
| reserved_blocks | 1 |
| block_bytes | 2,359,296 |
| peak_request_blocks | 512 |
| peak_request_payload_capacity_bytes | 1,207,959,552 |
| snapshots | 1,053 |
| preemption_count | 0 |
| scheduled_token_positions | 8,188 |
| extra_small_run_scheduled_positions | 1,805 |
| cancel_released_blocks | 104 |
| cancel_release_after_return_s | 0.02985778101719916 |
| all_request_blocks_released | `true` |
| small_large_outputs_match | `true` |
| cancel_survivors_match | `true` |

计量条件：

- 实验8-3真实RTX PRO 6000／vLLM0.23.0／Qwen3-8B BF16固定revision，四条1536-token输入、强制512输出，APC关闭、eager、同步调度，设备有其它服务。每条件单次新引擎，不是统计性能结论。
- 原始21文件封存SHA校验，官方KV几何每token144KiB、16-token块2.25MiB；池包含一个null保留块，不属于请求。APC关闭时逐快照核对free+owned+reserved=total、块不重复、引用为1。
- 记录调度token位置与输出token分别计量。抢占保留输出历史、computed清零并归还块；small相对large多调度位置不能叫额外输出，也不能按相同成本位置直接变成FLOPs或时间。
- 取消API返回与scheduler finish_after观察时刻分开，释放按前后空闲差与被取消请求拥有块核对；观察有同步trace开销，时间不代表无观测实现的精确取消延迟。
- 块容量不等于全部有效KV字节，尾块可能未满。本模型不从瞬间tokens字段推断执行完成的KV长度；APC共享、缓存空闲块与copy-on-write未在此实验中测量。

固定来源：

- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
- [sources/kv-traces/cancel.log](../../experiments/ch08/08-03/cancel.log)，SHA256 `2cf4f22ea2bde8ae10920ac3ac7a909799b243e56570dfb4597d8190dbfdd7ce`。
- [sources/kv-traces/large.log](../../experiments/ch08/08-03/large.log)，SHA256 `05784b72cb9cd8fe7f1bd3569770006300eb2e1df0a40bfd5adee8d8e2d65d5d`。
- [sources/kv-traces/observer.py](../../experiments/ch08/08-03/observer.py)，SHA256 `bf76a3685260e2941cb616a7f8992df726655a588c02fbc468384663f090a383`。
- [sources/kv-traces/results/cancel/actions.jsonl](../../experiments/ch08/08-03/results/cancel/actions.jsonl)，SHA256 `162bf48f5380e7574ebe77b991208e18ed920982b711ea4b9ebc2e685e272de6`。
- [sources/kv-traces/results/cancel/blocks.jsonl](../../experiments/ch08/08-03/results/cancel/blocks.jsonl)，SHA256 `57c88d4c21573d6464a43542af7fd1b83022475642efbda8492debbfcff247e8`。
- [sources/kv-traces/results/cancel/environment.json](../../experiments/ch08/08-03/results/cancel/environment.json)，SHA256 `a6179af9faccd7e5dce20ed0c91ff6b72b53b621abed9344829fdace1bfd9add`。
- [sources/kv-traces/results/cancel/inputs.json](../../experiments/ch08/08-03/results/cancel/inputs.json)，SHA256 `9812fe4642aad1391ce902b33d1dd4d98ef82de7209470de99178e797752f0f3`。
- [sources/kv-traces/results/cancel/requests.jsonl](../../experiments/ch08/08-03/results/cancel/requests.jsonl)，SHA256 `f39706d24261f586b0550107d69532e833e59ca2d7b6dc480803e1800947c1a8`。
- [sources/kv-traces/results/large/actions.jsonl](../../experiments/ch08/08-03/results/large/actions.jsonl)，SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- [sources/kv-traces/results/large/blocks.jsonl](../../experiments/ch08/08-03/results/large/blocks.jsonl)，SHA256 `ca251bdfdc61ff83ec574be6a47612e82a9f840f7ae4d4e879263ea0a7fb93fe`。
- [sources/kv-traces/results/large/environment.json](../../experiments/ch08/08-03/results/large/environment.json)，SHA256 `36fbf47662078e4236095b3f0497c8d8c84aa93c385a2237b7ec7bd13072b367`。
- [sources/kv-traces/results/large/inputs.json](../../experiments/ch08/08-03/results/large/inputs.json)，SHA256 `9812fe4642aad1391ce902b33d1dd4d98ef82de7209470de99178e797752f0f3`。
- [sources/kv-traces/results/large/requests.jsonl](../../experiments/ch08/08-03/results/large/requests.jsonl)，SHA256 `2818bed22a5647645e7ccd8c764385bd9792fac495a33c4db7e0db3fb0d35764`。
- [sources/kv-traces/results/native-source-manifest.json](../../experiments/ch08/08-03/results/native-source-manifest.json)，SHA256 `8904553b5e92f16cb49e2b938ec075b5ba3e9d48febc6c54028397abda4c60b7`。
- [sources/kv-traces/results/small/actions.jsonl](../../experiments/ch08/08-03/results/small/actions.jsonl)，SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- [sources/kv-traces/results/small/blocks.jsonl](../../experiments/ch08/08-03/results/small/blocks.jsonl)，SHA256 `2a7b7bf82aa359c358d1031d4b26855ae11ce2146ad23d9ac23148502e0ce800`。
- [sources/kv-traces/results/small/environment.json](../../experiments/ch08/08-03/results/small/environment.json)，SHA256 `a5228d71d287cb13573d5e47dc1aa0426f60ea36a1895affaeee4dc1a322a3df`。
- [sources/kv-traces/results/small/inputs.json](../../experiments/ch08/08-03/results/small/inputs.json)，SHA256 `9812fe4642aad1391ce902b33d1dd4d98ef82de7209470de99178e797752f0f3`。
- [sources/kv-traces/results/small/requests.jsonl](../../experiments/ch08/08-03/results/small/requests.jsonl)，SHA256 `153695038951bdb976d82f8c8aaf5cf1e38a411d03dbdf8dbfa076defa36c6f9`。
- [sources/kv-traces/run.py](../../experiments/ch08/08-03/run.py)，SHA256 `b9f7afe1f915b212adc55c8d415be3464366bef047d4c438c248ae9fe2147d3a`。
- [sources/kv-traces/small.log](../../experiments/ch08/08-03/small.log)，SHA256 `6cc7be9d4f4f0d2b6fb889172a1c95ffb45aaeb991869ef14a3c4fb61e5450b4`。
