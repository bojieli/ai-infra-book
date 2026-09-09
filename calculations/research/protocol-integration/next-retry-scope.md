# C68 下一步：HRR、QUIC Retry 与 PSK 回退的有限消息计算

2026-09-09。本文是下一阶段的待实现合同及预先手算，不是已实现结果，不修改两个公共模块，也不据此勾选 C68。

## 官方依据和三种事件的区别

固定原件来自公共 `protocol-rfc` 源组，路径相对于本文：

- [RFC8446](../../sources/protocol-rfc/rfc8446.txt) §4.1.2、§4.1.4、§4.2.10、§4.2.11、附录E.5：HRR后的第二ClientHello移除early_data，并按要求修改key_share/cookie；不能继续发送早期数据。第二次HRR应中止握手。服务器可忽略未知PSK并在可能时选择非PSK握手；选中PSK后binder不合法则必须终止，不能把所有“票据错误”都改成普通回退。拒绝早期数据后的应用重发须明确授权。
- [RFC9001](../../sources/protocol-rfc/rfc9001.txt) §4.6.2、§4.7、§5.2、§5.6：TLS HRR一定拒绝QUIC早期数据；QUIC Retry不表示早期数据被拒绝，客户端可以再次尝试0RTT。HRR仍是承载在Initial中的TLS消息。拒绝后重置stream及绑定应用状态，不能只改一条输出标签。切换到1RTT后未发送尾部不再用0RTT。
- [RFC9000](../../sources/protocol-rfc/rfc9000.txt) §8.1、§8.1.2、§17.2.5：Retry用于地址验证，返回的token必须放进后续Initial；服务器收到并验证token时才验证地址。客户端检查Retry完整性、非空token和CID条件，一次连接尝试最多处理一个Retry。Retry改变后续DCID及Initial保护密钥，保留客户端SCID和相同TLS ClientHello；token会挤占Initial承载空间，可能增加分包。**所有包号空间均不得因Retry重置**。Retry没有PN，不能当成显式ACK。服务器可丢弃或缓冲Retry前的0RTT，这项政策必须声明。
- [RFC9002](../../sources/protocol-rfc/rfc9002.txt) §6.3：Retry重置拥塞／丢失恢复状态和待运行计时器，但保留握手消息；它不是“某个数据包被ACK”。本阶段不新增完整拥塞实现，因而只记录重置事件和未模拟状态，不能借此声称已经实现恢复规范。

上面是规范条件；下方包长、排队政策、密码处理时长和业务大小都是声明参数。

## 与已实现模块的衔接

`protocol_handshake.py` 已有TCP+TLS1.3及QUIC五种单请求基础分支，默认flight声明、双向FIFO和有限地址预算；`protocol_early_stream.py` 已有30MB逐包offset/PN、发送开始时密钥选择、拒绝后的授权重发和非抢占边界。

下一实现应扩展后者的**事件驱动发送器**作为QUIC重试分支的计算基础；不能先调用旧模块取得完整结果，再把固定RTT加到所有时刻。旧冻结场景在不开HRR/Retry/回退时须逐字段保持数学结果一致。TCP的HRR和PSK回退保留TCP三次握手，不能把TLS HRR误算成重建TCP。

建议有限输入分别是 `tls_hrr`、`quic_retry`、`psk_selection`，不使用一个含混的`retry=true`。首先分别实现独立分支；若本轮不支持组合HRR+Retry，显式拒绝该组合并保留缺口，不能默默忽略其中一种。PSK选择应至少区分`accepted`、`unknown_fallback_allowed`、`unknown_no_fallback`、`selected_binder_invalid`。

## HRR分支必须发生的事件

ClientHello1到服务器 → HRR发送及到客户端 → 停止尚未开始的早期包 → ClientHello2（无early_data，新key_share/cookie按声明输入） → 最终server TLS flight → client Finished → 授权的普通请求／重发。

HRR到达时已经开始序列化的0RTT/TLS早期包不可凭空撤销；它的实际线上字节及到达仍计入账本，但服务器不得把它作为可执行请求。下一包不能继续early。把HRR识别时刻与以后1RTT密钥安装时刻分别记录，期间不得发送普通应用数据。若没有应用重试授权则完成握手也不生成请求执行或响应。QUIC不发送TLS EndOfEarlyData。

重试时同一有效输入仅算一次，重发的STREAM范围和物理字节单列；HRR不等于QUIC地址token，不能自动清除放大限制。HRR到来后必须保留已发包、双向串行器和传播中的消息。

## QUIC Retry分支必须发生的事件

Initial1到服务器 → 声明的Retry datagram → 客户端验证Retry → Initial2携token和原TLS ClientHello → 服务器实际收到并验证token → 后续server TLS flight。

需记录原DCID、Retry SCID、后续DCID、客户端SCID是否保持、token长度和验证结果、Initial密钥epoch、每个PN空间下一个包号。第二Initial若因token增长而分成多包，逐包序列化、逐包收取UDP/IP字节，不复制原来的整段耗时。Retry自身的UDP字节也计入未验证前服务器预算。校验失败的Retry被丢弃，不应进入新握手分支；重复Retry与已经处理server Initial之后的Retry也应按规范忽略，不能无限重试。

优先实现一种明确可核对政策：**服务器丢弃Retry前0RTT，客户端获授权后再次尝试这些STREAM范围，随后发送未发尾部**。它不是TLS early rejection，不能将`early_result`强制改成reject；服务器后续仍可接受或拒绝这次早期尝试。应用发送early授权、Retry后的early再尝试政策、TLS拒绝后的普通重发授权分别列明。未重新尝试early时可以等待普通密钥再发送，但是否重发已尝试的业务仍由应用合同决定。

服务器若选择缓冲Retry前0RTT则另建场景：重复STREAM范围只能贡献一次有效输入，缓冲范围和保留边界必须显式；不得从该局部去重推出跨服务器／跨连接exactly once。为避免误导，第一版可以明确不支持该政策并拒绝输入。

收到有效token的Initial之前，服务器仍受实际收到UDP payload的三倍预算；token验证失败不得解除预算。有效Retry只要求客户端更新连接状态，不意味着服务器已收到token，不能在客户端收到Retry时提前验证地址。一般ACK、PTO及拥塞仍按原缺口保留。

## 无效PSK的普通回退

已有`valid_psk=false`目前会拒绝输入；新实现需显式分流。未知PSK且允许普通握手时，选择包含Certificate/CertificateVerify的最终server flight，早期请求不被处理，普通应用重发依赖授权。PSK拒绝本身不要求增加一个额外往返：若现有ClientHello足以进行普通握手，服务器直接发送普通flight，新增时间来自真实消息长度和依赖。如果缺所需key_share而必须HRR，应独立标出HRR分支。

选中PSK后binder不合法必须失败，不能产生普通握手或有效响应。未知PSK且不可回退也报告未完成及失败事件，不输出伪造耗时。错误类型、发送字节、已执行次数和业务终态分列。

## 预先手算：小整数消息图

以下是待实现oracle，使用每个数据报/包的**线上长度1228B**、双向9824bps，所以每包序列化1秒；每向传播1秒，应用处理0。QUIC各UDP payload=1200B。普通请求/响应各一包；server最终flight两包。为隔离依赖，关闭可选Handshake ACK，client Finished足以完成地址验证；未列一般ACK。TCP的SYN/ACK不能为了凑整数而填成1228B；TCP分支应另用合法IP/TCP头与TLS承载长度逐包计算。包长只是边界输入，之后仍须给出TLS/QUIC结构预算。

| 分支 | 关键轨迹 | 完整请求到服务器 | 完整响应到客户端 |
| --- | --- | ---: | ---: |
| QUIC普通基线 | Initial0–1，到2；server2–4，到5；Finished5–6，请求6–7，到8 | 8s | 10s |
| QUIC HRR，无early | HRR2–3，到4；CH2/Initial4–5，到6；server6–8，到9；Finished9–10，请求10–11，到12 | 12s | 14s |
| QUIC Retry，无early | Retry2–3，到4；带token Initial4–5，到6并验证地址；其后同上一行 | 12s | 14s |

HRR与Retry在这个特定oracle都增加4秒，但它们改变的状态、有效early数据及密钥不同；不能因这张表而实现同一个“加4秒”函数。未知PSK普通回退若最终flight与普通基线一样，且没有额外HRR，完整结果应与相应普通基线相同。TCP验收另使用合法SYN/SYN-ACK头长度，明确保留原三次握手并在ClientHello1与最终server flight之间插入HRR、ClientHello2两个实际消息；不能重发SYN来凑出额外往返。

### Retry与0RTT仍可接受的逐包oracle

仍采用每包1秒、每向传播1秒；请求4包，每包1168B有效数据，0RTT额外32B；响应一包。客户端Initial0–1；旧early包1–2、2–3、3–4。Retry在4秒到达，与发送结束同刻先处理；Initial2占4–5，服务器6秒收到有效token。服务器flight6–8，在9秒完整到客户端。客户端重新尝试4个early范围5–6、6–7、7–8、8–9，9秒安装普通密钥并发Finished9–10。服务器丢弃前三个旧early包，接受新的四个，10秒有完整请求，响应10–11、12秒完整到客户端。

应得到：early payload实际发送7×1168=8176B，有效输入4×1168=4672B，执行1次；不存在因Retry自动拒绝0RTT。所有应用PN严格递增，旧范围再次发送使用新PN。若服务器最终TLS拒绝early，以上早期范围均不贡献有效输入，后续结果必须依赖普通重发授权，不能复用12秒结果。

## 验收与交付

独立检查至少覆盖：上表小整数；30MB在HRR/Retry到达时恰逢包边界及包中途；Initial token增加导致分包；有效／无效／空token及重复Retry；PN不重置；Initial密钥更新但TLS ClientHello内容保留；HRR后不再early；未知PSK普通回退及选中binder错误终止；Retry接受和后续TLS拒绝两条路径；有／无应用重试授权；实际UDP预算、已发包守恒、唯一STREAM输入及完整输出。

完成后交付公共CLI分支、固定输入及JSON/Markdown、独立oracle、统一reproduce与正文12.3.1补充。此有限阶段仍不完成一般拥塞/恢复、媒体截止、多流及C68整体；它应消除现有两个模块已经明确列出的HRR/Retry/票据回退缺口，而不把任务扩大成实现所有网络栈。
