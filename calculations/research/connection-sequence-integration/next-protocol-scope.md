# C68 下一步：真实协议版本的握手、恢复与应用交付

2026-09-09；仅为现有来源与原要求的审查和待实现设计。没有执行真实 TLS/QUIC，也没有将现有自定义 ACK 协议改名为标准实现。

## 原要求及现有证据

原正文 12.3.1 要求 HTTP/1.1、HTTP/2 over TCP+TLS 与 HTTP/3 over QUIC 的新建、恢复、复用和多轮累计；12.3.2 还要求短请求/大图窗口与恢复、固定 CUBIC/BBR 版本；12.3.3、实验/图12-4还包括多流、媒体截止与实际业务交付。现有 connection_sequence 可比较声明的四/两消息图、连接复用、分别继承方向窗口和在途 ACK，但消息不是 TLS 握手、固定每包 RTO 不是 QUIC PTO、选择性 packet ID ACK 不是 TCP ACK。必须新增具有真实协议依赖的模型，不能只修改标签。连续请求公共接入与本文件无关；本文件不据其进度勾选 C68。

## 已读取的官方固定原件

路径相对于本文件；末尾给出本次读取字节和 SHA256。RFC9001 已在仓库，不能称缺失。

- [RFC9293](../../../references/files/standards/rfc9293.txt) §3.5：TCP 三次握手、带数据段与 ESTABLISHED 的关系。
- [RFC8446](../../sources/connection-window/rfc8446.txt) §2、§2.3、§4.1.4、§4.2.10、§8、附录 E.5：TLS1.3 消息、PSK/早期数据、HRR、重放边界。
- [RFC9000](../../../references/files/standards/rfc9000.txt) §7、§7.4.1、§8.1、§14.1：QUIC v1、记忆的传输参数、地址验证和三倍放大限制、Initial 数据报最小 UDP payload。
- [RFC9001](../../../references/outline-checks/2026-09-07/rfc9001.txt) §4.6–4.7、§8.3、§9.2：QUIC 与 TLS1.3、0RTT 接受/拒绝、Retry 与 HRR 区别、不使用 TLS EndOfEarlyData。
- [RFC9002](../../../references/files/standards/rfc9002.txt) §6.2、§7：丢失检测、PTO 和拥塞控制；PTO 到期本身不宣告丢包。
- [RFC5681](../../sources/connection-window/rfc5681.txt) §3–4：TCP 慢启动、拥塞避免、快速恢复及空闲后的窗口；不是 CUBIC/BBR。
- [RFC9114](../../../references/outline-checks/2026-09-07/edge-media/rfc9114.txt) §7.2.4.2：HTTP/3 初始/记忆 SETTINGS 与0RTT兼容性；本次不扩展 HTTP 层完整状态机。

HTTP/2 的 SETTINGS/前言、HTTP/1.1 请求编码以及 HTTP 早期数据应用重试规则仍需固定对应官方原件和具体章节后实施。本次没有把 HTTP 425 等未审查规则写成完成事实。CUBIC 与 BBR 也需要各自的规范/明确代码版本及参数；上述 RFC 不能证明任一版本实现。

## 第一阶段必须实现的协议消息图

先固定 TCP RFC9293 + TLS1.3 RFC8446（禁止 TLS1.2 混入）、QUIC v1 RFC9000 + TLS1.3 RFC9001；TLS 恢复选择 PSK-(EC)DHE、无客户端证书，证书链与密码套件明确声明。禁用 TCP Fast Open、TLS HRR、QUIC Retry 的基准单列，再分别加入 HRR/Retry 分支。

| 路径 | 必须体现的消息依赖 | 业务可用时刻 |
|---|---|---|
| 新 TCP + TLS1.3 | SYN → SYN/ACK → ACK；客户端可把 ClientHello 与最终 ACK 一起发送或声明另发；服务器收到 ClientHello 后回 ServerHello、EncryptedExtensions、Certificate、CertificateVerify、Finished；客户端验证后发送 Finished 与请求 | 分开记录客户端可发请求、服务器收到完整请求、服务器允许处理、客户端收到完整响应 |
| 新 TCP + TLS1.3 恢复，无 early data | 仍需新 TCP；PSK 不能去掉 TCP 握手；TLS服务器证书消息可省但请求仍等待服务器 Finished | 不得将恢复凭据等价为存活连接，也不得默认减少一个 TLS 往返 |
| 新 TCP + TLS1.3 接受 early data | TCP 就绪后 ClientHello + 早期请求；服务器 EncryptedExtensions 表示接受；客户端按 TLS 规则发送 EndOfEarlyData 和 Finished | 服务器“可解密早期请求”与应用“准许执行”分开；回应必须经过对应服务器 TLS flight |
| QUIC v1 首次 | 客户端 Initial/CRYPTO ClientHello → 服务器 Initial/Handshake flights → 客户端 Handshake Finished/1RTT请求；没有 TCP 三次握手 | 密钥可用、握手完成、握手确认分开，不等待无关 ACK 才提交应用 |
| QUIC v1 恢复 + 接受0RTT | ClientHello Initial 和携带请求的0RTT；服务器通过 EncryptedExtensions 接受，使用1RTT确认0RTT数据 | 不加入 TLS EndOfEarlyData；0RTT/1RTT共享应用包号空间但密钥层级不同 |
| 现存连接复用 | 不再发送建立连接消息；保留实际方向窗口、流控、ACK与链路队列 | 复用凭证、连接存活、允许开新流分别是显式输入 |

HTTP/3 依据 RFC9114 §7.2.4.2 使用默认或记忆 SETTINGS 发送合法消息，不应无条件增加等待对方 SETTINGS 的屏障；接受0RTT时必须验证记忆设置兼容性。

所有 flights 都应分解成实际可排队的 packet/record 字节，不能先收取整个 RTT 再叠加相同消息的传播。ACK、CRYPTO、STREAM、TLS Finished 和 HTTP 请求可以共包时必须选择一种明确策略，不能两次计算共享头。服务器 TLS flight 可以包含早期可发的应用响应，不得强制所有路径等待客户端 Finished；如应用政策确实等待确认，另列 policy。

## 0RTT 接受、拒绝和重试不能合并

1. 凭据：区分有效 PSK/ticket、允许早期数据、地址验证 token、记忆的 QUIC transport parameters、HTTP/3 settings；一个有效 ticket 不自动提供全部条件。TLS 的 max_early_data_size 与 QUIC 的 0xffffffff 标志/传输流控不是同一 payload 上限。
2. 接受：服务器 EncryptedExtensions 的 early_data 标记；输出发送早期字节、接受字节、应用实际执行次数以及首次/完整结果。单独声明应用立即处理还是等待握手确认。
3. 拒绝：服务器无 early_data，不能处理该早期请求；QUIC必须重置相关流及绑定应用状态，按新参数重新建立1RTT发送状态。旧0RTT已发送字节仍占链路；重新发送产生额外物理字节但有效业务输入只算一次。
4. TLS HRR：early data 被拒绝，第二 ClientHello 不带 early_data；消息依赖增加一轮交互。QUIC Retry 是地址验证，不等同于 TLS HRR 或自动拒绝0RTT；两者必须单独测试。Retry后可尝试0RTT，仍受明确状态与参数限制。
5. 应用重试：RFC8446 附录 E.5 不允许 TLS 层自行自动重发被拒早期数据；应用必须授权。关闭重试时结果应是“本次早期请求未执行/待应用决策”，不能伪造完整响应。图像推理看似只读仍可触发计费/排队；Computer Use 外部动作不能默认可重放。若声明幂等键/去重，需声明共享去重范围、保留期和失败行为，不能直接推出 exactly once。
6. 票据无效但允许普通握手的回退、有效PSK却拒绝early data、接受early data后网络重传，是三种不同事件；分别统计重复 wire、有效执行和额外等待。

## 必须显式提供的数量与约束

记录完整 TCP/IP/UDP 版本、MSS/MTU、TCP选项、TLS records与tag/padding、证书链/扩展字节、QUIC CID/packet-number 长度、frame变长整数、AEAD tag、Initial padding、HTTP头及控制流字节。标准不提供一个适合本书所有部署的“握手固定400/800B”。可以使用注明生成配置的抓包，或声明长度并验证边界；不得称声明长度为官方测量。

用 UDP payload 作为 QUIC 放大预算计数边界：未验证地址收到1200B、仅有该笔输入时最多发送3600B；若服务器需要发送4800B，则剩余至少1200B必须等待更多接收/验证。这个预算不是额外固定一个RTT；后续客户端包和验证消息何时到达决定解除时刻。线上总字节另加UDP/IP头。客户端含Initial的数据报至少1200B，不能用一字节握手oracle冒充有效QUIC包。

首次连接费用、后发NewSessionTicket/NEW_TOKEN费用分别记账：即使关键响应之前不需要票据，它仍是物理字节，不能免费生成后续恢复凭据。密码计算/证书验证可声明独立服务时间或实测并固定环境；不能从FLOPs硬推真实TLS执行时间。

## 可先手算的验收 oracle（待实现，不是性能结论）

先用消息图的零序列化极限验证依赖，单向传播 d=50ms、处理=0、无丢失、无Retry/HRR、完整请求/响应极小且窗口足够、允许最终ACK与ClientHello同发；这些是理想下界，不能替代合法包字节场景。

| 路径 | 服务器得到可执行请求 | 客户端得到响应 |
|---|---:|---:|
| 新 TCP + TLS1.3 普通/恢复但无early data | 5d=250ms | 6d=300ms |
| 新 TCP + TLS1.3 接受early data并允许立即处理 | 3d=150ms | 4d=200ms |
| 新 QUIC v1 普通1RTT | 3d=150ms | 4d=200ms |
| QUIC接受0RTT并允许立即处理 | d=50ms | 2d=100ms |
| 已建立可用连接 | d=50ms | 2d=100ms |

QUIC拒绝0RTT、应用授权1RTT重试且无HRR/Retry：请求执行只能在3d，响应4d；早期请求大小B则payload发送2B、有效输入B、执行一次。禁止应用重试则执行0次、无完整结果。TLS/TCP对应允许重试后5d/6d。HRR增加两个单向传播间隔，完整场景还要增加实际消息字节与排队；不允许据此把所有错误回退统一为加1RTT。

合法包字节验收另需：至少1200B Initial、3600B放大上限边界、初始/恢复flight分包、双方向链路忙时守恒、旧ACK不消失、重复早期请求不增加有效业务输入、票据背景字节归属。提供一个服务器flight恰为3600B及一个4800B受阻的对照，必须能解释阻塞解除事件。

恢复验收不能沿用每包固定RTO：RFC9002给定smoothed_rtt=100ms、rttvar=20ms、granularity=1ms，则Initial/Handshake PTO=180ms；握手确认后Application Data且max_ack_delay=25ms时为205ms。检查到期发送probe与宣告loss不同、不同packet-number space、确认前禁止应用PTO、ACK到期相同时的顺序；后续指数回退按所选规范实现。TCP另按固定RTO/拥塞规范，不能共享一个timer公式冒充全部协议。

## 完成交付条件

公共CLI、冻结协议/业务输入、可读事件和逐消息字节、所有分支JSON/Markdown、独立oracle和非法输入验收、统一reproduce和正文12.3.1接入。上述握手完成也不能关闭C68的真实CUBIC/BBR、大文件窗口、媒体截止、多流与图12-4整体。

## 本次原件指纹

- `references/files/standards/rfc9293.txt`：263696B，SHA256 `6d9ac8be4b0286f8c3d337addf442b2eb6a9b14e1366594ea7fbc273f93dc2d9`。

- `calculations/sources/connection-window/rfc8446.txt`：337736B，SHA256 `47871bc8820a2c3b6ea89f061055577058862cf543686b82d10131239702b3bd`。

- `references/files/standards/rfc9000.txt`：403442B，SHA256 `f88aae47f8b18e102024916e975e919201d8dde689cba79b01079eaedd402e22`。

- `references/outline-checks/2026-09-07/rfc9001.txt`：126175B，SHA256 `3bbaecdf5afd278052a2c48348ce118c4ff8d0cf6b9915549858171b3f98a591`。

- `references/files/standards/rfc9002.txt`：89071B，SHA256 `3a8a54eea1ad5d1c134a548bf15edfa0e21bfb4106dbd7db3c09cace842099af`。

- `calculations/sources/connection-window/rfc5681.txt`：44339B，SHA256 `a2d99a2421d5c57b248394f26ba44fc364aa546680fbf10ff0aa7034dad8b87d`。

- `references/outline-checks/2026-09-07/edge-media/rfc9114.txt`：155206B，SHA256 `6b84555c88eeebcf5d2b2e1d9d7b58630abc97ab877b2cf62dee4cd635db34e4`。
