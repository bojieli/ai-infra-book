# TLS1.3 / QUIC v1声明消息图：独立审查

**修订后PASS。** 本次只写独立checker及报告，没有修改作者代码。审查源码SHA256为 `d97b640e062b3e0d11adf5787dcddb43a1835138341302445ccc93cf8392beaf`；实际运行 `python3 calculations/research/protocol-handshake/check-independent.py`，通过52场景/手算对照、287条报文事件检查、21项非法输入拒绝。七份固定RFC原件逐字节重新校验长度及SHA。

依据 `research/connection-sequence-integration/next-protocol-scope.md`，并实际读取RFC9000§8.1/14.1、RFC9001§5.6及RFC8446§2/4.2.10等原文。这里验收的是受这些约束的声明报文依赖与算术，不是TLS密码执行、完整报文codec、真实协议栈或HTTP应用验收。

## 发现并由作者修复的问题

1. 初版缺少应用授权发送0RTT的独立输入，只验证凭据并声明服务器执行策略。RFC9001§5.6将应用请求使用0RTT与凭据分开。修后新增 `application_early_data_authorized`，且PSK、early凭据与授权均严格bool；未授权、整数1冒充True均拒绝。
2. 初版用报文总bytes大于业务payload检查承载，无法保证扣头部后仍装得下业务数据，且早期报文分布没有闭合。修后给出逐包payload分配与请求/响应总量，核一致性及每包声明overhead下限；checker核边界相等可容纳、差1byte拒绝、分配总和错误拒绝。
3. 长早期上传跨客户端1RTT密钥安装需要切换保护级别，不能把全部已排队包一直标为0RTT。当前有限实现明确拒绝该输入，并保留一般逐包密钥切换未实现。checker真实触发拒绝；没有假造分块转换实现。

## 独立时间和依赖核验

对TCP+TLS1.3/QUIC v1各五种模式、立即执行/等待client Finished两种策略，共20组建立外部Fraction flight级max-plus递推。递推从给定报文byte、方向速率与单向传播开始，独立得到应用执行与完整响应时刻，没有拿候选输出时间作期望。再对全部事件核序列化长度、方向资源不重叠及到达=发送结束+该向传播。

TCP先SYN→SYN/ACK→携最终ACK的ClientHello；普通/PSK无early请求在服务器flight到客户端后发送Finished与请求，两个在同向串行器上相邻发送，不额外等待Finished到服务器。QUIC没有TCP三次握手，client Finished的发送需要服务器flight到达。

服务器立即执行早期业务不等于能够提前发1RTT响应：response序列化必须在server flight全部发送结束之后，也必须满足应用完成时间和QUIC反放大预算。响应到客户端后才能算完整结果，不能拿模型完成或发送完替代。

根独立六条固定手算也全部实际执行相等：TCP fresh310.6192ms、resume310.4352ms、early accept210.3472ms、early reject/retry310.4352ms；QUIC fresh210.88992ms、early accept110.59904ms。默认packet修订增加请求/响应各20bytes后，手算已同步，未沿用旧数值。

另构造低上行例：early序列化已在client1RTT安装前结束，但其尾部到服务器时晚于整个server flight到客户端。候选仍在ClientHello到达后立即发送server flight，没有反向等待未来early尾部；该合法边界通过。更长early跨安装时刻则明确拒绝。

## QUIC Initial与放大限制

逐事件重算server发送累计UDP payload，并在每次发送开始只累计此前**已到达服务器**的client UDP payload。分母不含IP20B和UDP8B；discarded early所属datagram仍可作为收到连接bytes，不因业务拒绝而抹去传输收据。计数的是UDP payload含QUIC头/保护载荷，业务payload不等于此计数边界。

检查包含：

- client所有Initial及server首个ack-eliciting Initial的UDP payload均至少1200bytes，1199拒绝。
- 仅收到1200bytes时，server恰发3600可以推进；4800且没有后续指定ACK则本声明图受阻。
- [1200,1200,1228]总3628bytes仍受阻，不能通过把client的28B IP/UDP头算入分母而错误放行。
- 4800bytes场景收到第二个server Handshake报文后，client发送显式Handshake ACK；**ACK在服务器到达**才完成地址验证，既不在client发送时，也不在client收到server包时提前验证。
- 被拒early的400B UDP datagram实际到达后将累计接收由1200升至1600，才可支持4800发送；拒绝不会消除其bytes，未来到达也不能提前提供预算。
- 大1RTT响应虽已由立即执行生成，仍需等待足够额度/地址验证；未绕过限制。

无ACK的受阻例只能称 `budget_blocked_in_declared_graph`。真实QUIC还有一般ACK、Initial/Handshake PTO等机制，本候选明确未实现，不能据此称真实协议死锁。

## 早期业务与字节声明边界

拒绝后有应用重试授权：业务请求发送两份、被接受唯一业务输入一份、执行一次。无重试授权：早期传输仍计bytes，业务执行0次，没有完整响应，保留待应用决策。是否立即执行已接受early是另一独立策略，不构成跨连接重放防护或exactly-once保证。

TCP声明包bytes已经包含IPv4/TCP；QUIC声明bytes是UDP payload，模型额外加28B IPv4/UDP。本实现的TCP62B最低开销对应所选简化IPv4/TCP40B与TLS记录/AEAD等22B假设；它不是全部TCP选项、TLS padding或任意记录划分的通用值。QUIC32B是选择的报文头/frame/tag预算，也不是RFC定义的统一最小开销。checker只证明给定业务分配装得下这些声明预算，不能证明真实Certificate、CID、frame变长编码或AEAD报文正确。

输出使用 `modeled_wire_bytes_by_direction`准确限定为**已建模报文**。一般TCP数据ACK、一般QUIC ACK/PTO、HTTP头及HTTP/3 SETTINGS、票据/token后台签发、拥塞控制和流控未计，不能将该数标成真实网络总字节或直接与完整协议抓包比较。

## 保留缺口

未实现HRR、QUIC Retry、无效ticket回退、真正0RTT跨保护级别续传、密钥/证书验证、HTTP应用状态机、真实CUBIC/BBR及大文件窗口/恢复。复用模式假设存活且可用的空闲连接、足够信用，未继承先前请求的在途队列。当前源码不能被表述为完整C68闭合；它提供明确协议版本依赖的有限新增证据。
