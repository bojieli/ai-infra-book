# 长早期上传逐包保护级别：独立审查

最终冻结版本 **PASS**，源码SHA256 `693f3045ca269e1b914b74b7ad0c202e30cbc85fbbde2cc7debb666e1e5678af`，与作者确认一致。执行 `python3 calculations/research/protocol-early-stream/check-independent.py`，得到54场景检查、15项非法输入拒绝；包含实际30MB输入/5MB输出、根预先手算和密钥中途到达。七份复用RFC原件独立复核长度和SHA；checker核验源码在整轮执行中未改变。只写独立checker、结果与本报告，旧protocol-handshake冻结文件没有修改。

## 独立检查方法

直接从每个发送记录重算payload区间、序列化、单向传播、发送时刻密钥及反放大预算，未调用候选内部发送或状态更新函数。完整覆盖使用相邻区间cursor检查，拒绝重叠/缺口；重发检查使用区间多重性而非set union，避免把重复业务贡献掩盖掉。包号按方向核连续递增，0RTT/1RTT均归application空间；STREAM offset与payload长度另核，不混同包号。

每个request包若发送start严格早于client1RTT密钥安装则为0RTT，否则必须为1RTT。开始发送后不会因中途密钥事件改写保护级别或抢占；发送结束时刻与密钥安装同刻，也先处理密钥/接收事件，再选择下一包。已发送数据不在握手前整段预约未来链路。

一般Handshake ACK及client Finished作为同向FIFO控制消息争用，先于尚未入队业务尾部是本候选声明的排程选择。独立检查1RTT request不得在Finished尚未发送完时开始；服务器response必须等其server flight发送完及应用就绪。已收到server flight与客户端向服务器证明地址可达是两个事件，验证取client Handshake包实际到达服务器时刻。

## 根预先手算和中途密钥

等长报文案例：UDP payload1200B，外层28B，双向9824bit/s、各单向1秒，故每包序列化1秒。6个request包各1168有效bytes，响应100bytes加声明1100bytes开销/填充。根的预先手算与候选实际执行全部相等：

- Initial发送0–1、到达2；server flight发送2–3和3–4，到达4和5；client1RTT密钥安装5。
- 4个early包发送1–2、2–3、3–4、4–5。5秒没有再起一个early包；Handshake ACK发送5–6，Finished6–7；地址验证7，服务器收到Finished8。
- 接受：early4672B、1RTT尾2336B，唯一输入7008B；执行10秒，完整响应12秒。
- 拒绝且授权：early4672B仍计传输，1RTT发送7008B；其前4672B恰对应重发，尾2336B只发送一次；执行14秒，完整响应16秒。
- 拒绝且未授权：停止未发送尾部，1RTT request为0、有效输入0、执行0、没有完整响应，保留待应用重试决定。

另实际复算根的中途事件：server方向速率39296/3bit/s，其余不变，密钥4.5秒到达。4–5秒正在发送的第四个early包完整结束，保持0RTT；接受响应11.75秒，授权拒绝响应15.75秒。再用不同反向传播设置独立构造三种结果的中途密钥变体，均观察到恰一个跨密钥时刻的非抢占early包。checker同时核30个不同尾包长度/上行速率场景。

## 实际30MB / 5MB

按默认1100B有效payload分包，分别真实运行接受、拒绝重试和拒绝未授权；没有用小文件结果乘倍数代替。

| 结果 | 已发early有效bytes | 已发1RTT request bytes | 接受唯一输入bytes | 完整响应秒 |
|---|---:|---:|---:|---:|
| 接受 | 232100 | 29767900 | 30000000 | 13.65867488 |
| 拒绝，授权重试 | 232100 | 30000000 | 30000000 | 13.75792928 |
| 拒绝，未授权 | 232100 | 0 | 0 | 无 |

接受时early前缀与1RTT尾部恰好覆盖一次完整请求。拒绝重试时，重复wire区间精确等于已启动early区间，拒绝包不计入接收业务贡献；新1RTT包使用新的递增application包号，但重发部分保持原STREAM offset。接受业务记录恰覆盖一次30000000bytes，并非仅凭候选内部set去重成立。响应区间也恰覆盖5000000bytes。

## 反放大、字节与输入合同

两个方向分别核wire=UDP payload+28B，应用UDP payload=有效payload+该保护级别声明开销；方向串行器无重叠。逐server发送事件只使用此前实际到达的client UDP payload作为3倍分母，不使用未来数据或外层IP/UDP头。拒绝early的datagram仍属于收到连接bytes，因此可能提供反放大信用；它提供信用不代表业务接受。

缺Handshake ACK且只有短请求的4800B server flight场景受阻；有ACK后实际到达验证解除限制。状态仅称声明图预算受阻，不称真实QUIC死锁；一般ACK、PTO及其他主动恢复未实现。

非法输入实际拒绝包括各授权/凭据bool冒用整数1、无early发送授权、无有效PSK、零packet payload、过小声明开销、IPv4 UDP payload超限、超过100000原始业务包、零速率、Initial小于1200，以及控制包和最多一次重发合计超过200000包。两个规模限制防止通过巨大控制列表绕开原始业务包上限。

## 准确范围

本次没有发现需要作者修复的协议事件或算术问题。它闭合旧候选明确拒绝的“早期长上传跨密钥安装”有限路径，但仍是声明依赖与布局模型。32B最低开销及默认64/48B不是所有QUIC版本/编码的通用常数；包号与offset记录不是实际AEAD或STREAM codec运行。

接受/拒绝决定、应用发送授权、立即执行或等Finished、拒绝后重试授权均是不同声明输入。本轨迹执行一次不提供跨连接防重放或exactly-once保证。没有HTTP业务状态机、一般ACK/PTO、丢失、拥塞/流控、HRR/Retry或票据后台成本，`modeled_wire_bytes`不能称完整真实网络流量。旧protocol-handshake的限制没有被倒改，完整C68仍保留这些后续项。
