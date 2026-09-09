# cache-missing — 

输入：`{"experiment": "9-8 missing pages"}`

缺页恢复及输出来自封存实验，原页／恢复页逐BF16元素核验；不推断差异原因。

| 结果 | 值 |
| --- | ---: |
| cases | 2 |
| requests | 6 |
| device_control_full_requests | 3 |
| device_control_prefix_requests | 1 |
| outputs_match_reference | `true` |

显存分段控制v2：前置512输入、1输出；随后device命中512／1008／1008。

| KV页比较 | 元素数 | 不同BF16元素 | 最大绝对差 |
| --- | ---: | ---: | ---: |
| full_vs_device | 1179648 | 1021226 | 13.5625 |
| storage_vs_device | 1179648 | 992972 | 26.53125 |

| 条件 | get页数 | get bytes | 首次复用token | 重算token | 不同BF16元素 | 最大绝对差 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| first | 0 | 0 | 0 | 1024 | 0 | 0.0 |
| middle | 32 | 75497472 | 512 | 512 | 995403 | 26.75 |

| 条件 | 请求 | 缓存token | 剩余prefill token | prefill FLOPs |
| --- | ---: | ---: | ---: | ---: |
| first | 0 | 0 | 1024 | 14535715979264 |
| first | 1 | 1008 | 16 | 233102114816 |
| first | 2 | 1008 | 16 | 233102114816 |
| middle | 0 | 512 | 512 | 7345789730816 |
| middle | 1 | 1008 | 16 | 233102114816 |
| middle | 2 | 1008 | 16 | 233102114816 |

| 条件 | 层 | K/V不同元素 | 最大绝对差 |
| --- | ---: | ---: | ---: |
| first | 0 | 0 | 0.0 |
| first | 1 | 0 | 0.0 |
| first | 2 | 0 | 0.0 |
| first | 3 | 0 | 0.0 |
| first | 4 | 0 | 0.0 |
| first | 5 | 0 | 0.0 |
| first | 6 | 0 | 0.0 |
| first | 7 | 0 | 0.0 |
| first | 8 | 0 | 0.0 |
| first | 9 | 0 | 0.0 |
| first | 10 | 0 | 0.0 |
| first | 11 | 0 | 0.0 |
| first | 12 | 0 | 0.0 |
| first | 13 | 0 | 0.0 |
| first | 14 | 0 | 0.0 |
| first | 15 | 0 | 0.0 |
| first | 16 | 0 | 0.0 |
| first | 17 | 0 | 0.0 |
| first | 18 | 0 | 0.0 |
| first | 19 | 0 | 0.0 |
| first | 20 | 0 | 0.0 |
| first | 21 | 0 | 0.0 |
| first | 22 | 0 | 0.0 |
| first | 23 | 0 | 0.0 |
| first | 24 | 0 | 0.0 |
| first | 25 | 0 | 0.0 |
| first | 26 | 0 | 0.0 |
| first | 27 | 0 | 0.0 |
| first | 28 | 0 | 0.0 |
| first | 29 | 0 | 0.0 |
| first | 30 | 0 | 0.0 |
| first | 31 | 0 | 0.0 |
| first | 32 | 0 | 0.0 |
| first | 33 | 0 | 0.0 |
| first | 34 | 0 | 0.0 |
| first | 35 | 0 | 0.0 |
| middle | 0 | 0 | 0.0 |
| middle | 1 | 20588 | 0.25 |
| middle | 2 | 23303 | 0.125 |
| middle | 3 | 24260 | 0.0625 |
| middle | 4 | 25795 | 0.25 |
| middle | 5 | 25121 | 0.5 |
| middle | 6 | 25736 | 0.25 |
| middle | 7 | 25915 | 0.125 |
| middle | 8 | 27225 | 0.25 |
| middle | 9 | 27309 | 0.1484375 |
| middle | 10 | 27814 | 0.5 |
| middle | 11 | 27888 | 0.25 |
| middle | 12 | 27970 | 0.390625 |
| middle | 13 | 28798 | 0.53125 |
| middle | 14 | 29046 | 1.515625 |
| middle | 15 | 29569 | 2.2421875 |
| middle | 16 | 30083 | 8.3515625 |
| middle | 17 | 30230 | 3.125 |
| middle | 18 | 30487 | 6.734375 |
| middle | 19 | 30112 | 5.4609375 |
| middle | 20 | 30318 | 6.015625 |
| middle | 21 | 30202 | 7.5 |
| middle | 22 | 29945 | 5.890625 |
| middle | 23 | 29998 | 7.0625 |
| middle | 24 | 30020 | 9.046875 |
| middle | 25 | 29639 | 8.59765625 |
| middle | 26 | 30205 | 6.734375 |
| middle | 27 | 29835 | 7.5703125 |
| middle | 28 | 29782 | 6.96875 |
| middle | 29 | 30063 | 7.0625 |
| middle | 30 | 29901 | 9.828125 |
| middle | 31 | 29905 | 8.890625 |
| middle | 32 | 29617 | 9.703125 |
| middle | 33 | 29994 | 20.703125 |
| middle | 34 | 29527 | 26.75 |
| middle | 35 | 29203 | 15.484375 |

计量条件：

- 封存缺页0／32两个独立恢复实例，原页复用cache-restart已归档载荷；恢复页实际bytes与SHA核验。其余64页未改变的结论来自前后文件清单，未再复制两份完整目录。
- 实际layer_first BF16页[2,36,16,8,128]，按两字节字模式比较，再转FP32计算绝对差；全部元素有限，逐层合并K/V统计。
- get止于缺口之前，后续文件仍存在不等于可复用连续前缀。首请求缺页0重算1024token、缺页32重算512token，后两次均device命中1008。
- 六次16token输出等于参考，不证明KV逐位一致。分段执行、形状和数值路径未完全隔离，不能将差异唯一归因于存储损坏或舍入；显存分段控制v2已核对512输入／1输出的前置请求及后续实际device命中512，排除旧528边界尝试；该控制仍未完全隔离所有形状与执行因素。
- 首条件含独立JIT，只有每条件一次重启，不作速度比或p95。矩阵只计实际剩余prefill，文件bytes不是物理磁盘IO，故障策略和长期持久性另计。

固定来源：

- [sources/cache-missing/preparation.json](../../experiments/ch09/09-08/missing-pages/preparation.json)，SHA256 `cb08b3582165d4649feb99b7a45b74b936d6002121c866f89967e092f31275e9`。
- [sources/cache-missing/reference-output.json](../../experiments/ch09/09-08/missing-pages/reference-output.json)，SHA256 `53c08fb2943142bd9d04349af5fc1045ff0b1c901b6cf87acd4f1fef6186525f`。
- [sources/cache-missing/restored-first.bin](../../experiments/ch09/09-08/missing-pages/restored-first.bin)，SHA256 `b4a2f8f4aea5ae1d21acc1d6ab979f13f11567067665f08145c1a73bb1a57e99`。
- [sources/cache-missing/restored-middle.bin](../../experiments/ch09/09-08/missing-pages/restored-middle.bin)，SHA256 `17ab975e061e2e25ddd79669372fa475b60608760004cdd8e75b16bba14c2ae4`。
- [sources/cache-missing/memory_pool_host.py.snapshot](../../experiments/ch09/09-08/missing-pages/memory_pool_host.py.snapshot)，SHA256 `828a67de019d75455a9df801f674ce5446c124090ece3b686f9d63a89f55ce0a`。
- [sources/cache-missing/run.py](../../experiments/ch09/09-08/missing-pages/run.py)，SHA256 `2df17d8f2596a5bbddfdb8b8c2030b523c1ae2397d07454aeffd538754e53fb2`。
- [sources/cache-missing/storage_trace.py](../../experiments/ch09/09-08/missing-pages/storage_trace.py)，SHA256 `775c891770581d15fb2764e7a06eeff6a1983d9b2063176a63c1cc079db22ec7`。
- [sources/cache-missing/config.json](../../experiments/ch09/09-08/missing-pages/config.json)，SHA256 `b841e4a3aaea95ad5af1bacb287fd2ab7ac4f93b9f939424c3d282d7b3a0fc35`。
- [sources/cache-missing/inputs.json](../../experiments/ch09/09-08/missing-pages/inputs.json)，SHA256 `8dff397f30621ff9eb41f4ec2c726d5e65d57a704312ea7d80c4957dd2a9e364`。
- [sources/cache-missing/results/first/raw.json](../../experiments/ch09/09-08/missing-pages/results/first/raw.json)，SHA256 `2c09c4e37457cf7b099ba902a4b64f4a62ab6bb5ff47e307466fed03fd6d891a`。
- [sources/cache-missing/results/first/storage.jsonl](../../experiments/ch09/09-08/missing-pages/results/first/storage.jsonl)，SHA256 `cfad7993b354ec99031b5a7cd95c2864df1915fab91549c7911475ff63818fd3`。
- [sources/cache-missing/results/middle/raw.json](../../experiments/ch09/09-08/missing-pages/results/middle/raw.json)，SHA256 `2f19437d57c4bb659ae213212a73a511b8e28ec948405c94ab68fb8a69ad17a2`。
- [sources/cache-missing/results/middle/storage.jsonl](../../experiments/ch09/09-08/missing-pages/results/middle/storage.jsonl)，SHA256 `a3bb34d99b93c15b4c35bd433b04aa889ac7845d9a0079112e98674aa0ab8899`。
- [sources/cache-missing/manifest.json](../../experiments/ch09/09-08/missing-pages/manifest.json)，SHA256 `5f013cbb6149537eb6a618ff93be79f829d99c4f47fdb6fdf1f3d44596d3ad1a`。
- [sources/cache-missing/run_device_prefix_v2.py](../../experiments/ch09/09-08/missing-pages/run_device_prefix_v2.py)，SHA256 `15f72169c5718c2120ecdc8844577bf05a63a8e663a4f52fbd21960557ded41f`。
- [sources/cache-missing/results/device-prefix-v2/raw.json](../../experiments/ch09/09-08/missing-pages/results/device-prefix-v2/raw.json)，SHA256 `ce2553a825be4c15e8bd0f169be6abf9df2fccd704bee43179f293a6ef0a9b9f`。
- [sources/cache-missing/device-prefix-v2-page32.bin](../../experiments/ch09/09-08/missing-pages/device-prefix-v2-page32.bin)，SHA256 `92c4dacac0f7d14ba5bf7780b0ae76747824c09f679c9c4c176c16db5bed0644`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
