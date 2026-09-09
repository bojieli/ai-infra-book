# QUIC HRR、Retry与PSK分支：独立审查

最终冻结版本 **PASS（限README列明的QUIC单分支合同）**。源码SHA256为 `c83da49a679ee638de1f609a3485c84b18287387fa3e8d86049930fb7b80cd7c`，与作者确认一致。实际运行 `python3 calculations/research/protocol-retry/check-independent.py`，通过60场景、9项非法输入拒绝、7份RFC长度/SHA核验；包含实际30MB/5MB多分支以及旧基线逐字段对照，执行中源码未改变。只写独立checker、结果和本报告，未改旧研究或公共模块。

依据 `research/protocol-integration/next-retry-scope.md`，实际读取固定RFC8446§4.1.4/4.2.11、RFC9000§8.1/17.2.5及RFC9001§4.6.2/4.7等。验收声明事件、条件、报文预算和时序，不证明密码计算或真实网络协议栈。

## 初审发现并由作者修复

1. 初始失败消息被归入Handshake包号空间，但在binder错误等分支客户端尚未获得Handshake密钥。修后使用Initial保护的CONNECTION_CLOSE声明。CLOSE-only不属于ack-eliciting包，不能从RFC9000§14.1推导必须1200B；当前1200B是手算profile，输入遵守声明布局下限。
2. 多个携token Initial时，原实现等全部CRYPTO到达才验证地址。修后首个有效token Initial实际到服务器即验证，完整ClientHello仍等全部分片。这两个里程碑分别检查。
3. 服务器response的DCID原先错误沿用server CID。修后指向client SCID；Retry后的客户端DCID才应使用Retry SCID。
4. 原先没有关闭early发送的普通请求模式，无法执行无early的HRR/Retry预先手算。修后 `send_early=false` 等普通密钥发送首次请求，不因 `application_retry_authorized=false`被阻挡；首次普通发送不等于重发。
5. 客户端收到failure后最初只停止应用包，尚未启动的控制队列仍继续发送。修后停止该端所有尚未开始发送的包，保留当前包非抢占和在途到达。独立构造十个Retry Initial、首token无效场景验证close到达后没有新client发送。
6. 多Retry及多failure列表原先可被当成一个flight末尾才处理。当前有限合同明确只允许一个完整Retry及一个完整failure数据报，非法多包声明直接拒绝。它没有实现运行时重复Retry/空token的收包与丢弃，此点仍是缺口。

## 三种事件不能合并

HRR：client收到HRR后不再启动0RTT包；新CH2身份明确移除early_data，等待最终server flight安装1RTT密钥，期间不偷偷发送普通业务。已开始early包仍付完整wire和传播，但没有业务贡献。HRR不产生地址token，不能自动清除三倍限制。

Retry：client收到有效Retry后记录新Initial密钥epoch、更新后续client DCID、保留client SCID和原CH1身份。Initial与Handshake及application包号分别保持单调，不重置；Retry自身无PN。0RTT application保护epoch仍保持不变，重发用新PN、原STREAM offset。服务器明确丢弃旧尝试0RTT，新尝试仍可以被TLS接受；Retry没有被自动改成early rejection。

PSK：客户端持有凭据与服务器识别/选择分开；兼容字段valid_psk作为client_credentials_available的默认值，服务器决策由handshake_event明示。未知且允许回退直接使用声明证书flight，不平白增加一轮；选中binder错误或不允许回退会发送真实failure并终止，没有伪造普通结果。这里的有效性均是声明输入，不是运行binder或Retry完整性密码验证。

## 根预先手算实际复算

每UDP1200B、外层28B、双向9824bit/s、单向传播1秒，故每个包序列化1秒，禁可选Handshake ACK：

- 无early普通QUIC：完整请求8秒、完整响应10秒。
- 无early HRR：HRR到client4秒，CH2到server6秒，client keys9秒；完整请求12秒、完整响应14秒。
- 无early Retry：client收到Retry4秒，带token Initial到server6秒才验证地址；完整请求12秒、完整响应14秒。
- 同报文预算的未知PSK普通回退与普通基线同为8/10秒，不凭PSK失败增加RTT。上述四种分支均额外测试关闭应用重发授权，仍成功首次普通请求。

Retry且接受early的四包请求：旧early发送1–2、2–3、3–4；Retry在4秒同刻先处理，Initial2为4–5，token在6秒验证。新early发送5–6、6–7、7–8、8–9，client keys9秒。总early有效传输8176B，接受唯一业务4672B；请求10秒完整、响应12秒完整；application PN严格为0..6，重发前三个offset保持0/1168/2336。

Fatal时序：server在2秒收到CH检测错误，close2–3发送、4秒client知情。client此前仍发送1–2、2–3、3–4三包；最后旧early在5秒到server并丢弃。客户端失败时刻4与最后已建模到达5分开，不能让客户端在server本地检测的2秒提前知情。

Token分包：原CH900B在一个Initial可容纳，增加400B token后两个Initial承载。首包6秒验证地址，完整CH7秒，成片15秒；没有将验证拖到7秒。容量检查同时覆盖原CH、每个带token Initial及总CRYPTO承载，不能用总和掩盖某包装不下token。

## 字节多重性、30MB和旧基线

checker按有效输入区间排序要求首尾相接，重叠或缺口直接失败，不用set union掩盖重复。逐方向核PN严格递增、wire=UDP+28、序列化与单向传播、发送不重叠及只由已到达UDP payload提供三倍信用。每条成功轨迹接受业务区间恰覆盖一次请求，响应也恰覆盖一次完整输出。

20个候选固定场景实际运行，含30MB/5MB的HRR、Retry、PSK回退/失败与授权组合。例如：

| 30MB路径 | request有效wire载荷累计bytes | 接受唯一业务bytes | 执行 |
|---|---:|---:|---:|
| HRR后授权普通重发 | 30231000 | 30000000 | 1 |
| Retry后early再尝试并接受 | 30231000 | 30000000 | 1 |
| 未知PSK允许普通回退 | 30232100 | 30000000 | 1 |
| Retry再尝试后TLS又拒绝，授权重发 | 30463100 | 30000000 | 1 |
| selected binder无效 | 231000 | 0 | 0 |

表中只累加业务payload发送量，头部/控制bytes在wire账另计，不能称完整网络传输量。拒绝且不授权普通重发不会继续未发送业务尾部；Retry选择wait_1rtt且不授权重发也保持0次执行。

另执行旧protocol-early-stream的全部13场景：`handshake_event=none`时status、milestones、summary、反放大记录逐字段相同，所有旧transmission字段逐包相同，新增CID/epoch等元数据不改变数学结果。30MB没有由小文件线性放大代替实际事件执行。

## 仍保留的缺口

本轮没有实现TCP上的HRR/PSK回退、组合HRR+Retry、运行时重复Retry/空token/已处理server Initial后的Retry丢弃、Retry前0RTT缓冲政策、一般ACK/PTO/拥塞/流控、HTTP或实际TLS/QUIC编码器。空token、多Retry、多close目前是非法输入拒绝，不能把它写成运行时规范分支已经执行。

无效Retry完整性实际被丢弃，但由于没有PTO，结果为 `waiting_unmodeled_recovery`；只有实际待发server包确被额度限制才报声明图budget blocked，均不能推断真实QUIC死锁。已记录恢复状态重置事件不等于实现了未建模的拥塞和丢失状态机。局部一次有效执行也不构成跨连接exactly-once或重放安全保证。
