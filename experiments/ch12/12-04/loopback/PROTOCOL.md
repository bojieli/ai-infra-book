# 12-4：真实 loopback HTTP 传输首轮协议

范围是基础传输夹具，不等于原第12-4项图片精修、ASR/TTS、Computer Use业务结果或固定WAN/移动链路实验。只用本地Mac真实TCP/UDP sockets，不设网络模拟、限速或人工丢包。TCP路径使用h11 HTTP/1.1和Python/OpenSSL TLS1.3；QUIC路径使用aioquic1.3.0 HTTP/3，ALPN h3、证书验证开启。不同协议栈实现也是变量，不能归因TCP/QUIC本体优劣；没有HTTP2。

固定64KiB确定性字节载荷，每请求POST上传并由服务器原样回传，客户端逐字节SHA256校验。三个trial，每组8请求。协议×新连接/复用×并发lane1/4共8条件，每trial内seed1204打乱，合计192请求。每lane独立连接，主并发4条件两协议均4个复用连接，不把连接数差异当多流收益。本首轮不额外叠加HTTP3单连接多流条件。

正式前每协议各一次同payload真实warmup，单独记录，不进入主统计。每请求分别记录尝试开始、连接就绪/握手、发送、首个响应头/数据、完成与校验、连接ID和源端口。新连接模式每请求新TLS/QUIC连接，不主动提供session ticket或0RTT；复用模式每lane第一请求建连。响应结束后连接暂留至组末统一关闭，避免将各协议连接关闭等待混入下一请求。记录客户端HandshakeCompleted、ALPN、session_resumed/early_data与qlog；HTTP1.1记录TLS版本/cipher/ALPN/session_reused。两路径同证书，验证localhost/IP SAN，不关闭CERT_REQUIRED。

先独立smoke（每条件2请求、1trial），失败保留；正式192请求必须全部错误/成功均记录，不能只统计成功后隐去失败。服务器只做echo，不执行模型。计时包括本机客户端/服务端栈开销，不是纯传输传播时间。证书生成、服务器启动、预热、连接关闭/qlog落盘均与请求指标分开。记录环境、依赖锁、源码SHA、实际端口/握手、所有响应hash，原始数据+图按需+README封存。若执行缺依赖，只报告事实，不装系统服务。
