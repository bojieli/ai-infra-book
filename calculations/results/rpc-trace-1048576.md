# rpc-trace — 

输入：`{"payload_bytes": 1048576}`

RPC阶段来自封存实测；两端阶段不可重复相加，SSH转发条件必须保留。

| 结果 | 值 |
| --- | ---: |
| verified_record_pairs | 264 |
| selected_measured_calls | 80 |
| excluded_warmup_calls | 24 |
| json_client_cpu_median_ns | 9,774,500.0 |
| binary_client_cpu_median_ns | 1,084,500.0 |
| json_request_application_bytes | `[1398135]` |
| binary_request_application_bytes | `[1048593]` |
| json_to_binary_paired_median_saved_ns | 10,093,646.5 |
| json_to_binary_positive_pairs | 11 |

| 实测模式 | 总时间中位 ns | CPU中位 ns | 总时间p95 ns |
| --- | ---: | ---: | ---: |
| json_copy_worker | 362598708.5 | 9774500.0 | 507227917 |
| binary_copy_worker | 302047145.5 | 1084500.0 | 525441416 |
| binary_view_worker | 324332520.5 | 1091000.0 | 485969459 |
| binary_view_inline | 456563041.5 | 1118500.0 | 497151375 |

| 阶段中位数 ns | JSON worker | binary copy | binary view | inline |
| --- | ---: | ---: | ---: | ---: |
| encode_ns | 8844083.0 | 1667.0 | 1749.5 | 2062.5 |
| prepare_ns | 80104.0 | 99500.0 | 9374.5 | 9833.5 |
| send_ns | 579854.5 | 697542.0 | 830708.5 | 841250.0 |
| response_wait_ns | 354044937.5 | 301067978.5 | 323353833.5 | 455606667.0 |
| verify_ns | 129167.0 | 131333.0 | 126542.0 | 119124.5 |
| total_ns | 362598708.5 | 302047145.5 | 324332520.5 | 456563041.5 |
| client_cpu_ns | 9774500.0 | 1084500.0 | 1091000.0 | 1118500.0 |
| server_receive_ns | 128628743.0 | 54843378.5 | 74381647.0 | 210687383.0 |
| server_decode_ns | 8131201.0 | 542375.0 | 2408.5 | 2316.0 |
| server_queue_ns | 49569.0 | 51900.0 | 46047.5 | 433.5 |
| server_hash_ns | 451013.0 | 445734.0 | 444702.0 | 446154.5 |
| server_observe_ns | 20425.0 | 18450.5 | 19651.0 | 143.5 |

| 配对修改 | 差的中位 ns | 两中位数之差 ns | 变快轮数/20 |
| --- | ---: | ---: | ---: |
| json_copy_worker → binary_copy_worker | 10093646.5 | 60551563.0 | 11 |
| binary_copy_worker → binary_view_worker | 20730437.5 | -22285375.0 | 12 |
| binary_view_worker → binary_view_inline | -12634500.0 | -132230521.0 | 7 |

计量条件：

- 真实实验7-4：Apple M2 Max客户端到RTX主机Linux CPU服务端，经持久TCP和SSH转发，单次一个在途；GPU未使用。不是模型推理、RDMA、数据中心直连或裸链路测量。
- 三种载荷、四种模式、每条件2次预热20次正式测量，共264次。校验封存哈希、两端记录、载荷身份与同轮各模式配对；当前选定一种载荷80次正式调用。
- 客户端相邻五阶段逐次相加等于完整RPC；CPU时间另列，不与墙钟相加。服务端时钟独立，只算本地差值；服务端阶段与客户端发送／等待重叠，不能再加到客户端总时间。
- 各阶段中位数不保证相加等于总中位数。配对差为同轮before-after，正数表示变快；差的中位数不等于两个中位数之差，保留全部20个差值与正差次数。p95取20条排序第19条。
- 应用请求字节不含TCP/IP/SSH framing。binary copy→view同时改变拼接／发送API与服务端物化；worker→inline改变交接路径。局部CPU下降不自动证明完整调用稳定变快，有限配对结果不是显著性或总体性能保证。

固定来源：

- [sources/rpc-traces/client.py](../../experiments/ch07/07-04/client.py)，SHA256 `36bbb9bbc4465c6fae4f6a6212034374930d25f524098826eb6ae999afc39b92`。
- [sources/rpc-traces/results/client/environment.json](../../experiments/ch07/07-04/results/client/environment.json)，SHA256 `e6c3a57e77a73a06ccc4ede84e5b163a236d06d34e5dcf764412036fb4341d12`。
- [sources/rpc-traces/results/client/requests.jsonl](../../experiments/ch07/07-04/results/client/requests.jsonl)，SHA256 `074f27a32aa9d579c29c344413d63c2821e2e88e8b45f2fae1324ad8aacc3d20`。
- [sources/rpc-traces/results/server/environment.json](../../experiments/ch07/07-04/results/server/environment.json)，SHA256 `537ad37d1fc872556c3030f8c533725c29776d9f33f9de2a647f2a8eb9dd264c`。
- [sources/rpc-traces/results/server/requests.jsonl](../../experiments/ch07/07-04/results/server/requests.jsonl)，SHA256 `4df63b7cc545f473efe003a2b98c849ba946979a65635eb830e1b32ebcdda5ce`。
- [sources/rpc-traces/server.log](../../experiments/ch07/07-04/server.log)，SHA256 `ed1a545bb85e55816bbf9566b028b2a0bc456b88f49f6f266c0401048824194b`。
- [sources/rpc-traces/server.py](../../experiments/ch07/07-04/server.py)，SHA256 `b5de2d1a48a0fe6f7d0782f8d45c2080e5f591ddca4eeed7c7352c84a37855c6`。
