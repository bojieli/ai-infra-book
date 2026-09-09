# cache-restart — 

输入：`{"experiment": "9-8 clean restart"}`

文件载荷与调用来自封存正常重启实验，读入量与复用量分开。

| 结果 | 值 |
| --- | ---: |
| verified_payload_files | 65 |
| kv_page_tokens | 16 |
| kv_page_bytes | 2,359,296 |
| stored_payload_bytes | 153,354,240 |
| consumer_get_calls | 64 |
| consumer_read_file_bytes | 150,994,944 |
| consumer_read_page_tokens | 1,024 |
| consumer_reusable_tokens | 1,008 |
| consumer_reusable_bytes | 148,635,648 |
| read_but_not_reused_token_equivalent_bytes | 2,359,296 |
| requests | 6 |
| outputs_match | `true` |

| 进程 | 请求 | 缓存token | 来源 | 客户端秒 | prefill节省FLOPs |
| --- | ---: | ---: | --- | ---: | ---: |
| producer | 0 | 0 | None | 15.308563911123201 | 0 |
| producer | 1 | 1008 | {'device': 1008, 'host': 0, 'storage': 0, 'storage_backend': 'HiCacheFile'} | 0.2820548699237406 | 14302613864448 |
| producer | 2 | 1008 | {'device': 1008, 'host': 0, 'storage': 0, 'storage_backend': 'HiCacheFile'} | 0.18520815786905587 | 14302613864448 |
| consumer | 0 | 1008 | {'device': 0, 'host': 0, 'storage': 1008, 'storage_backend': 'HiCacheFile'} | 1.222087767906487 | 14302613864448 |
| consumer | 1 | 1008 | {'device': 1008, 'host': 0, 'storage': 0, 'storage_backend': 'HiCacheFile'} | 0.19542441214434803 | 14302613864448 |
| consumer | 2 | 1008 | {'device': 1008, 'host': 0, 'storage': 0, 'storage_backend': 'HiCacheFile'} | 0.18587432405911386 | 14302613864448 |

| 进程 | 方法 | 调用数 | 所指文件bytes | 调用覆盖墙钟秒 |
| --- | --- | ---: | ---: | ---: |
| producer | get | 0 | 0 | 0 |
| producer | set | 65 | 153354240 | 0.09845256013795733 |
| consumer | get | 64 | 150994944 | 0.029036132851615548 |
| consumer | set | 1 | 2359296 | 6.101885810494423e-05 |

计量条件：

- 封存9-8 producer-v6/consumer-v6原件和65份实际KV文件全部SHA核验，模型BF16/16token页/配置相同，六次16token输出一致；未重跑服务或清页缓存。
- 每页bytes按官方Qwen36层GQA计算。读取64页对应1024token，但引擎可复用1008；多读16token等价量单列，不称全部读取都避免重算。
- 文件bytes和成功get/set调用不等于物理磁盘IO；set遇到已有文件可能直接成功。消费者一次set不计成新增持久化文件；两进程文件库存与哈希相同。
- 首个producer请求含JIT，单次正常重启不作速度比或恢复p95。fromfile/tofile路径不证明fsync、断电持久性、损坏检测或崩溃一致性。
- 矩阵仅计prompt首token前的完整／命中逻辑prefill，不含之后15次decode、真实访存或编译。强制相同16输出不等于任务质量或KV逐位与重算一致。

固定来源：

- [sources/cache-restart/run.py](../../experiments/ch09/09-08/run.py)，SHA256 `2df17d8f2596a5bbddfdb8b8c2030b523c1ae2397d07454aeffd538754e53fb2`。
- [sources/cache-restart/storage_trace.py](../../experiments/ch09/09-08/storage_trace.py)，SHA256 `775c891770581d15fb2764e7a06eeff6a1983d9b2063176a63c1cc079db22ec7`。
- [sources/cache-restart/config.json](../../experiments/ch09/09-08/config.json)，SHA256 `b841e4a3aaea95ad5af1bacb287fd2ab7ac4f93b9f939424c3d282d7b3a0fc35`。
- [sources/cache-restart/inputs.json](../../experiments/ch09/09-08/inputs.json)，SHA256 `8dff397f30621ff9eb41f4ec2c726d5e65d57a704312ea7d80c4957dd2a9e364`。
- [sources/cache-restart/results/producer-v6/raw.json](../../experiments/ch09/09-08/results/producer-v6/raw.json)，SHA256 `e7ac6581bd8512bd2dcd4684281a524fbdfaffefb5f63ed528df4c16ce5536dc`。
- [sources/cache-restart/results/producer-v6/storage.jsonl](../../experiments/ch09/09-08/results/producer-v6/storage.jsonl)，SHA256 `0587dc4a9952af95bcb716cde2bc9fa8826cf4129565f81ed767e1dfade25591`。
- [sources/cache-restart/results/consumer-v6/raw.json](../../experiments/ch09/09-08/results/consumer-v6/raw.json)，SHA256 `38ae3df73c43da0ebe45eb3e67b4ed4420397171afc9c2ea454b7160c2e44f3e`。
- [sources/cache-restart/results/consumer-v6/storage.jsonl](../../experiments/ch09/09-08/results/consumer-v6/storage.jsonl)，SHA256 `38164b44864e6deade4614fc30cc03973457612e0357c8c5308dee4dd720c8e0`。
- [sources/cache-restart/manifest.json](../../experiments/ch09/09-08/manifest.json)，SHA256 `3ab30c316e16d9e5d3fe0f8b06e6080973d1efd9e75f0dd7c9b224befea1c1f5`。
- [configs/models/qwen3-8b/config.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/config.json)，SHA256 `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30`。
- [sources/qwen3-8b/model.safetensors.index.json](https://huggingface.co/Qwen/Qwen3-8B/resolve/b968826d9c46dd6066d109eabc6255188de91218/model.safetensors.index.json)，SHA256 `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc`。
- [sources/qwen3/modeling_qwen3.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3/modeling_qwen3.py)，SHA256 `704c914530530a1acb0b443add1f520404e3ac2c28c0ab7e16f80f86cfe8ccb2`。
- [sources/qwen3/modeling_qwen3_moe.py](https://raw.githubusercontent.com/huggingface/transformers/0720e206c6ba28887e4d60ef60a6a089f6c1cc76/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py)，SHA256 `3af43d01f9f902c8009b6dd7d7b8b563561b53dd0aa54175f585ae90d049fdb8`。
