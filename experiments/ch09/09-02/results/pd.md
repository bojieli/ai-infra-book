# 实验 9-2 结果：A100＋H20 的 PD 分离

每 worker 速率为声明假设：A100 prefill 16,384 tok/s／decode 64 tok/s；H20 prefill 4,096／decode 256。链路 25 GB/s。

| 布局 | 场景 | 每请求交接 | PD 上界 | 共置上界 | PD/共置 | 链路容量 | 瓶颈 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 共置（8 张 A100 都做两件事） | 输入 2K／输出 128／无命中 | 0.281 GiB | 3.500 req/s | 3.765 req/s | 0.93× | 82.784 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 共置（8 张 A100 都做两件事） | 输入 8K／输出 128／无命中 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×6 |
| 共置（8 张 A100 都做两件事） | 输入 8K／输出 1024／无命中 | 1.125 GiB | 0.438 req/s | 0.485 req/s | 0.90× | 20.696 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 共置（8 张 A100 都做两件事） | 输入 8K／输出 128／命中 6K 前缀 | 1.125 GiB | 3.500 req/s | 3.765 req/s | 0.93× | 20.696 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 共置（8 张 A100 都做两件事） | 输入 32K／输出 128／无命中 | 4.500 GiB | 2.000 req/s | 2.000 req/s | 1.00× | 5.174 req/s | prefill、decode | P:A100-80GB-prefill×4 D:A100-80GB-prefill×4 |
| 共置（8 张 A100 都做两件事） | 输入 8K／输出 128／到达率 8 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×6 |
| 同构 PD（A100 4＋4） | 输入 2K／输出 128／无命中 | 0.281 GiB | 3.500 req/s | 3.765 req/s | 0.93× | 82.784 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 同构 PD（A100 4＋4） | 输入 8K／输出 128／无命中 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×6 |
| 同构 PD（A100 4＋4） | 输入 8K／输出 1024／无命中 | 1.125 GiB | 0.438 req/s | 0.485 req/s | 0.90× | 20.696 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 同构 PD（A100 4＋4） | 输入 8K／输出 128／命中 6K 前缀 | 1.125 GiB | 3.500 req/s | 3.765 req/s | 0.93× | 20.696 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×7 |
| 同构 PD（A100 4＋4） | 输入 32K／输出 128／无命中 | 4.500 GiB | 2.000 req/s | 2.000 req/s | 1.00× | 5.174 req/s | prefill、decode | P:A100-80GB-prefill×4 D:A100-80GB-prefill×4 |
| 同构 PD（A100 4＋4） | 输入 8K／输出 128／到达率 8 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×6 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 2K／输出 128／无命中 | 0.281 GiB | 9.000 req/s | 5.882 req/s | 1.53× | 82.784 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×2,H20-96GB-decode×4 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 8K／输出 128／无命中 | 1.125 GiB | 8.000 req/s | 3.200 req/s | 2.50× | 20.696 req/s | prefill、decode | P:A100-80GB-prefill×4 D:H20-96GB-decode×4 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 8K／输出 1024／无命中 | 1.125 GiB | 1.188 req/s | 0.909 req/s | 1.31× | 20.696 req/s | decode | P:A100-80GB-prefill×1 D:A100-80GB-prefill×3,H20-96GB-decode×4 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 8K／输出 128／命中 6K 前缀 | 1.125 GiB | 9.000 req/s | 5.882 req/s | 1.53× | 20.696 req/s | decode | P:A100-80GB-prefill×2 D:A100-80GB-prefill×2,H20-96GB-decode×4 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 32K／输出 128／无命中 | 4.500 GiB | 2.250 req/s | 1.471 req/s | 1.53× | 5.174 req/s | prefill | P:A100-80GB-prefill×4,H20-96GB-decode×2 D:H20-96GB-decode×2 |
| 异构 PD（A100 4 做 prefill，H20 4 做 decode） | 输入 8K／输出 128／到达率 8 | 1.125 GiB | 8.000 req/s | 3.200 req/s | 2.50× | 20.696 req/s | prefill、decode | P:A100-80GB-prefill×4 D:H20-96GB-decode×4 |
| 全 H20（8 张） | 输入 2K／输出 128／无命中 | 0.281 GiB | 8.000 req/s | 8.000 req/s | 1.00× | 82.784 req/s | prefill、decode | P:H20-96GB-decode×4 D:H20-96GB-decode×4 |
| 全 H20（8 张） | 输入 8K／输出 128／无命中 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | prefill | P:H20-96GB-decode×6 D:H20-96GB-decode×2 |
| 全 H20（8 张） | 输入 8K／输出 1024／无命中 | 1.125 GiB | 1.250 req/s | 1.333 req/s | 0.94× | 20.696 req/s | decode | P:H20-96GB-decode×3 D:H20-96GB-decode×5 |
| 全 H20（8 张） | 输入 8K／输出 128／命中 6K 前缀 | 1.125 GiB | 8.000 req/s | 8.000 req/s | 1.00× | 20.696 req/s | prefill、decode | P:H20-96GB-decode×4 D:H20-96GB-decode×4 |
| 全 H20（8 张） | 输入 32K／输出 128／无命中 | 4.500 GiB | 0.875 req/s | 0.941 req/s | 0.93× | 5.174 req/s | prefill | P:H20-96GB-decode×7 D:H20-96GB-decode×1 |
| 全 H20（8 张） | 输入 8K／输出 128／到达率 8 | 1.125 GiB | 3.000 req/s | 3.200 req/s | 0.94× | 20.696 req/s | prefill | P:H20-96GB-decode×6 D:H20-96GB-decode×2 |
