# C68：有限ACK窗口教学协议候选

本目录实现一个完整30MB原图上传→声明模型工作→5MB完整成片回传的确定性事件模型。依据第12.3的连接、窗口和恢复问题及 `research/connection-window-scope/README.md` 的来源整理。指定的 `research/plan-c68-c69-audit.md` 在实施时未出现在工作区；本候选使用已存在正文及scope，不因缺少该文件推断额外要求。只写research候选；根独立手算见 `handcheck.md`。

**它不是TCP、QUIC、CUBIC、BBR、TLS或HTTP实现。** 特别地，按首次packet-ID ACK固定增长窗口、每包固定RTO、最多一次有效重传、丢失后不重置cwnd均是本题明示规则。RFC5681/6298/9000/9002用于说明必须区别的机制，不能为这些自定参数提供标准背书。官方原件由 `connection-window-scope/sources.lock.json` 及该目录README固定；本候选不执行RFC协议。

## 输入与规模

`calculate.py:calculate`的所有速率/时长接受非负整数或有理数字符串，速率和RTO必须严格正；拒绝浮点、bool、未知值。bytes、packet-ID、窗口为整数。默认输入30,000,000、输出5,000,000bytes，数据分段25,000bytes，共1200+200个身份；尾段按剩余真实长度，没有padding。每次数据发送另加声明40bytes头，每次ACK为40bytes。25kB是受控教学分段，不声称网络MTU或TCP MSS。packet计数默认上限10000，可显式调整，绝对上限100000；不做自动分段精度改变。

默认初始窗口50,000payload bytes，最大窗口1,000,000bytes，接收窗口1,000,000bytes，首次ACK增量为min(该包payload,25,000)，上限cap。两向采用相同窗口参数但各自独立状态，不共享cwnd或ACK前缀。上行20Mbit/s，下行100Mbit/s，前向/反向传播各0.05秒，模型0.3秒。编解码/最终拼接若有成本须包含于所给模型时长；默认不另计。

可以指定上传或下载某packet-ID的第一次发送丢失，至多选择一方向一包。默认RTO为1秒。固定loss例取upload packet12，即默认偏移300,000bytes；它不是scope建议1000B分段下的12,000偏移，不能混称。

## 状态转移与事件排序

每方向发送端只维护已到达ACK提供的信息：新包满足 `outstanding_unique + length <= cwnd` 且 `packet_end <= sender_known_prefix + receive_window` 才能入队。**入队admission即预留唯一payload credit**，后续FIFO序列化预约不可撤销。此处有意采用队列预留语义，不能改写成无限排队或直到真正发送才占credit。

接收端按packet-ID去重，更新完整已收连续前缀；连续前缀立即进入应用文件存储并释放运输层重组空间，应用仍等整图。ACK携带该包ID和产生时的累计前缀，并排入反向串行器。每个ACK先付自身序列化，再付反向传播。

ACK到达后，只有第一次确认该ID才释放其唯一payload credit并增长cwnd；接收信用只使用ACK携带前缀的单调max增量。发送端不读取接收端即时真实前缀。乱序后段可以选择性释放发送credit，但不能越过未确认连续前缀允许的接收窗口右界。重复数据不增加文件bytes，重复ACK不再次释放credit或增长窗口。

队列使用Fraction精确时间。同刻ACK优先于数据到达和timer；当前时刻事件清空后再入队新数据。ACK或timeout重传的队列预约优先于此时新admission；既有FIFO预约不被抢占。每次数据timer在自身序列化结束+RTO触发，ACK同刻到达可取消。仅允许指定首发丢包的一次有效timeout；未指定包有效超时或二次恢复直接拒绝，提示增大RTO或改变速率/窗口以回到有限合同。无自适应RTO、退避、快速恢复、ACK丢失或拥塞窗口重置。

取消timer可能在很晚的deadline被事件堆读出并记录，但它不占物理资源。`protocol_quiet_seconds_exact`取真实最后ACK到达，绝不取处理完所有取消timer后的堆时钟。

## 一个请求共用双向资源

统一事件引擎保留client→server和server→client两个全双工串行器。数据、ACK和握手均按实际方向竞争，传播不占序列化资源：

- 上传数据与下载ACK共享client→server。
- 上传ACK与下载成片数据共享server→client。
- 上传完整连续接收即启动模型，模型完成即允许响应admission，不等上传最后ACK。
- 尚占回程串行器的上传ACK会推迟响应真正发送，不能在两个transfer之间重置链路可用时刻。

完整成片客户端接收、所有唯一包发送端确认、协议最后ACK分别输出。默认成片没有独立preview元数据，故preview保持null。接收重组buffer峰值不是整个输入文件的存储需求。

连接输入二选一：外部 `connection_ready_seconds`；或最多8条有序 `handshake=[{direction,bytes},...]`。每条消息必须在前一条完整到达后发送，自行占相应链路并计单向传播。不是在原预算上再加一个RTT。固定fresh示例为400B c2s/800B s2c重复两轮，ticket示例为前两条，reused为外部ready=0；这些只是教学消息图，不宣称TCP/TLS/QUIC精确握手。

## 固定结果与复现

```sh
python3 calculations/research/connection-window/calculate.py
```

`result.json`保留六个场景完整packet/window身份日志。默认1400包使文件较大，但没有丢失抽样身份；公共接入可另输出摘要并保留可重现日志。

| 场景 | 完整成片秒 | 真实最后ACK秒 | 有效恢复 |
|---|---:|---:|---:|
| reused，默认窗口 | 13.4612448 | 13.5112608 | 0 |
| fresh，两轮消息 | 13.6616928 | 13.7117088 | 0 |
| ticket，一轮消息 | 13.5614688 | 13.6114848 | 0 |
| receive window50kB | 76.42544 | 76.475456 | 0 |
| 上传packet12首发丢失 | 14.1507488 | 14.2007648 | 1 |
| 足够大窗口、零头/零ACK bytes | 12.8 | 12.85 | 0 |

最后一行回到明确单向传播的12.8秒整图接收基线，而发送端最后ACK仍需传播，不能将两终点合并。上/下行payload BDP分别250,000/1,250,000bytes；BDP只是无头载荷的速率×往返传播，不自动等于足够协议窗口。

根独立10byte stop-and-wait基准已实际代入：4/4/2bytes、头1byte、双向8bit/s、ACK1byte、前向2秒/反向3秒、固定window4、growth0，数据到达7/18/27秒，上传最后ACK31秒；输出精确匹配 `handcheck.md`。候选正式独立审查由另一个代理进行，结果另附，不以内部守恒替代外部oracle。

## 输出结构

- `transmissions`：唯一记录ID、kind、direction、packet/offset/attempt、payload/wire bytes、队列/开始/结束时刻及丢弃标志。
- `data_arrivals`：packet身份、重复标志、唯一已收bytes、真实累计前缀。
- `ack_arrivals`：新确认标志、释放唯一在途bytes、ACK携带前缀、新增已知接收信用。
- `window_events`：起始/admission/ACK/阻塞/重传时刻，cwnd、唯一在途、sender已知前缀、允许右界、send/rwnd阻塞原因。
- `timer_events`：每次generation deadline与取消/重传状态；取消deadline不表示协议忙。
- `application_events`、`transfers`、`links`：模型和交付事件、各方向完整接收/ACK时间、重传和ACK wire bytes、串行器忙时/最后可用时刻。

本交付只算一个请求及有限握手图。四请求序列、暖窗口继承、真实TLS/QUIC握手/0RTT接受拒绝、多流与媒体截止、ACK合并/丢失和C69半双工空口模型保留原C68/C69缺口，不应因本候选勾选整项完成。
