# C68 四轮连接与窗口：独立事件审查

2026-09-09。审查脚本仅修改 `check-independent.py` 与本审查文件，不修改候选作者的 `calculate.py`。结果见 `independent-review.json`，其中保存受审候选 SHA-256。执行：

```sh
python3 calculations/research/connection-sequence/check-independent.py
```

已实际通过 **118 个完整 trace replay、6 个非法输入拒绝用例**。测试检查候选产生的事件是否符合独立维护的资源、身份和信用账，并通过预先手算及现有公共单请求内核交叉核对；不以候选汇总重新加总作为唯一正确性依据。

## 独立证据

- 四种策略的 ACK 排空手算分别得到四轮成片 `[15,31,47,63]`、`[11,23,35,47]`、`[15,23,31,39]`、`[15,21,27,33]` 秒，与预先保存的 `hand-oracles.json` 一致。
- 非零 ACK 的成片触发手算得到提交 `[0,5,11,17]`、下一轮上传实际起传 `[0,6,12,18]`、成片 `[5,11,17,23]`、最后 ACK `[7,13,19,25]` 秒。ACK 排空触发得到成片 `[5,12,19,26]`、最后 ACK `[7,14,21,28]`。这证明前轮 ACK 仍占共同上行串行器，未被 wrapper 平移抹去。
- 4 策略 × 2 提交模式 × 2 接收窗口 × 2 增长参数 × 无损/第2请求上行一次丢失，以及每策略/模式的第2请求下行一次丢失，全部逐身份重放。
- 另检查上行 6B/下行 2B 不等初窗、零/非零传播、0/2 秒 think time。ACK 排空手算中三个 2 秒思考间隔仅增加总成片 6 秒，不隐含 idle 窗口衰减。
- `reuse_reset` 专项：第2–4请求提交时，下行前轮各有 1B 尚未确认。提交将 cwnd 重置到 1B，但保留这 1B 债务；旧请求 ACK 在提交后到达，正确释放原身份并使同一连接 cwnd 增长到 2B。后轮未免费获得被抹掉的信用。
- 两个单请求用例（无损/一次上行丢失）中，剔除新增 request/connection 身份和提交记录后，数据发送、到达、ACK、窗口、计时器、应用事件六类日志与当前公共 `connection_window.calculate` 逐字段完全一致。
- ACK 恰在 RTO 时刻到达先取消计时器；缩短 RTO 导致未选择包有效超时则拒绝。另拒绝 bool/浮点请求数、负 think time、总序列 packet cap 超限和超范围 loss request。

## 重放的守恒与因果

每个方向从上一条实际预约末尾重算 FIFO start/end，并以输入 bit/s 计算序列化，检查真实物理 wire bytes、busy time 与最后可用时刻。跨轮共享同一串行器，握手、数据、ACK 均在此账中。

独立状态使用 `(request_id, transfer)` 保存 packet、acked 集合、前缀及请求 outstanding，使用 `(connection_id, transfer)` 保存共同 cwnd/outstanding。新段必须同时满足连接剩余发送信用与该文件已收到 ACK 的前缀加 rwnd。重传不再增加唯一信用；ACK 身份只能释放对应请求的已发送段。逐窗口事件检查连接总债务、请求债务、窗口增长、前缀单调、blocked 原因和下一段编号。

每条到达与 ACK 均核对其原始发送身份及 `serialization_end + propagation`，重新构造连续接收前缀。每条 timer 以原发送结束加 RTO 重算，检查同身份此前是否已 ACK。每请求提交时刻等于指定前轮成片/最后 ACK 端点加 think time；请求响应时间从本轮提交起算。所有唯一路径最终 sent = acked = received，outstanding 归零；尾段按实际字节、不补齐。

## 范围与限制

这是自定义有限教学协议的事件审查，不证明 TCP/QUIC 的实际性能、TLS ticket 有效性、0-RTT 接受/拒绝或真实拥塞控制器行为。窗口重置后旧 ACK 仍增长窗口是本模型明示的教学语义。主对照中 ACK 可靠且不主动注入重复/丢失 ACK；独立 replay 有检查重复身份的分支，但本次没有把受控 duplicate injection 算入覆盖数量。

118 个完整重放是小整数/有理数场景的核验，不宣称已检查完整 30MB 冻结产物、公共 CLI/正文接入或全书完成。这些交付必须由后续公共验收另行证明。
