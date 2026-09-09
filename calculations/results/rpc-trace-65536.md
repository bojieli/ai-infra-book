# rpc-trace — 

输入：`{"payload_bytes": 65536}`

RPC阶段来自封存实测；两端阶段不可重复相加，SSH转发条件必须保留。

| 结果 | 值 |
| --- | ---: |
| verified_record_pairs | 264 |
| selected_measured_calls | 80 |
| excluded_warmup_calls | 24 |
| json_client_cpu_median_ns | 1,608,000.0 |
| binary_client_cpu_median_ns | 424,000.0 |
| json_request_application_bytes | `[87415]` |
| binary_request_application_bytes | `[65553]` |
| json_to_binary_paired_median_saved_ns | 1,667,812.5 |
| json_to_binary_positive_pairs | 12 |

| 实测模式 | 总时间中位 ns | CPU中位 ns | 总时间p95 ns |
| --- | ---: | ---: | ---: |
| json_copy_worker | 219628083.5 | 1608000.0 | 230228166 |
| binary_copy_worker | 219601125.5 | 424000.0 | 228366833 |
| binary_view_worker | 218985896.0 | 420000.0 | 225940500 |
| binary_view_inline | 221170229.0 | 403500.0 | 245971042 |

| 阶段中位数 ns | JSON worker | binary copy | binary view | inline |
| --- | ---: | ---: | ---: | ---: |
| encode_ns | 1214083.0 | 1583.0 | 1604.5 | 1687.5 |
| prepare_ns | 16770.5 | 22375.0 | 8521.0 | 8854.5 |
| send_ns | 132895.5 | 97333.5 | 111000.0 | 119791.5 |
| response_wait_ns | 218085604.5 | 219322291.5 | 218722563.0 | 220997249.5 |
| verify_ns | 112583.0 | 128416.5 | 128812.0 | 119041.5 |
| total_ns | 219628083.5 | 219601125.5 | 218985896.0 | 221170229.0 |
| client_cpu_ns | 1608000.0 | 424000.0 | 420000.0 | 403500.0 |
| server_receive_ns | 846579.0 | 326413.5 | 351920.5 | 243225.5 |
| server_decode_ns | 482645.5 | 9394.0 | 899.0 | 1318.0 |
| server_queue_ns | 53250.0 | 49721.5 | 47590.0 | 398.0 |
| server_hash_ns | 43813.0 | 42937.5 | 42802.5 | 43602.5 |
| server_observe_ns | 12823.5 | 13147.5 | 14264.0 | 133.0 |

| 配对修改 | 差的中位 ns | 两中位数之差 ns | 变快轮数/20 |
| --- | ---: | ---: | ---: |
| json_copy_worker → binary_copy_worker | 1667812.5 | 26958.0 | 12 |
| binary_copy_worker → binary_view_worker | 1399146.0 | 615229.5 | 12 |
| binary_view_worker → binary_view_inline | -1439770.5 | -2184333.0 | 9 |

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
