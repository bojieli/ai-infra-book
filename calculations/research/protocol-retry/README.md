# C68 QUIC HRR、Retry 与 PSK 决策：逐包研究候选

本候选扩展已有逐包发送器，不修改已冻结的公共模块。`handshake_event=none`保留原early-stream计算的发送时刻、应用字节和业务终点；新增身份字段及输入默认值单独变化。不是实际QUIC栈，不执行加密、模型或网络。

```bash
python3 calculations/research/protocol-retry/calculate.py \
  --output calculations/research/protocol-retry/result.json
# 单例增加 --inputs path/to/input.json
```

API为 `calculate(inputs)`、`example()`、`scenarios()`，目前20个固定场景。默认30MB请求、5MB响应、模型0.3s、上行20Mbps/下行100Mbps、单向50ms；数字是声明值，不是规范性能数据。源文件和锁继续来自 `../protocol-handshake`，七份官方原件每次检查长度与SHA256。

## 不同握手事件

`handshake_event`支持`none`、`hrr`、`retry`、`psk_unknown_fallback`、`psk_unknown_abort`、`selected_binder_invalid`，组合输入明确拒绝。

- **HRR**：服务器发送Initial中的HRR。客户端收到后停止未开始的early包，排队CH2，等待最终server flight安装普通密钥。CH2身份标明移除early_data；它是新的TLS握手消息。已经开始的包不抢占、不擦除线上字节，但所有early输入都无效。普通重发只有在应用授权时发生。
- **Retry**：客户端收到并验证Retry后更新DCID、Initial密钥epoch，保留SCID、原CH1内容身份及所有PN序列。`client_hello_retry`带token，服务器收到第一个有效token包时验证地址，完整CRYPTO到达后才发送最终server flight。第一次0RTT明确采用服务器丢弃政策；`retry_early_policy=reattempt`可以重新尝试相同STREAM范围并继续尾部，**不把Retry本身当TLS拒绝**。`wait_1rtt`选择等普通密钥，再按应用重发授权决定提交。后续TLS仍可接受或拒绝early。
- **未知PSK回退**：服务器忽略不可用PSK，直接选择包含Certificate/CertificateVerify的声明server flight；不自动增加一轮。`psk_unknown_fallback`场景给三包最终flight；读者也可声明其他完整证书消息预算。无完整TLS编码器，消息语义与长度由输入合同声明。
- **未知PSK不可回退／选中binder无效**：服务器失败并发送Initial保护的CONNECTION_CLOSE声明包。服务器检测错误与客户端收到close是两个时刻；其间客户端已发的early仍耗线上字节。客户端到close后停止未发尾部，执行0次，无完整响应。Close-only不是ack-eliciting Initial，故未强制1200B；仍要求声明的头/帧/tag空间足够。

`send_early=false`用于普通基线，ClientHello之后等待普通密钥才发业务，不要求early授权，也不要求“重发授权”才能第一次发送请求。客户端拥有凭据由`client_credentials_available`表达；`valid_psk`仅保留旧输入兼容，作为未显式提供client_credentials_available时的默认值。**服务器是否认识/选择PSK由handshake_event表达**，未知PSK场景可使用`valid_psk=false,client_credentials_available=true`，不需要把服务器未知票据伪称有效。

实际尝试early需`application_early_data_authorized`及客户端凭据条件。Retry后再次尝试early另有`retry_early_replay_authorized`；最终TLS拒绝或选择等待普通密钥后的业务重发需`application_retry_authorized`。所有开关严格要求boolean。局部有效区间去重不构成跨连接exactly-once保证。

## 字节、身份与发送时刻

应用包保留STREAM offset/end、有效payload、应用PN和密钥层级。0RTT/1RTT共用应用PN空间，Retry及重发不重置；相同offset重发使用新PN。`attempt_epoch`区分Retry前后尝试，`application_key_epoch`说明Retry不会改变0RTT保护密钥。Initial和Handshake控制包也分别分配单调PN；Retry没有PN。客户端包记录DCID和SCID，服务器响应DCID是client_scid。

每方向FIFO串行链路，控制包先于尚未入队应用包；实际开始发送时选密钥。到达事件先于同刻发送调度。已发包不可抢占，因此HRR/Retry/close在序列化中途到达时，不会抹掉原包字节。包传播不占链路，全部时间用Fraction。

放大预算只用服务器实际收到的UDP payload，包含能唯一归属本连接的被丢弃包；Retry自身也消耗发送预算。收到携有效token的第一个Initial或Handshake包才验证地址，不在客户端收到Retry时提前验证。无效token通过真实failure消息告知客户端；无效Retry完整性被客户端丢弃，因未实现PTO，后续可报告受限消息图无完成，不能称真实协议永久死锁。

包长度声明为UDP payload；线上加IPv4+UDP28B。ClientHello的有效CRYPTO长度由`client_hello_crypto_bytes`给出，原Initial必须装得下；每个Retry Initial都要重复token，并至少给48B头/帧/tag预算，每包及总承载容量都检查。默认padding有余量，新增32B token可以仍装进1200B；800B token+800B CRYPTO场景需要三个1200B Initial，对比首包地址验证与末包CRYPTO完成时刻。这里的48B/32B等是有限布局预算，不能替代实际CID/varint/AEAD编码器。

## 已预先手算的验收

线上1228B、双向9824bps、单向传播1s，普通请求/响应一包，server最终flight两包，禁可选Handshake ACK：普通QUIC完整请求8s/响应10s；HRR或Retry完整请求12s/响应14s。

Retry early四包请求，每包1168B：Retry前已发三包，Retry后再次early发送四包，实际early8176B、有效输入4672B、丢弃旧3504B、完整响应12s。PSK fatal服务器2s检测、close4s到客户端，期间三包early继续发送，最后包5s到服务器仍丢弃。

## 尚未实现及有限输入边界

不支持TCP HRR、组合HRR+Retry、Retry前0RTT缓冲政策、重复Retry运行轨迹或空token运行时丢弃；当前只接受单个非空token的Retry声明，非法组合／长度明确拒绝。未实现HTTP/3 SETTINGS、完整TLS/QUIC字节编码、实际证书链验证、一般ACK/PTO/拥塞/流控、真实恢复状态、后台票据与媒体截止。Retry仅记录恢复状态重置事件，没有假装存在未实现计时器。

原始应用包最多100000；包含三个完整请求尝试、完整响应及该分支全部控制包的保守总预算最多200000。大文件结果是声明链路和消息图的计算，不是实际QUIC吞吐或生产可靠性结论。该候选尚未公共接入，C68整体保持未完成。
