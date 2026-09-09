# C68：TLS 1.3 / QUIC v1 声明数据包握手图候选

研究候选，尚未接入公共 CLI / reproduce / 正文。固定协议依赖来自 `sources.lock.json` 的七份官方 RFC；每次计算校验原件字节数与 SHA256。文件由本仓库既有固定原件复制，未宣称本次联网下载。默认字节数是教学输入，**不是 RFC 给出的典型测量值**。

```bash
python3 calculations/research/protocol-handshake/calculate.py \
  --output calculations/research/protocol-handshake/result.json
# 单场景：--inputs path/to/input.json --output path/to/result.json
```

## 输入和消息语义

`calculate(inputs)`、`example(protocol, mode)`、`scenarios()` 是可导入 API。17 个固定场景覆盖两个协议各五种模式，以及延迟早期执行、拒绝后不重试、QUIC 3600/4800 UDP 字节的预算对照。

- `protocol`: `tcp_tls13` 或 `quic_v1`；`mode`: `fresh`、`resume`（无 early data）、`early_accept`、`early_reject`、`reused`。
- TCP 使用 IPv4，无 IP 选项；`packets` 每个整数是完整 IP 包字节，包括声明的 TCP 选项和承载内容。SYN → SYN/ACK → 承载最终 ACK 的 ClientHello；未使用 TCP Fast Open。TLS 1.3 单向服务器认证、无客户端证书；PSK 恢复须显式 `valid_psk=true`，选择 PSK-(EC)DHE。`server_flight` fresh 包含 ServerHello、EncryptedExtensions、Certificate、CertificateVerify、Finished；resume/early 不含服务器证书。`client_finished` 是 Finished，在 TLS 接受早期数据时同时包含 EndOfEarlyData。字节包列表由场景声明，尚无 record/tag/certificate 字节组成验证。
- QUIC v1 的 `packets` 每个整数是 UDP payload；线上另加 IPv4 20B + UDP 8B。第一 `client_hello` 数据报含 Initial/ClientHello，至少 1200B；第一 `server_flight` 是至少 1200B 的 ack-eliciting Initial，后续数据报是 Handshake。**假设第一包完整承载 ServerHello，使客户端能够处理后续 Handshake 包**。QUIC `client_finished` 是 Handshake/Finished，不发送 EndOfEarlyData；`early_request` 是 0RTT，正常 request/response 是 1RTT。
- 此处的 `request` 与 `response` 是声明的应用负载承载包，**不是已经实现 HTTP/1.1、HTTP/2 或 HTTP/3 编码器的结果**。
- `early_credentials_valid=true` 是外部已验证凭据、early-data 限制及记忆参数的输入条件；尚未细分 TLS max_early_data_size、QUIC transport parameters、HTTP/3 SETTINGS 检查。
- `application_policy=immediate` 允许早期请求完整到达后执行；`wait_client_finished` 等服务器收到客户端 Finished 才执行。响应在服务器 TLS flight 后序列化。`early_reject` 不执行早期请求；只有 `application_retry_authorized=true` 才在普通密钥可用后重新提交一次。没有把库层自动重发或 exactly-once 当成协议保证。
- `reused` 必须 `connection_usable=true`；本图明确从无排队、信用充足的空闲连接开始，不继承 connection-sequence 的窗口或在途 ACK。

## 时间、链路与预算

时间全部用 Fraction。每方向一个 FIFO 串行器，序列化时间是 `8 × wire_bytes / bits_per_second`；传播时间只作用于到达事件，不占串行器。后继消息由实际到达事件触发，不预收 RTT。单 flight 数据报按列表依次不可撤销排队；`ready/start/end/arrival` 全部可见。

QUIC 三倍预算使用**服务器实际收到的 UDP payload**，排队发送字节保守地预留预算；不得因预知稍后将到达的客户端数据而提前花费。客户端 Handshake 包到服务器即验证地址，毋须等待完整 TLS Finished。

`server_flight_ack=true` 在客户端收到第二个 server flight 数据报后立即发送显式 Handshake ACK；该 ACK 到服务器时解除地址验证限制。`false` 有意省略此消息，用来显示受限消息图的预算等待。4800B/无 ACK 场景是 **`budget_blocked_in_declared_graph`**，不是宣称真实 QUIC 必然死锁：真实栈还可有 Initial ACK、Handshake ACK、PTO 探测等解除事件。

3600B 场景恰能消耗 1200B 初始输入所提供的三倍预算；4800B 场景先发送三包，再等待 Handshake ACK 的实际到达。输出保留阻塞位置及已接收/已预留字节。`modeled_wire_bytes_by_direction` 只统计显式列出的消息，不能当成包含所有 ACK/控制消息的完整抓包字节。

## 仍未实现的原范围

- 长 early upload 跨客户端安装 1RTT 密钥时，需要按 STREAM offset 将未发送尾部改为 1RTT，并正确处理拒绝后的授权重发。当前候选检测 early serialization 跨该时刻并明确拒绝，不提供错误的整段 0RTT 结果；30MB early-data 场景仍待实现。
- TLS HRR、QUIC Retry、无效票据回退、NewSessionTicket/NEW_TOKEN 后台字节、真实证书/record/frame 编码与每层 overhead 验证。
- 一般 QUIC ACK、PTO、丢包、TCP 数据 ACK、CUBIC/BBR、flow control 和继承中的窗口。已提供的单次 Handshake ACK 不是完整 ACK 实现。
- HTTP 语义、0RTT 重放防护、媒体截止、跨请求关联及实测性能。

这些缺口继续属于 C68，不能用本候选关闭原工作包。

## 最终候选的输入防错

应用发送早期数据必须额外明确 `application_early_data_authorized=true`；它与服务器执行政策及拒绝后重试授权是三个不同决定。全部授权和凭据标志要求 JSON boolean。

`request_payload_bytes` 与 `response_payload_bytes` 分别声明有效业务输入、完整输出；`payload_bytes_by_packet` 给 request、early_request、response 的逐包有效字节分布，长度必须匹配对应 packet 列表，且总和必须等于业务字节。每包剩余空间至少保守留出 TCP 62B（IPv4/TCP 最小头40B + TLS1.3 record/tag22B）或 QUIC 32B（声明的简短包头/frame/tag下限）。这只是排除物理不可能输入的下限检查，**不能证明任意给定包已完成正确TLS/QUIC编码**，实际CID/options/扩展/frame编码仍须后续拆分验证。默认请求100B、响应200B分别用180B、280B承载包。

本候选无拥塞和流控，不能将声明的大文件按链路额定带宽序列化称为真实协议吞吐或30MB业务性能。现有连续窗口模型也不能直接冒充其TCP/QUIC实现。
