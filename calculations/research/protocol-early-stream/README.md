# QUIC v1 长早期上传：逐包密钥切换与拒绝后的应用重试

这是 C68 的独立研究候选，不修改已经冻结的 `protocol-handshake`。默认案例声明上传30,000,000B、完整输出5,000,000B、模型处理0.3s、上行20Mbps、下行100Mbps、单向传播50ms。它计算列出的数据包及消息依赖，不执行网络栈或模型。

```bash
python3 calculations/research/protocol-early-stream/calculate.py \
  --output calculations/research/protocol-early-stream/result.json
# 只算一个输入：增加 --inputs path/to/input.json
```

`calculate(inputs)` 接收单场景，`example()` 给出30MB参数，`scenarios()` 给13个固定场景：30MB和100B请求的接受／授权重试／未授权重试，三项整数手算，两个密钥在包中途到达案例，以及4800B服务器flight的有／无Handshake ACK对照。

## 必须追踪的身份和事件

每个应用包显式保存 `stream_id=0`、`offset`、`end_offset`、`payload_bytes`、`encryption_level`、`packet_number_space=application` 和 `packet_number`。每个方向的0RTT／1RTT共用单调递增应用包号，密钥切换及重发不重置包号；重发相同STREAM范围用新包号。控制消息未展开完整包号空间，属于下述完整协议实现缺口。

发送器只有在链路空闲并实际开始发送时选密钥，未发送的应用尾部不提前占据FIFO。已排队控制消息按FIFO先于尚未进入链路的应用包，这是声明的调度策略。已经开始序列化的包不可抢占：密钥在其中途安装，该包继续作为0RTT发送，下一包开始时用1RTT。同刻事件顺序为到达／密钥安装、序列化结束、调度发送，避免同刻多发一个旧密钥包。

接受早期数据时，服务器将实际收到的0RTT范围和后续1RTT尾部组成同一有效输入。拒绝时，实际发送的0RTT范围无效；只有 `application_retry_authorized=true` 才重启应用发送范围，将此前发送的范围以1RTT重发，再继续未发送尾部。关闭授权则停止尚未开始的尾部，已开始包保留线上字节，执行0次且不伪造完整响应。发送早期数据自身另需 `application_early_data_authorized=true`，凭据有效与应用允许重放是不同前提。

服务器以实际到达且有效的唯一范围累计完整输入。`application_policy` 可选择立即处理或等客户端Finished；执行次数只在完整请求满足政策时增加一次。响应也逐包发送并累计完整有效输出，不把首包到达当作5MB完整结果。

## 时间、字节和地址验证

每方向一个串行器；Fraction计算每包 `8 × (UDP payload + 28) / rate`，传播不占链路。默认每包至多1100B有效payload，0RTT额外声明64B、1RTT48B，用于包头/frame/tag预算；IPv4+UDP再加28B。`response_overhead_bytes` 可另声明响应布局，默认等于1RTT额外字节。32B保守下限只是排除明显不足，未替代真实CID、变长整数、STREAM frame或AEAD编码器。末包按剩余有效字节缩短。

第一客户端Initial和服务器ack-eliciting Initial最少1200B UDP payload。第一server包假定完整承载ServerHello，后续包用Handshake密钥。服务器未验证前最多发送实际收到UDP payload的3倍，按实际开始发送扣预算。第二server包到客户端可触发显式Handshake ACK；服务器收到Handshake包就验证地址，无须等全部Finished。列出受阻事件，4800B无ACK停住仅表示本消息图缺解除事件，不是实际QUIC死锁结论。

所有来源在 `../protocol-handshake/sources.lock.json`，输出 `reference_source_root` 给出该解析根；七份原件每次检查长度及SHA256。规范约束来自官方原件，默认消息长度与业务参数是声明值。

## 手算可复核边界

所有UDP包1200B、每向9824bps让线上1228B恰好序列化1秒，传播1秒。请求6×1168=7008B，响应100B单包，服务器两包flight。密钥恰在5秒安装，早期发送4包共4672B；Handshake ACK与Finished占5–7秒。

- 接受：剩余两包7–9秒发送，完整请求10秒，完整响应12秒。
- 拒绝且授权：6包1RTT在7–13秒发送，完整请求14秒，完整响应16秒。
- 拒绝且未授权：只有4672B早期payload，执行0次，无完整输出。

改反向传播为1.5秒会让密钥落在已发包中途，用于验证非抢占边界。

## 保留的缺口

没有拥塞／流控、一般ACK、PTO、loss、重传计时器、HTTP/3 SETTINGS、Retry、HRR、无效票据回退及后台票据。零RTT拒绝的应用重试不等同于网络丢包重传。地址budget与一次Handshake ACK不是完整QUIC实现。30MB結果因此是所声明链路和消息图的计算，不能称真实QUIC吞吐或端到端实测。

最多100000个原始应用包，包含控制与最多一次全请求重发的保守预算最多200000包。整项C68仍未完成；公共CLI、正文和上述范围须继续接入或实现。
