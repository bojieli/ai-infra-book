# 实验 7-10 结果：网络优化的模型级收益

集合通信时间取自实验 7-3 已解析的公开 NCCL AllReduce 记录（80 个可用实测点）。

| 场景 | 记录 | rank | 条件 | 曲线依据 | 通信 | 暴露通信 | 计算/访存 | 合计 |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx2 | 16 | 基线（直接用公开曲线） | measured_point | 68.67 ms | 68.67 ms | 405.08 ms | **473.74 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx2 | 16 | 分层通信（跨机消息减半） | measured_point | 34.37 ms | 34.37 ms | 405.08 ms | **439.44 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx2 | 16 | 与计算重叠（80% 可重叠） | measured_point | 68.67 ms | 13.73 ms | 405.08 ms | **418.81 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx2 | 16 | 慢链路（通信时间 ×3） | measured_point | 206.00 ms | 206.00 ms | 405.08 ms | **611.08 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx2 | 16 | 故障退化（一条链路失效，通信 ×2） | measured_point | 137.34 ms | 137.34 ms | 405.08 ms | **542.41 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx4 | 32 | 基线（直接用公开曲线） | measured_point | 91.08 ms | 91.08 ms | 405.08 ms | **496.16 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx4 | 32 | 分层通信（跨机消息减半） | measured_point | 45.57 ms | 45.57 ms | 405.08 ms | **450.65 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx4 | 32 | 与计算重叠（80% 可重叠） | measured_point | 91.08 ms | 18.22 ms | 405.08 ms | **423.29 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx4 | 32 | 慢链路（通信时间 ×3） | measured_point | 273.24 ms | 273.24 ms | 405.08 ms | **678.32 ms** |
| 训练步（8192-token 前反向，梯度 all-reduce 一次） | hgx4 | 32 | 故障退化（一条链路失效，通信 ×2） | measured_point | 182.16 ms | 182.16 ms | 405.08 ms | **587.24 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx2 | 16 | 基线（直接用公开曲线） | measured_point | 16.79 ms | 16.79 ms | 135.03 ms | **151.81 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx2 | 16 | 分层通信（跨机消息减半） | measured_point | 9.64 ms | 9.64 ms | 135.03 ms | **144.66 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx2 | 16 | 与计算重叠（80% 可重叠） | measured_point | 16.79 ms | 3.36 ms | 135.03 ms | **138.38 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx2 | 16 | 慢链路（通信时间 ×3） | measured_point | 50.36 ms | 50.36 ms | 135.03 ms | **185.39 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx2 | 16 | 故障退化（一条链路失效，通信 ×2） | measured_point | 33.57 ms | 33.57 ms | 135.03 ms | **168.60 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx4 | 32 | 基线（直接用公开曲线） | measured_point | 20.68 ms | 20.68 ms | 135.03 ms | **155.70 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx4 | 32 | 分层通信（跨机消息减半） | measured_point | 13.33 ms | 13.33 ms | 135.03 ms | **148.36 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx4 | 32 | 与计算重叠（80% 可重叠） | measured_point | 20.68 ms | 4.14 ms | 135.03 ms | **139.16 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx4 | 32 | 慢链路（通信时间 ×3） | measured_point | 62.04 ms | 62.04 ms | 135.03 ms | **197.06 ms** |
| 跨服务器推理 prefill 8192（每层 all-reduce） | hgx4 | 32 | 故障退化（一条链路失效，通信 ×2） | measured_point | 41.36 ms | 41.36 ms | 135.03 ms | **176.38 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx2 | 16 | 基线（直接用公开曲线） | measured_point | 2.53 ms | 2.53 ms | 27.60 ms | **30.13 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx2 | 16 | 分层通信（跨机消息减半） | measured_point | 1.68 ms | 1.68 ms | 27.60 ms | **29.29 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx2 | 16 | 与计算重叠（80% 可重叠） | measured_point | 2.53 ms | 0.51 ms | 27.60 ms | **28.11 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx2 | 16 | 慢链路（通信时间 ×3） | measured_point | 7.60 ms | 7.60 ms | 27.60 ms | **35.20 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx2 | 16 | 故障退化（一条链路失效，通信 ×2） | measured_point | 5.06 ms | 5.06 ms | 27.60 ms | **32.67 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx4 | 32 | 基线（直接用公开曲线） | measured_point | 2.62 ms | 2.62 ms | 27.60 ms | **30.22 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx4 | 32 | 分层通信（跨机消息减半） | measured_point | 2.41 ms | 2.41 ms | 27.60 ms | **30.01 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx4 | 32 | 与计算重叠（80% 可重叠） | measured_point | 2.62 ms | 0.52 ms | 27.60 ms | **28.13 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx4 | 32 | 慢链路（通信时间 ×3） | measured_point | 7.86 ms | 7.86 ms | 27.60 ms | **35.46 ms** |
| 跨服务器推理 decode b64 h8192（每层 all-reduce） | hgx4 | 32 | 故障退化（一条链路失效，通信 ×2） | measured_point | 5.24 ms | 5.24 ms | 27.60 ms | **32.84 ms** |
