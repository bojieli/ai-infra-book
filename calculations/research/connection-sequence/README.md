# C68：四轮请求的共同事件计算候选

研究实现，尚未自行声明公共交付。`calculate.py` 基于公共 `connection_window.py` 的同一逐段协议规则扩展：唯一 payload 窗口、ACK 携带累计文件前缀、Fraction 时间、serialization-end 固定 RTO、指定首发丢失的一次恢复。不是 TCP、TLS、QUIC 或实际拥塞控制器测量。官方机制边界沿用 `../connection-window-scope/` 固定 RFC，教学窗口和握手字节不来自 RFC 标准参数。

## 运行与输出

`python3 calculations/research/connection-sequence/run_scenarios.py` 写入 `result.json`：30MB/5MB 图片与 64KiB 双向小文件 × 两种提交触发 × 四种策略，共16主场景，另加仅第2请求上传第12包首发丢失，共17场景。大场景保存精确输入、每请求统计与总量；调用 `calculate(**inputs)` 可重建全部逐事件日志。`small-pending-ack-trace.json` 保存完整小整数日志，成片 5/11/17/23s、真实最后 ACK 7/13/19/25s。

## 状态与行为

一个贯穿全序列的优先队列和两个方向 FIFO 串行器。每段/ACK/计时器带 request_id、connection_id、方向和包身份。上传完整到达立即启动声明模型计算，模型完成启动下载；不等上传最后 ACK。每轮文件 prefix、received/acked 集合和独有 payload 信用分开；每连接、每方向共享 cwnd 和 outstanding。保留旧轮 ACK 对共享窗口的更新以及它占据的链路时间。任意未来取消计时器不延后 quiet。

- `fresh`：每轮新连接，默认四条声明消息图，每方向窗口重置。
- `ticket`：每轮新连接，默认图前两条；有效 ticket 为外部前置条件，不含生成、验证、拒绝或回退。
- `reuse_reset`：首次图、后续无图，每次提交重置两个 cwnd，但绝不清除仍在途的 unique outstanding。重置后 outstanding 可以暂时高于新 cwnd，直到旧 ACK 释放前不再准入。旧 ACK 仍按协议增长该窗口。这是明确教学干预，不是实装 idle/loss 规则。
- `reuse_warm`：首次图、后续继承提交时已发生 ACK 更新后的两个方向状态；不提前继承未来 ACK 造成的窗口，也没有隐含 idle decay。

`submit_on='complete_received'` 在完整响应到达加 think time 后提交下一轮，保留未排空 ACK；`'quiet'` 等本轮两个文件的真实 ACK 全部到达后提交。最后输出窗口明确区分提交、完整接收、最后 ACK 三个时刻。后者可能已经包含下一轮 ACK 对同一连接的更新，不伪装成独立请求的最终窗口。

握手逐条实际预约全局 FIFO，下一条只在上一条到达后预约。`handshake=None` 选默认400/800/400/800B交替图；`[]` 显式无握手；最多8条。`ticket` 取声明图前两条。非零 `connection_ready_seconds` 明确拒绝，第一请求提交固定0，不混入外部就绪偏移。所有日志时间都是序列绝对时间。

方向初值可用 `initial_upload_window_bytes`、`initial_download_window_bytes` 独立覆写。以各方向实际最大段检验，不能将上行窗口赋给下行。总序列包数受 `max_total_packets` 约束，硬上限100000；最多100请求。全序列最多一次指定首发丢失，`loss_request_id` 是1-based，包ID仍是0-based。不容许非指定超时或第二次恢复。安全上限按全序列而非每请求计算。

每请求包含 submit/ready/model/完整响应/最后ACK、响应时长、窗口快照、握手与数据/ACK/头/重传字节、方向busy time。响应时长是完成减提交；总墙钟、响应时长之和、握手累计等待分列。busy time是物理wire序列化，握手等待含队列/传播，不能相加当作新增独立阶段。

## 验证与剩余范围

独立手算基准在 `hand-oracles.json`（由另一审查者编写），另有独立检查脚本与报告。四策略 quiet 的最后成片分别63/47/39/33s、最后 ACK64/48/40/34s，握手16/8/4/4B。无损与丢包案例均不省略 ACK；指定第2请求丢包不会复制到其它轮。

本项覆盖有限教学协议下跨请求连接/窗口/物理FIFO复用。真实 TLS/QUIC 握手及0RTT接受/拒绝、真实拥塞控制器、ASR/TTS媒体截止、截图版本、多流共享窗口及图12-4整体仍是原C68未完成范围。
