# C68 下一有限交付：连接握手、ACK窗口与完整图片请求

本文件是范围与来源设计，不是已实现计算或验收结果。仅写本研究目录，不修改公共模块、场景或PLAN。依据 `research/plan-c68-c69-audit.md`、正文及extensions第12.3，优先使用已有封存原件；本轮未实现协议模拟、未重跑网络实验。

## 1. 保留已有成果，只补缺失连接

- `topics/image_request_budget.py`已有30MB原图/5MB成片、20Mb/s上行/100Mb/s下行、0.3s模型和0.1s残余RTT的串行12.8s教学预算。新计算沿用同一完整可用成片终点，但用实际列出的握手、单向传播、ACK与窗口事件**替换**笼统connection/RTT输入，不能再叠加原0.1s。
- 已有上行BDP=20,000,000×0.1/8=250,000bytes；同条件下行BDP=1,250,000bytes。它们是方向独立的无头部带宽时延积，不是待补空白，也不是自动足够的可用窗口。
- `packet_reorder.py`可借鉴区间身份、重复去除和交付事件，但其重传等待为输入，没有ACK/RTO推导；`feedback_queue.py`不能改名为CUBIC/BBR；`connection_states.py`不是HTTP握手模块。
- 已有loopback192正式+2预热及HTTP3多流144正式+18预热数据保留原边界。不得重复执行后才承认它们存在，也不得将其时间拟合成本题WAN常数或协议排名。
- 研究目录 `image-request-streaming`已有声明块依赖；本项先固定**整图可靠交付**，不重新做块模型独立性或preview调度。ASR/TTS、Computer Use、过期媒体以及C69空口模型保持后续项。

## 2. 一个闭合且可复算的有限教学协议

建议命名 `finite-ack-window-image-v1`。以下都是明确教学参数和状态转移，**不是TCP、QUIC、CUBIC、BBR或某HTTP库的实现**。RFC用于解释必须区分的机制，不能为这些自选数值背书。

### 2.1 工作负载、资源与字节

- 请求依次完成30,000,000bytes原始输入上传、服务器0.3s处理、5,000,000bytes成片下载；客户端收到完整唯一有序成片即可用，额外编码/组装默认显式0。质量要求相同，无真实图像/codec执行；preview未知。
- 两个独立全双工方向FIFO串行器：client→server20,000,000bit/s；server→client100,000,000bit/s。每向传播0.05s，无随机排队/丢包，仅第2.5节一次注入。传播不占链路资源，ACK和握手必须使用相应方向串行器，不能瞬时出现。
- 每数据包最多1000payload bytes，声明40bytes协议头；尾包按真实长度，不padding。ACK为40bytes，握手消息长度另外给出。这里的40bytes不是对任意TCP/IP/TLS/QUIC报文头的测量。
- 输入方向30,000包，输出方向5,000包；每端维护独立发送窗口、ACK状态和接收重组集合。每个包保留`request_id,direction,offset,length,attempt`，网络bytes计每次发送，唯一payload不因重传增加。
- 接收端将连续已收前缀立即放入应用文件存储并释放运输层buffer；应用层仍等待完整文件才启动模型或交付成片。运输窗口与完整文件存储容量不得混为同一内存预算。

### 2.2 握手依赖：连接状态和窗口状态分开

固定以下教学消息图，而不是直接声称“TCP首次2RTT/QUIC恢复0RTT”：

- `fresh_two_exchange`：H1 client→server400B；收到后H2 server→client800B；客户端收到后H3 client→server400B；服务器收到后H4 server→client800B；客户端收到H4后请求可发送。服务器发送H4后已具备请求接收状态。无证书/密码运算开销。消息各走链路并计传播，故等待包含2次双向传播及实际序列化，不只是手填0.2s。
- `ticket_one_exchange`：事先持有有效ticket为前置条件，H1/H2一轮后才能发送应用数据。ticket签发、过期验证及丢失ticket情形未模拟。这是声明的一轮握手，不把所有真实resumption都说成一轮或0RTT。
- `reused`：已建立连接无需握手消息。首轮如何建立要在请求序列中明确列出，不能把组内首请求隐去。
- 先做4个串行同图请求：fresh每轮重建、ticket每轮一轮握手、fresh一次后复用三次。下一请求在上一请求**完整成片且该连接双向ACK已排空**后到达；保留完成时刻与ACK排空时刻，避免最后ACK越过场景边界后被遗漏。
- 握手对比默认每请求都重置发送cwnd至IW，使差值只归因连接消息；再单列`reuse_preserve_windows`，复用继承各方向已确认cwnd并重置该请求sequence offset，且无idle衰减假设。这个独立开关避免把连接复用和暖窗口收益混成一项。
- 0RTT不在v1。可预留`unsupported`，不能默认为成功/免费，也不把有效ticket当应用重放安全证明。真实HTTP/TLS/QUIC新建、恢复、复用、0RTT接受/拒绝与fallback对照仍是C68后续项。

### 2.3 窗口与有限ACK推进规则

每方向分别维护`next_offset, highest_contiguous_ack, acked_packet_ids, outstanding_unique_payload, cwnd, receive_window, received_intervals`。

- IW=10,000payload bytes；`cwnd_cap=2,000,000bytes`；`receive_window=2,000,000bytes`，均独立输入。接收窗口扫描50,000／250,000／2,000,000bytes；初始窗口扫描1,000／10,000／250,000bytes。不宣称10包是某TCP版本的规范默认。
- 一个新数据包只有在`outstanding_unique_payload + length <= cwnd`且`offset + length <= highest_contiguous_ack + receive_window`时才可进入发送串行器。credit在开始序列化时占用；不得预先排无限个尚不满足窗口的包。
- 每收到一个数据包，接收端更新去重区间和连续前缀，立即产生ACK；ACK含该包identity及当前连续接收prefix。ACK即时产生不等于即时抵达：ACK要排入反向串行器、完成40B发送并传播0.05s。ACK本身不需要ACK。
- ACK到达发送方后，仅新确认的packet-ID释放其唯一payload在途credit；累计前缀只取max，不因晚ACK后退。每个首次确认包增加cwnd `min(newly_acked_payload,1000)`，直到cap；重复ACK不增长。这是明示ACK驱动有限增长规则，受cwnd/rwnd双约束，**不是RFC5681完整慢启动/拥塞避免，也不是QUIC ACK-range实现**。
- 接收重组缺口存在时，选择性packet credit可以释放，但累计flow-control右边界不会越过缺口。因而要同时核“在途唯一bytes”和“最大可发送offset”，不能用一个min(B,W/RTT)替代逐事件状态。
- 固定ACK每包一次，不加入ACK合并timer、延迟ACK或ACK丢失。后续ACK频次/空口时间是C69的另一交付；这里已经计入反向线路字节，不应再次加相同ACK为额外网络payload。

### 2.4 事件排序与服务器交付

使用Fraction精确时间。事件包括握手消息发送/到达、数据发送/到达/丢弃、ACK发送/到达、timer到期/取消、窗口状态变化、模型开始/结束、成片完整和连接排空。

同刻次序：先处理全部接收及ACK到达并更新窗口/取消timer，再处理仍有效timer，最后启动各空闲方向的发送。ACK已于timer期限同刻到达则不重传。FIFO队列以生成时间和稳定序号排序；重传优先只影响尚未开始的**本方向新数据**，不抢占已在发送的包或挤掉已排队ACK/控制消息。

服务器在输入区间完整连续覆盖[0,30MB)的接收时刻启动0.3s模型，不等待最后上行ACK返回客户端。模型完成后启动5MB返回，窗口为服务器→客户端自己的状态；此时未排空的上行ACK也须与下行数据共享同一server→client发送资源。完整成片不等于服务器收到最后下行ACK，两个终点分别输出。

### 2.5 明确一次丢包与恢复

仅丢弃上传方向offset=12,000、length=1000的首发包（零基第12包）。它仍消耗1040B上行序列化资源，随后在声明的接收前丢弃，不产生该包ACK。后续包可乱序到达并ACK，接收缺口阻止完整输入交付。所有其他数据/ACK/握手均成功。

每个未确认数据包在其发送完成时设置固定教学timeout=1s；ACK取消对应generation timer。**这不是TCP RFC6298自适应RTO，也不是QUIC PTO**。首个有效timeout触发一次重传同一identity/区间，cwnd重置1000B；其他已在途数据不被撤回，若在途超过新cwnd便暂停新发送直至credit允许。重传不再次占新的唯一bytes或flow-control offset，但再次占1040B物理发送量，ACK也再占反向资源；收到重传后最终累计前缀可跨过已缓存后续区间。

v1要求恰一次恢复成功：如选择参数导致第二个有效timeout、未指定包超时或ACK丢失，应显式输出超出有限协议合同/拒绝，而不是隐式无限重试。所有timer事件与取消原因须保留。恢复后仍用第2.3节ACK增长规则，不凭RTO后半窗、fast-recovery、PTO探测等名称假装实现额外算法。

## 3. 输出和验收

输出每方向payload/header/ACK/handshake/retransmit wire bytes，发送资源busy区间与window-blocked区间、瞬时cwnd/rwnd/inflight/累计prefix、接收乱序峰值、握手ready时刻、输入完整/模型开始/模型结束/成片完整/ACK排空时刻，以及4请求合计。

必须有独立小整数oracle：4–12包、1–3包窗口逐事件手算；先核IW1不可能在第一个ACK前发送第二包，再核ACK增长、rwnd小于cwnd、首包/中包/末包丢失及timer/ACK同刻、重复ACK/乱序ACK不重复释放credit、重传后只交付一次、最后成片不等待其ACK。基准30MB/5MB再核上下行守恒和完整质量终点。窗口无限且头/ACK/握手为0时应回到传播明确的12.8s整图基线；头/ACK开启后不能强行保持原12.8s。

固定初交付矩阵可取3握手策略×3初始窗口×3接收窗口×无丢包/一次丢包=54场景，另加暖窗口复用4请求对照及64KB小文件边界。真实代码应限制窗口合法性、有效loss offset和非负精确时间，记录固定参数而非自动调参择优。

图12-4候选只画同结果的握手/发送/ACK等待/恢复/应用交付事件，已有loopback、多流实测另列证据面板，不能拼成同条件TCP/QUIC排名。独立审查通过后再接CLI、固定JSON/Markdown、统一重现和链接核查。

## 4. 必须引用的现有固定RFC原件

以下hash本轮从本地文件重新计算。RFC编号/节号是固定定位；文字只概括约束，不将教学参数说成标准值。

| 原件及官方入口 | 要核的固定段落 | 本地路径 | SHA-256 |
|---|---|---|---|
| [RFC9293](https://www.rfc-editor.org/rfc/rfc9293.txt) | §3.5三次握手；§3.8.1要求RTO算法；§3.8.2拥塞控制与RFC5681/6298依赖；§3.8.6窗口 | `references/files/standards/rfc9293.txt` | `6d9ac8be4b0286f8c3d337addf442b2eb6a9b14e1366594ea7fbc273f93dc2d9` |
| [RFC9000](https://www.rfc-editor.org/rfc/rfc9000.txt) | §4.1–4.2独立stream/connection绝对flow-control limit；§13.2.1–13.2.2 ACK生成/频率；不能把QUIC流控等同TCP滑窗 | `references/files/standards/rfc9000.txt` | `f88aae47f8b18e102024916e975e919201d8dde689cba79b01079eaedd402e22` |
| [RFC9002](https://www.rfc-editor.org/rfc/rfc9002.txt) | §6.1确认驱动loss；§6.2.1 PTO公式；§6.2.4 probe；§7.2初始窗口；§7.3.1 slow start；用于明确本协议未实现这些完整规则 | `references/files/standards/rfc9002.txt` | `3a8a54eea1ad5d1c134a548bf15edfa0e21bfb4106dbd7db3c09cace842099af` |
| [RFC9001](https://www.rfc-editor.org/rfc/rfc9001.txt) | §4.1.1–4.1.2 complete/confirmed；§4.5 resumption可禁用0RTT；§4.6.2接受/拒绝；§9.2 replay | `references/outline-checks/2026-09-07/rfc9001.txt` | `3bbaecdf5afd278052a2c48348ce118c4ff8d0cf6b9915549858171b3f98a591` |
| [RFC9114](https://www.rfc-editor.org/rfc/rfc9114.txt) | §1–2 HTTP/3建立于QUIC；§3连接；§4 HTTP消息仍有语义，连接/多流不取消载荷 | `references/outline-checks/2026-09-07/edge-media/rfc9114.txt` | `6b84555c88eeebcf5d2b2e1d9d7b58630abc97ab877b2cf62dee4cd635db34e4` |
| [RFC9221](https://www.rfc-editor.org/rfc/rfc9221.txt) | §5 DATAGRAM的非可靠性与拥塞控制；仅用于说明完整可靠图片不能自动采用过期媒体政策 | `references/outline-checks/2026-09-07/rfc9221.txt` | `ee8c04c5228fd120030ba7a8f6725c2ca609da107ad2ba8c44fdd44f73edb3b4` |

已读本地关键定位例：RFC9293的§3.5约在1221行、§3.8.1约1920行、§3.8.2约1945行；RFC9000 §4.1约1035行、ACK频率约4161行；RFC9002 PTO约624行、IW约911行、slow start约967行；RFC9001 resumption约740行、0RTT约766行。实施前引用锁定文件及哈希，不能仅引用某网站当前页面。

## 5. 已有源码、缺失原件和下一轮固定要求

已有官方匹配记录在 `experiments/ch12/12-04/loopback/official-sources.json`：

| 固定源码 | 本地路径 | SHA-256 |
|---|---|---|
| aioquic1.3.0 async client | `experiments/ch12/12-04/loopback/sources/aioquic.asyncio.client.py` | `5159d2e28bd33da386c59dbac99dbb35ee47ecf4b480596367299c5ec03dd1c9` |
| aioquic1.3.0 HTTP/3 | `experiments/ch12/12-04/loopback/sources/aioquic.h3.connection.py` | `696e9c3735de11c314b8cd1e7e1265761a9373d1bbd2dbdf66570961dac839cd` |
| h11v0.16.0 connection | `experiments/ch12/12-04/loopback/sources/h11._connection.py` | `93d61155fea4a19a9bb6d056dfac5259a26959d6706bec50554f401c4a3d0ee2` |

这些可用于解释已有实验路径，**不足以证明指定loss/congestion控制器**。本次未找到对应封存aioquic recovery/congestion模块或固定Linux TCP CUBIC/BBR实现；如做实现级算法对照，应补具体tag/commit、算法模块和默认配置，不能由客户端版本猜测实际控制状态。

本轮初查未找到以下RFC本地原件，随后按根追加要求从RFC Editor官方原站下载原始txt，已封存在本目录 `sources/`。`sources.lock.json`记录官方URL、重定向后URL、UTC获取时间、HTTP状态、bytes和SHA-256；这是研究局部锁，**尚未注册公共 `calculations/configs/sources.lock.json`**：

- [RFC5681](https://www.rfc-editor.org/rfc/rfc5681)：§2窗口/flight术语、§3.1 slow start与拥塞避免、§3.2 fast recovery、§4.1 idle restart、§4.2 ACK；若采用实际TCP规则须引用该研究原件并完成公共来源接入。该固定文本的存在不代表它囊括后续全部TCP更新。
- [RFC6298](https://www.rfc-editor.org/rfc/rfc6298)：§2 RTT估计和RTO、§3 Karn规则、§5 timer管理；实际TCP timeout不可用本设计固定1s冒充。
- [RFC8446](https://www.rfc-editor.org/rfc/rfc8446)：§2.1–2.3 handshake/resumption/0RTT、§4.6.1 ticket、§8 replay；若输出真实TCP+TLS1.3消息时序矩阵须引用该研究原件并完成公共来源接入。

下一实施若只交付上述**明示自定义有限协议**，现有固定RFC足以界定概念边界；若标题或输出改为实际TCP/TLS/QUIC实现，则须先公共注册新增RFC并补固定实现，不允许只是换名字。即使有限协议通过公共验收，完整C68的0RTT回退、实际控制器及语音/截图轨迹，和完整C69空口/多路径费用仍不得整体勾选。

### 本轮追加封存核对

| 原件 | bytes | SHA-256 |
|---|---:|---|
| `sources/rfc5681.txt` | 44339 | `a2d99a2421d5c57b248394f26ba44fc364aa546680fbf10ff0aa7034dad8b87d` |
| `sources/rfc6298.txt` | 22454 | `f3a6d937c0a7653bd431fdbbdcd7920f4e9d9cdb6134fa9db7a74b90d215edf6` |
| `sources/rfc8446.txt` | 337736 | `47871bc8820a2c3b6ea89f061055577058862cf543686b82d10131239702b3bd` |

三份均HTTP200，内容包含对应RFC编号；本地重读bytes/SHA与局部锁一致。未下载第三方转述、未修改公共source lock。

## Public integration follow-up

The three RFC originals are now registered under `sources/connection-window` in the public source lock. The implemented one-request contract and differences from this initial proposal are recorded in [scope](../connection-window-integration/scope.md) and [acceptance](../connection-window-integration/acceptance.json). Remaining sequential-request and real-protocol work is not implied complete.
