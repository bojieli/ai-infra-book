# Independent window/ACK hand checks

These are exact acceptance examples for the declared finite protocol, not measured TCP behavior.

## Fixed one-packet window, no loss or growth

Let n packets have payload lengths p_i, data overhead h bytes, data-link rate B bits/s, ACK length a bytes, reverse-link rate A bits/s, and one-way propagation f and b seconds. There is no other traffic and window credit is released only when the packet ACK arrives. For packet i after packet i−1, sender start advances by 8(p_(i−1)+h)/B + f + 8a/A + b. Therefore complete receiver time from first send is:

T_receiver = sum_i 8(p_i+h)/B + n*f + (n−1)*(8a/A+b).

T_last_ACK = T_receiver + 8a/A + b.

Test a partial last segment: 10 payload bytes in4/4/2, h=1, B=8bits/s, a=1, A=8bits/s, f=2,b=3. Data durations5/5/3s, ACK serialization1s. Send starts0/11/22s; receiver arrivals7/18/27s; ACK arrivals11/22/31s. Complete receiver27s is distinct from final ACK31s. Unique delivered10bytes; wire data13bytes and ACK3bytes. An initial window of4bytes and no growth is sufficient for each segment but not two concurrently.

## Unlimited window without reverse bottleneck

When all packets can be issued and no other traffic contends, complete receiver=sum(data serialization)+f; one-way propagation is not charged on the data serializer for each packet. ACK generation occurs after reception, reverse ACK serialization is a separate FIFO max-plus recurrence. A sufficiently slow ACK path can extend sender completion after the complete receiver endpoint, even while it no longer affects that file's receiver completion.

## One declared loss with a fixed timeout

For one data packet with duration d, forward f, ACK serialization a_t and reverse b, first transmission is dropped after paying d. If a fixed retransmission timer is set at serialization end plus R, retry begins at d+R (provided the data link is otherwise idle). Complete receiver=2d+R+f; final ACK=2d+R+f+a_t+b. Physical data bytes double but unique payload and credited ACK growth do not. This fixed timer is not RFC6298's RTT estimator/backoff/oldest-outstanding timer.

No-loss ACK exactly at its timer deadline must cancel the timeout. Thus with d=1,f=2,a_t=1,b=3, R=6, ACK arrives7 and timer is7; no retry is valid. R below6 would exceed the intended single-loss contract rather than silently becoming a different recovery algorithm.

## Response begins at complete received, shared ACK resource remains occupied

The model begins at the upload receiver completion and response becomes ready after model time, independently of upload last ACK. However the upload ACK's reverse serializer reservation still occupies the same direction used for the response. The response must respect this reservation rather than resetting the reverse link clock. File arrival and ACK completion cannot be used interchangeably.

## Source boundary

Research-local RFC5681/6298/8446 files were independently reread against recorded lengths and SHA256 before these checks. Their existence does not imply the candidate implements them. RFC6298 section5 restarts the timer on newly acknowledged data, retransmits earliest unacknowledged data and backs off RTO; a fixed per-packet timeout with one permitted retry has different semantics. RFC5681 congestion response is also distinct from fixed ACK growth without loss window reset. Any such departures must be in candidate output and final teaching prose.
