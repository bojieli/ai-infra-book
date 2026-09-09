# What a China-US datacenter path actually is (2026-08-26)

A Huawei Cloud instance in Guiyang and a colocated server in Irvine,
California. This is the first path we've characterized for the datacenter
profile. We picked it because it matches that profile's shape: a long hop
between two machines one operator runs, carrying request/response traffic of a
few hundred kilobytes.

Measured with `pathprobe` (open-loop UDP) and `pathmeasure` (new in this
branch). To re-run any of this, see
[MEASURING-A-DC-PATH.md](MEASURING-A-DC-PATH.md).

## The path

| Property | Value |
|---|---|
| Round trip | 199-207ms, min 185.9ms |
| Jitter at 1 packet/s | mdev 0.58ms over 30 probes |
| Path MTU | 1500, no blackholing |
| Capacity knee, downstream | ~333 Mbit/s |

A round trip whose min and max are 3ms apart isn't queueing anywhere. So
whatever the loss turns out to be, it isn't congestion.

## The two directions behave like different paths

<p align="center">
  <img src="../assets/two-directions.svg" alt="A diagram showing the two directions behaving as different channels. Guiyang to Irvine lost zero of 41,663 datagrams at 50 Mbit/s. Irvine to Guiyang erases about 14 percent at every offered rate from 1 to 300 Mbit/s, rising to 44 percent only above the 333 Mbit/s knee. Cubic reads the flat erasure as congestion and settles at a fraction of a megabit, while an open-loop probe pulls 256 Mbit/s across the same channel." width="880">
</p>

| Direction | Protocol | Loss | Throughput |
|---|---|---|---|
| Upload, CN→US | UDP 50 Mbit/s | **0.0%** (0 of 41,663) | 49.99 Mbit/s |
| Upload, CN→US | TCP cubic | 0.36-2.90% retransmitted | 73-94 Mbit/s |
| Download, US→CN | UDP 1-300 Mbit/s | **~14%** | knee ~333 Mbit/s |
| Download, US→CN | TCP cubic | -- | **0.13-0.47 Mbit/s** |

Our first reading of this data said UDP was being policed 20-40x harder than
TCP. That was wrong. `pathprobe`'s server does the sending, so it measures the
download; `pathmeasure`'s client does the sending, so it measures the upload.
We were comparing directions, not protocols. `pathmeasure -mode udp` exists
because of that mistake.

## Download loss is memoryless and doesn't depend on rate

| offered Mbit/s | delivered | loss | P(loss\|prev ok) | P(ok\|prev lost) | burst factor |
|---|---|---|---|---|---|
| 1 | 0.85 | 14.5% | 0.136 | 0.802 | 1.07 |
| 5 | 4.13 | 17.5% | 0.181 | 0.854 | 1.00 |
| 20 | 17.01 | 14.9% | 0.072 | 0.408 | 2.08 |
| 150 | 129.19 | 13.9% | 0.136 | 0.843 | 1.02 |
| 300 | 256.15 | 14.6% | 0.141 | 0.825 | 1.03 |
| 600 | 333.49 | **44.4%** | 0.490 | 0.613 | 1.00 |

For a memoryless channel with loss `p`, you expect `P(loss|prev ok) = p` and
`P(ok|prev lost) = 1-p`. At 1, 150, and 300 Mbit/s the measured pairs match
within sampling noise. Delivered rate scales linearly all the way to 300
Mbit/s, so nothing is congested below that. At 600 the loss jumps to 44.4% with
a longest run of 795 packets. That's the knee, and it's the only point on this
path where loss actually means congestion.

The high burst factors at 20-80 Mbit/s are an artifact of how the probe
releases packets, not something the path is doing. They disappear at 150 and
300 Mbit/s, where we have two orders of magnitude more samples.

**What TCP does with this.** Mathis gives `MSS/(RTT·√p)` = 1448/(0.2·√0.14) =
**0.155 Mbit/s**. We measured 0.13-0.47. TCP isn't broken. It's responding
correctly to a loss signal that carries no information here, while the
open-loop probe pulls 256 Mbit/s across the same channel.

## Sustained throughput, which this document had never measured

Everything else here measures how long a request takes. That is the workload,
and it left a gap: the profile also carries transfers, and nobody had asked what
either transport does when a flow runs long enough to reach a steady state.

<p align="center">
  <img src="../assets/sustained-throughput.svg" alt="A bar chart of sustained single-flow throughput. An open-loop UDP probe measures the path's capacity knee at 333 Mbit/s with no congestion control involved. Direct TCP cubic ranges 3.6 to 105.8 Mbit/s across five runs on the upload and 68 to 84 on the download. Queqiao reaches 310 and 268. A CPU profile of the transfer puts encryption under 2 percent and the coding below the top twenty, with the syscall per batch of packets dominating." width="880">
</p>

One flow, 15 to 20 seconds, arms alternated, upload direction:

| | direct TCP cubic | queqiao |
|---|---|---|
| best of five runs | 105.8 Mbit/s | **310.4 Mbit/s** |
| worst | 3.6 Mbit/s | 0.4 Mbit/s |
| typical | 30 to 100 Mbit/s | 144 to 310 Mbit/s |

310.4 Mbit/s is 93% of this path's 333 Mbit/s knee, which is what an open-loop
UDP probe measured with no congestion control involved at all. Downstream the
gap is wider still, because that is the direction that erases: 68 to 84 Mbit/s
direct against 224 to 268 through the transport.

Both arms vary enormously, and two different causes are mixed into that. The
path's loss moves, which is what takes direct upload from 3.6 to 105.8 Mbit/s
across five runs in one session. And the client host is a single core shared
with other work, which is what takes the tunnel down to 0.4 Mbit/s in one run
and is not a property of either transport. Quote the range, not a figure from
it.

### The ceiling is CPU, and this host cannot say how much

Sampled during a 310.4 Mbit/s upload, `queqiaod` was using 75.3% of a single
core with 22.5% idle. That reading is not trustworthy and the reason is worth
recording: the client host has one core and other things running on it. A later
sample of the same measurement found 64.6 Mbit/s with the core 92% in kernel
mode, and the cause was a Python process belonging to somebody else taking 58%
of it. The run that collapsed to 0.4 Mbit/s was almost certainly the same thing.

What survives is the direction rather than the figure. The transport is
userspace QUIC plus coding and it costs real CPU, enough that on a busy single
core it becomes the binding constraint before the path does. How much is a
question for a host that is not shared, and this one is.

Two things a profile does settle, because they are ratios within the process
rather than shares of a contended machine. Encryption is not the cost: AES-GCM
is 1.7% of samples, hardware-accelerated. Neither is the coding: the `fec` and
`coded` packages do not appear in the top twenty. What dominates is the syscall
per batch of packets, which is what userspace UDP is.

That cost is already half-optimised and the half that is missing is upstream.
The QUIC stack sets `UDP_SEGMENT`, so a send hands the kernel up to 64KB and it
splits that into datagrams: one syscall for roughly forty packets. Receives get
`recvmmsg` batching instead, which is one syscall for a batch of separate
messages rather than one coalesced read. Checked against upstream quic-go
v0.61.0 as well as the fork this project uses, `UDP_GRO` appears in neither, and
the receive path's control-message parser handles only TOS and packet
information. So the asymmetry is real and it is not something this repository
can close.

## Flow completion time

Upload direction, cubic, at the payload sizes an inference call actually sends:

| size | cold | warm-first | warm | floor |
|---|---|---|---|---|
| 100KB | 836-2009ms | 742ms | 186-763ms | ~200ms |
| 300KB | 1172-1198ms | 1029ms | **209ms** | ~200ms |
| 1MB | 1560-1721ms | 1687ms | **212ms** | ~200ms |

A warm connection is worth 5.7x at 300KB, and 209ms on a 200ms path is one
round trip, which is the floor.

The first flow on a warm connection isn't warm: 1029ms, versus 209ms for the
ones after it. Reusing a connection saves the handshake right away and saves
the ramp later.

Small flows have worse tails than bigger ones, which is backwards from what
you'd expect. 100KB is about 70 packets, too few to reliably generate the three
duplicate ACKs that fast retransmit needs, so a loss falls through to a
timeout.

## A long-lived connection doesn't stay warm

Six 300KB bursts on one connection with 3s idle between them, which is roughly
what an interactive session looks like:

| burst | cubic, `ssai=1` | bbr, `ssai=1` | cubic, `ssai=0` |
|---|---|---|---|
| 0 | 941.9ms | 1082.6ms | 1028.5ms |
| 1 | 941.0ms | 317.3ms | **209.1ms** |
| 3 | 941.9ms | 288.5ms | **208.7ms** |
| 5 | 941.0ms | 284.9ms | **209.0ms** |

With Linux's default, cubic runs full slow start on every burst, forever. 941ms
is five round trips, repeated six times, on a connection that stayed open the
whole time.

BBR doesn't reset, because `tcp_slow_start_after_idle_check()` returns early
for any controller that provides `cong_control`. It settles at 285ms instead.
The remaining gap is pacing: BBR paces at a bandwidth estimate it derived from
these same bursts, and `app_limited` reads true from burst 1 on.

Setting `tcp_slow_start_after_idle=0` gets cubic to 209ms. **One sysctl, worth
4.5x**, and tuned cubic then beats BBR because cubic doesn't pace.

**Loopback, for scale.** The same 300KB takes 0.1ms (28.9-31.5 Gbit/s) on the
same server talking to itself, versus 209ms across the path. Every constraint
above is a function of the round trip.

## How much of the win is ours, and how much is just QUIC

`internal/baseline` implements TUIC's data-path shape on the same QUIC fork in
the same process, so any gap between them is design rather than library.
Order-alternated, download direction:

| payload | direct TCP | TUIC-shaped QUIC | Queqiao | QUIC's share | coding adds |
|---|---|---|---|---|---|
| 100KB | 1918.4ms | 401.0ms | **218.5ms** | 4.8x | 1.84x |
| 300KB | 5449.7ms | 791.7ms | **399.1ms** | 6.9x | 2.0x |

Getting off TCP accounts for most of it. The honest claim is that Queqiao is
about twice as fast as a well-tuned QUIC tunnel here, not fourteen times TCP. A
comparison table without the QUIC arm overstates our contribution by about 7x.

The spread is more interesting than the median. Sixteen consecutive 100KB
downloads through Queqiao spanned **16ms** (204-220), on a channel dropping a
seventh of everything. The same sixteen over TCP spanned four seconds.

On the clean upload direction with a warm connection, the tunnel **costs**
50-75ms. That's the price of a userspace proxy plus an extra local hop.
Queqiao is the cheaper of the two tunnels by 21.8ms.

## Concurrency: the two workload shapes disagree

**Requests**, 300KB each, all started at once, against the reference (emulated
path):

| concurrency | queqiao | reference |
|---|---|---|
| 4 | 4/4, p99/p50 **1.07** | 4/4, p50 **35637ms** |
| 16 | 16/16, p99/p50 **1.06** | **0/16 completed** |
| 48 | 48/48, p99/p50 **1.05** | **0/48 completed** |

Every flow completes and the tail stays within 7% of the median. 48x the load
costs 2.7x the latency. The reference falls over at sixteen.

On the live link the same pattern holds, and the tunnel moves 2.5x the
aggregate at 16 and 32 flows (86.1 versus 35.4 Mbit/s).

**Frames**, 80 bytes every 20ms, 24 sessions (emulated): p50 203.3ms against a
200ms floor, p90 208.2ms, then **p99 766.6ms**, with 4.96% of frames arriving
more than one frame interval late.

That's the opposite of the request result, and the cause is payload size. An
80-byte frame is a single packet. There's no block to code over and no traffic
behind it to expose the loss, so it waits out a timeout.

## What fixes the frame tail: using the carrier voice actually uses

The frame tail above was measured over a reliable ordered stream, and that was
the wrong shape. A voice stream is not carried on TCP, and measuring it as if
it were reports a problem the application does not have.

The mechanism is visible in the transport's own counters. Across a 52-second
session on the emulated 14% path, the coded substrate carried 2270 symbols,
recovered 1708 of them, and lost 5. Five failures cannot make one percent of
frames slow on their own. They do it by stalling everything queued behind them,
which is what an ordered stream does and what a datagram does not.

Measured on the live path, 16 sessions of 200 messages, with downstream loss at
3.6% during the run:

| carrier | delivered | lost | p50 | p90 | p99 | p99/p50 | >250ms |
|---|---|---|---|---|---|---|---|
| UDP, direct | 3037 | **163** (5.1%) | 193.6ms | 205.6ms | 213.7ms | **1.10** | 0.00% |
| UDP, through Queqiao | 3166 | **34** (1.1%) | 208.2ms | 213.9ms | 217.6ms | **1.05** | 0.00% |
| TCP, through Queqiao | 3200 | 0 | 208.4ms | 214.0ms | **728.4ms** | **3.49** | 2.16% |

Over UDP the transport removes four fifths of the lost frames, from 5.1% to
1.1% on a path erasing 3.6%, and the tail stays flat: p99 is five percent above
the median rather than three and a half times it. That is the code repairing
gaps inside the round trip that carried them, which is what it was built to do.

Over TCP nothing is lost and the tail is 728ms, because reliability converts
every gap into delay for the frames behind it.

So there is no missing coding scheme here. UDP ASSOCIATE has been in this
transport since the beginning, and a voice application using it gets both
properties at once. The earlier reading of this as an open problem came from
measuring frames over a stream, and the tool now measures both carriers so the
mistake is harder to repeat.

A separate defect did turn up while chasing it, and it was real: whether a flow
counted as a series of small exchanges was decided from its lifetime byte
total, so any long conversation eventually stopped qualifying and was demoted
to bulk, losing its coding after about a minute. That signal is now a rate over
a recent window, which a transfer never drops under and a conversation never
reaches whatever its age.

## HTTP/2 flow control, and an ingress for receivers you don't control

Same 1MB upload to the same server, varying only the window it advertises:

| receiver window | 300KB warm | 1MB warm |
|---|---|---|
| Go `http2.Server` default | 187.5ms | 193.2ms |
| 8MB explicit | 191.3ms | 200.6ms |
| **65535, the RFC default** | **912.7ms** | **3903.0ms** |

Twenty times slower, and it matches the arithmetic: the window is credit per
round trip, so 1MB over 64KB is sixteen round trips. That predicts 3.2s and we
measured 3.9.

But `x/net/http2` defaults both upload buffers to 1MB, and gRPC-go sizes its
window from a measured BDP. 64KB is what RFC 7540 specifies, not what a default
Go service advertises. So the claim to make is narrower: when the window really
is 64KB it dominates everything else by 20x, and whether it's 64KB depends on
the implementation. Check before assuming.

An L7 ingress placed next to an **unmodified** 65535 server, reached across the
200ms path: 300KB warm goes 998.0ms → **184.8ms**, and 1MB warm goes 3394.9ms →
**190.8ms**, a **17.8x** improvement with nothing changed on the far side. A
window is credit per round trip, so shortening the trip makes it irrelevant.
190.8ms is one round trip, which also confirms the ingress streams rather than
buffers.

## One relay or several

24 concurrent 300KB requests, either all through one client or split eight
apiece across three independent clients, run in both orders:

| order | one relay | three relays |
|---|---|---|
| shared first | 1696.9ms, **34.6 Mbit/s** | 750/1176/1302ms, **57.5 Mbit/s** |
| split first | 1963.8ms, **29.8 Mbit/s** | 396/1187/1382ms, **78.7 Mbit/s** |
| split first, repeat | 2540.6ms, **23.1 Mbit/s** | -- |

Three relays beat one by about 2.5x on aggregate, in both orders. Three tunnels
are three congestion controllers probing a 333 Mbit/s path at once. One tunnel
is one controller, and there's no shared bottleneck here for the coordination
to help with.

We retired multipath on the opposite evidence: four lanes delivering 8 Mbit/s
where one delivered 11. Both results are correct, for different paths. On an
access link the bottleneck is the client's own uplink, and you can't split a
share that doesn't exist.

What sharing does buy is fairness. All 24 flows through one relay finished
within 2ms of each other (p99/p50 of 1.00), while the split arm's three groups
spread out by 3.5x.

## The path isn't stationary, which changes what every number above means

Downstream loss, three readings about ten minutes apart:

| when | offered | loss |
|---|---|---|
| t+0 | 2 Mbit/s | **0.0%** |
| t+0 | 20 Mbit/s | **2.4%** |
| t+9min | 20 Mbit/s | **9.1%** |

Earlier the same evening it read 9.8-17.5%. The same download comparison gave
**13.5x** when the path was dropping 14% and **6.5x** when it was in the single
digits. Both numbers are right. The transport repairs erasure, so its advantage
scales with how much erasure there is. The useful answer is the relationship,
not either endpoint.

Two things follow. **Take a loss measurement alongside every comparison.** And
**always alternate the order**: position in the test sequence was worth 158ms
here, while one policy we were testing was worth 2.4ms. Running the baseline
first showed a 53% win that flipped when we reversed the order. `pathmeasure
-mode ab` alternates and pools automatically, and tells you when the order
effect is bigger than the effect you're measuring.

## Two measurements that couldn't answer their question

**Does aggregating flows replace the need to probe?** We watched the
controller's counters across 1/4/16/32 concurrent flows. The non-app-limited
count stayed frozen at 79 and the bandwidth estimate read zero, even during a
sustained 30MB transfer at 285.8 Mbit/s.

That looks like a bug and isn't. `bbr_tuic.go` documents both halves: marking
app-limited on any unused congestion window is deliberate (tightened twice,
reverted twice), and the metrics endpoint reports the pooled control
connection, which really is idle. Answering this needs per-lane trace data.

At the level of outcomes, the claim's shape holds: aggregate throughput went
from 11.7 to 163.8 Mbit/s between one flow and thirty-two, with the tail
staying tight.

**Are frames late more often direct than tunnelled?** Our first live comparison
said 30% versus 2%. It counted lateness against each arm's own floor, so the
arm with the 10ms lower median had 10ms more room under its own bar. Against
fixed thresholds the difference disappears. A listener doesn't have a relative
bar.

## End-to-end validation, both profiles, all three carriers

One run per profile, on the live path, with the loss measured before and after
so each row can be placed against it.

**Datacenter profile** (loss 13.6% falling to 1.6% during the run):

| workload | arm | result |
|---|---|---|
| 16 concurrent 300KB requests | direct | p50 947.1ms, p99 1135.4ms, 22.5 Mbit/s |
| 16 concurrent 300KB requests | tunnel | p50 1852.7ms, p99 1857.8ms, 21.1 Mbit/s |
| 8 UDP frame sessions | direct | 40 of 1200 lost, p99 210.1ms |
| 8 UDP frame sessions | tunnel | **2 of 1200 lost**, p99 213.5ms |
| 8 TCP frame sessions | tunnel | 0 lost, p999 731.7ms, 0.58% over 250ms |

class transitions: interactive 8, **bulk 0**

**Access-link profile** (loss 2.4% rising to 3.0%):

| workload | arm | result |
|---|---|---|
| 16 concurrent 300KB requests | direct | p50 960.3ms, p99 1063.3ms, 17.2 Mbit/s |
| 16 concurrent 300KB requests | tunnel | p50 1713.3ms, p99 1748.4ms, 21.9 Mbit/s |
| 8 UDP frame sessions | direct | 156 of 1200 lost, p99 212.1ms |
| 8 UDP frame sessions | tunnel | 45 of 1200 lost, p99 215.0ms |
| 8 TCP frame sessions | tunnel | 0 lost, p99 599.9ms, 1.67% over 250ms |

class transitions: interactive 8, **bulk 16**

Three things this shows.

**The profile difference is real and visible in the counters.** Sixteen request
flows are demoted to bulk on the access-link thresholds and none on the
datacenter ones, which is exactly what those thresholds were changed for: a
300KB request is one ordinary request on a datacenter leg and a transfer on an
access link. A demoted flow stops preferring coding, which on an erasing path
is the difference between repairing a gap inside the round trip that carried it
and waiting out a timeout.

**Frames over UDP gain in both profiles**, by twenty times in one run and three
and a half in the other. The two runs saw different loss, so the ratio between
them means nothing; what transfers is that the transport repairs most of what
the path erases while leaving the tail flat.

**The tunnel trades median for variance on concurrent requests.** Direct gives a
lower median and a wider spread; the tunnel finishes nearly every flow together
-- p99/p50 of 1.00 and 1.02 against 1.20 and 1.11 -- at a similar aggregate and
wall time. That is the same fairness the relay comparison found, seen from the
other side, and it is a choice rather than a defect.


## Re-validated after the classification and carrier changes

The same run again, with the fixes in place and grouping discovery enabled
(loss 1.5% rising to 4.7% during it):

| workload | arm | result |
|---|---|---|
| 16 concurrent 300KB requests | direct | p50 991.2ms, p99 1062.7ms, 17.8 Mbit/s |
| 16 concurrent 300KB requests | tunnel | p50 1732.6ms, p99 1736.2ms, 22.6 Mbit/s |
| 8 UDP frame sessions | direct | 52 of 1200 lost, p99 212.4ms |
| 8 UDP frame sessions | tunnel | **15 of 1200 lost**, p99 209.8ms |
| 8 TCP frame sessions | tunnel | 0 lost, p99 737.1ms, 2.58% over 250ms |

class transitions: interactive 8, **bulk 0**

Every request flow completes, no session is demoted, frames over UDP lose a
third of what they lose direct while the tail stays flat, and frames over TCP
show the same tail they always do. Letting the tree rearrange itself from
measured correlation changed nothing here, which is what a path with one
destination group should show.

## Does aggregation give the estimator real evidence?

A bandwidth estimate only improves from samples that were not
application-limited. An earlier attempt to answer this read the aggregate
metrics endpoint and saw a frozen sample count and a zero estimate, which is
what that endpoint reports: one lane, and under pooling that is the idle
control connection.

Read from the per-lane trace instead, on the lane carrying data:

| concurrent flows | non-app-limited samples | bandwidth estimate |
|---|---|---|
| 1 | 12 | 6.8 Mbit/s |
| 4 | 30 | 24.6 Mbit/s |
| 16 | 31 | **87.6 Mbit/s** |

The estimate rises thirteenfold with concurrency and the non-app-limited count
accumulates rather than staying at whatever the handshake produced. An
aggregate fed by many flows does give the estimator evidence a single bursty
flow cannot, which is the argument the node-relay shape rests on. The sample
count plateaus while the estimate keeps climbing, which is the max filter
keeping its best sample and is what it is for.

## The whole stack, on the live path

An unmodified application, captured by a netfilter rule and carried through a
local agent into the tunnel:

```
app -> capture -> SOCKS5 -> queqiao client -> WAN -> gateway -> destination
```

| path | 300KB cold | warm |
|---|---|---|
| direct | 1089.3ms | 1001.4ms |
| through the stack | **624.9ms** | **381.2ms** |

The connect leg is the part worth reading: 0.2ms against 187.3ms. The
application's connection terminates on loopback, and the round trip it would
have paid was already paid by a tunnel that stayed warm. Every constraint
measured in this document is credit per round trip, and this is what putting a
zero-round-trip segment at each end does about them.

The application was never configured for any of it.

## The two projects as one system, on the live path

Both real components, no stand-ins: an application inside a captured cgroup,
`tunless` capturing it with eBPF and serving flow attribution, and the queqiao
client asking that agent what opened each flow before deciding what it is.

```
pathmeasure (in a captured cgroup)
  -> tunless eBPF capture -> SOCKS5 -> queqiao client -> WAN -> gateway
                                  \-- metadata lookup --/
```

The client logged, for each flow:

```
flow class declared from attribution  identity="path=/tmp/pathmeasure"  class=1
```

and `queqiao_class_transitions_1_total` reached 2, one per flow. The class was
known before either flow carried a byte, which is the second the classifier
would otherwise have spent inferring it -- and which a request finishing in
200ms spends entirely inside.

300KB cold through the whole stack: 686.1ms, against 1111.1ms for the same
request when the agent was not running.

Two things the components refused, correctly, on the way to this working. The
metadata server would not open its socket in a directory that grants group or
world access, because that socket answers questions about what processes are
doing. And the preflight refused to attach a capture to a cgroup containing
tunless itself, which would have captured the agent's own connection to its
upstream and re-captured every packet it forwarded.

> [!IMPORTANT]
> The ASR and TTS figures in this section were taken with a benchmark that
> rotated eight audio files from 146KB to 405KB while reporting only the last
> request's size, so every number labelled "a 355KB upload" is a median across
> that whole range and not the 355KB case. They are superseded by
> [the single-file re-measurement](#re-measured-with-one-fixed-file) below,
> which also postdates the pacing fix. Kept because the reasoning they
> prompted was sound and because a retracted measurement should stay visible.

## The workload this was built for

Everything above uses synthetic transfers. This section runs the actual thing.
The Irvine host serves SenseVoice ASR at `/v1/audio/transcriptions` and Fish
Audio S2-Pro TTS at `/v1/audio/speech`, both OpenAI-shaped. The client in
Guiyang posts real speech and asks for real synthesis. Both arms cross the same
reverse proxy on the inference host, so that hop cancels.

Arms alternate order every round, and each round's pair is compared against
itself, so a path that drifts during the run cannot be mistaken for a result.

### ASR upload

Eight WAV files, 146KB to 405KB, which is the size range that started this
whole line of work. The response is 150 bytes of transcript. Twenty paired
rounds, new connection each time:

| | direct | queqiao |
|---|---|---|
| total p50 | 1133.5ms | **290.2ms** |
| total p99 | 1343.6ms | **346.5ms** |
| connect | 187.1ms | **1.0ms** |
| request to first byte | 948.2ms | **289.3ms** |

Paired per-round ratio: median 3.63x, and the middle 80% of rounds fall between
3.47x and 4.21x, which is about as tight as this path gets.

Transcribing a 355KB file takes the model 38ms. Of the 1133.5ms a client in
Guiyang waits, roughly 1095ms is the network, and of that, 187ms is a handshake
that buys nothing and the rest is a 355KB upload climbing out of a 10-segment
initial window on a 199ms path.

### TTS download

The synthesis side is the opposite shape: a 272-byte request, a 100KB MP3 back.
The endpoint does not stream, so the whole file arrives as one burst after the
model finishes. Twenty paired rounds:

| | direct | queqiao |
|---|---|---|
| total p50 | 5661.3ms | 4550.4ms |
| connect | 192.6ms | **0.8ms** |
| request to first byte | 4479.3ms | 4457.7ms |
| download | 916.2ms | **74.9ms** |

The headline is 1.24x and the headline is the wrong number to read. Request to
first byte is 4479.3ms against 4457.7ms, a 0.5% difference, which is what it
should be: that leg is one round trip plus the model, and the model is the same
model on the same GPU either way. No transport does anything about 4.4 seconds
of synthesis.

What a transport can touch is the part that moves bytes, and that part goes from
916.2ms to 74.9ms. Counting the handshake with it, network-attributable time
falls from 1108.8ms to 75.7ms, which is 14.6x, and drops from 21% of the request
to 1.7% of it.

The paired ratio spans 0.90x to 1.42x, wider than the ASR run, because 4.4
seconds of variable model latency sits on top of a network difference of one
second. That is a measurement artifact of dividing by a large constant, not
instability in the transport.

### What connection reuse actually recovers

The advice everyone gives first is to reuse connections. It is good advice and
it is worth measuring, because the assumption underneath it -- that a connection
held open stays fast -- is not true on a stock kernel. Same ASR workload, same
twenty rounds, connections held open between rounds, roughly 1.7s idle in
between:

| ASR, 355KB | direct p50 | direct p99 | queqiao p50 | queqiao p99 |
|---|---|---|---|---|
| new connection each time | 1133.5ms | 1343.6ms | 290.2ms | 346.5ms |
| held open, stock kernel | 789.9ms | 1161.6ms | 292.7ms | 348.8ms |
| held open, `tcp_slow_start_after_idle=0` | **225.8ms** | 1026.5ms | 295.0ms | **373.5ms** |

Reuse on a stock kernel takes 1133.5ms to 789.9ms. That saves the handshake and
nothing else, because `tcp_slow_start_after_idle` defaults to 1 and every idle
gap longer than an RTO throws the congestion window away. The connection is
open. It is not warm.

Turn that sysctl off and the same client reaches 225.8ms at the median, which is
about a round trip plus the transfer, and is roughly the floor for this path. It
also beats queqiao at the median, by 1.3x.

That result belongs in this document precisely because it is the one that argues
against the thing being built. When you control the client, and you can set one
sysctl and reuse a connection, TCP gets to the floor on the median request and a
tunnel is a slower way to get there.

The tail is the other half of the sentence. Direct p99 is 1026.5ms against
373.5ms, and the paired ratio ranges from 0.66x to 2.93x depending on the round.
The rounds where direct wins are the rounds with no loss. The rounds where it
loses by 3x are the rounds where a packet dropped and cubic waited for a
retransmit, on a path whose download direction loses around 14% of packets in a
memoryless pattern that has nothing to do with congestion. Repairing that
without a round trip is the one thing here that a sysctl cannot do.

### The client fix works in one direction only

Run the same tuned client against the TTS side and it stops working. Sixteen
paired rounds, connections held open, `tcp_slow_start_after_idle=0` set:

| download of a 100KB MP3 | direct | queqiao |
|---|---|---|
| new connection, stock kernel | 916.2ms | 74.9ms |
| held open, `ssai=0` | 629.4ms | **71.4ms** |

Tuning the client moves 916.2ms to 629.4ms and then stops, while the transport
sits at 71.4ms either way. That is 8.8x, against the same tuned client that beat
us by 1.3x on the upload.

The reason is in the second table of this document. This path's two directions
are not the same path. Guiyang to Irvine dropped 0 packets out of 41,663.
Irvine to Guiyang erases around 14%, memorylessly, at every rate below the knee.

ASR uploads the audio, so it runs on the clean direction, and on a clean
direction a congestion window that never gets thrown away is all TCP needs. The
sysctl supplies exactly that, which is why it reaches the floor.

TTS downloads the audio, so it runs on the erasing direction, and there the
window is not the problem. Cubic reads 14% loss as congestion and backs off,
and no sysctl changes that, because the sysctl fixes what happens after an idle
gap and this is what happens during a transfer. Repairing an erasure without
spending a round trip on it is a transport decision.

### What this section concludes

Fix the client first. It is free, and on the clean direction it is worth more
than we are: 1133.5ms to 225.8ms on ASR, which beats this profile's 295.0ms.

Then deploy the transport for the three things that fix does not reach:

- **Cold connections.** 1133.5ms against 290.2ms. Anything that dials, or has
  been idle past an RTO, or runs behind a load balancer that doesn't pool.
- **Callers you can't reconfigure.** The sysctl and the connection pooling are
  both client-side changes. Where the client is a vendor's SDK or a customer's
  code, neither is available.
- **Any direction that erases.** 8.8x on TTS download against a fully tuned
  client, and a p99 of 373.5ms against 1026.5ms on ASR. This is the part that
  is actually ours, and it is the part a config change cannot buy.


## A model streaming tokens

Everything above measures a workload that ends. A language model answering does
not: a short prompt goes up, and then the answer comes back a few dozen bytes at
a time for as long as the answer takes. The reader waits for the first token and
then for the stream to keep up, and a total latency hides both.

Measured with `pathmeasure -mode stream` against a generator emitting 300 tokens
at a fixed 30ms cadence, so that the generator is not a variable. Ten paired
rounds, arms alternated.

Two things had to be right before any of these numbers meant anything. The mode
counts tokens rather than reads, because at this cadence over this path several
tokens are in flight and the segments group differently on each arm: one arm saw
907 reads deliver what the other saw as 1536, for the same 2400 tokens. And it
measures lateness against the generator's own schedule rather than the gaps
between arrivals, because a stall followed by a catch-up burst produces one long
gap and a run of zero-length ones, and the median of that looks healthy.

| | direct TCP | queqiao |
|---|---|---|
| time to first token, p50 | 421.0ms | **244.7ms** |
| time to first token, p99 | 471.7ms | **245.7ms** |
| median lateness | 30.1ms | **0.7ms** |
| tokens over 200ms late | 15.99% | **13.48%** |
| tokens over 500ms late | **1.47%** | 3.34% |

The first token arrives 1.72x sooner and the p99 of that is nearly flat, which
is the pooled connection rather than anything clever. The median token tracks
the generator to within a millisecond where direct TCP runs a full token
interval behind.

The last row is the one worth reading. More of the tail was worse through the
transport, which is the opposite of every other result in this document.

### Where that tail came from

Against the TUIC-shaped reference in `internal/baseline`, which runs on the same
QUIC fork in the same process, so the only difference is our coding:

| | reference | queqiao |
|---|---|---|
| time to first token | 247.9ms | 244.7ms |
| tokens over 200ms late | 19.00% | **8.13%** |
| tokens over 500ms late | **0.70%** | 1.91% |

Time to first token is identical, so that win belongs to QUIC and not to us.
Coding more than halves the common case and roughly triples the 500ms tail,
which is the signature of a code that usually works and costs an extra round
trip when it does not.

The transport's own counters said the same thing. Over one stream the code saw
2078 symbols, recovered 322 of them, and failed on 29: a 1.38% residual on a
workload where every unrepaired symbol is a reader watching a sentence stop.

The cause was in how a short block is sized. The code picks a block length by
maximising delivered bytes per symbol time, and prices a retransmission in
symbols the flow could have sent instead. A block that seals short seals because
the producer stopped, so those symbols were never going to be sent: the capacity
is free and the objective was treating it as scarce. At a 1100-byte symbol on
this path's erasure, a single symbol got **no repair at all** at the 20 KB/s
rate estimate a token stream demonstrates, one repair at 100 KB/s, and two at
850 KB/s. The protection followed the estimate, and an application-limited flow
is precisely the one whose estimate is small.

Blocks of four symbols or fewer are now sized to a delivery probability
instead. The change is proven where it can be: at the sizing level it is
deterministic, and the tests fail with the rule disabled.

It is **not** proven end to end on this path, and the reason is the subject of
the next section. Between the two runs the path stopped being the channel the
first one measured: erasure fell to 4.3% and the burst factor rose to 2.0, so
loss was arriving in runs rather than independently, which is harder for any
code. Coding failed on 8.3% of losses before the change and 11.0% after, and
neither figure can be attributed to the change. What can be said is that in the
same window after it, against direct TCP:

| | direct TCP | queqiao |
|---|---|---|
| tokens over 200ms late | 22.14% | **18.19%** |
| tokens over 500ms late | 4.58% | **2.61%** |
| tokens over 1s late | 1.94% | **0.00%** |

queqiao now leads at every threshold, where before the change it lost the 500ms
bar. That is consistent with the fix and is not proof of it. A second path,
measured while this one is not moving, is what would settle it.


## A transfer beside a stream, and a measurement that failed

The fifth shape is a checkpoint pull happening while inference traffic runs, and
the question is whether the transfer costs the reader anything.

One part of it answered cleanly. A 90-second transfer that moved 1.35GB reached
the bulk class on this profile: `queqiao_class_transitions_total{class="2"}`
went from zero to one, and `queqiao_bulk_isolations_total` reached three. That
is the idle-veto change working end to end. A transfer offered in one burst does
not reach it, because 300MB went into the local buffer in 8.57s and this
profile's minimum age is ten seconds, which is deliberate: the age floor is what
stops a five-megabyte request being read as a transfer.

The other part did not answer. Ordered alone, then with the transfer, then alone
again:

| | tokens over 200ms late | over 500ms |
|---|---|---|
| alone | 8.47%, 16.28% | 1.78%, 2.12% |
| with a 1.35GB transfer underneath | 26.76%, 26.53% | 9.20%, 4.68% |
| alone again | **53.40%, 40.25%** | **14.60%, 8.92%** |

The last row is worse than the middle one. The stream got worse throughout,
whether or not a transfer was running, so the middle row is not evidence that
the transfer cost anything. An earlier attempt at the same comparison showed the
same pattern in the same direction.

We are recording it because the conclusion is about the instrument rather than
the transport: **on this path the drift over a few minutes is larger than the
effect being measured**, so this question cannot be answered here at all. Order
alternation handles a trend that reverses; it does not handle one that runs one
way for the length of the experiment.

Two things follow. Any mixed-workload result on this path needs the arms
interleaved at a much finer grain than one run each, or it needs a path that
holds still. And the emulator, not this link, is where a contention question
gets settled, for the same reason the benchmarking guide already gives: a
result is reproducible where the channel is controlled.

### The same question, where the channel holds still

`TestATransferBesideATokenStream` puts both flows through the real transport
across the emulated version of this path. The bottleneck is narrowed to 20
Mbit/s, because the measured knee of 333 Mbit/s is more than a userspace
transport on loopback can fill, and a transfer that never reaches the
bottleneck never competes for it. The test reports what the transfer actually
offered and skips itself if that was too little to matter.

| | p50 lateness | p90 | p99 | tokens |
|---|---|---|---|---|
| stream alone | -3.5ms | -1.6ms | 2.2ms | 199/199 |
| stream beside a transfer at 15.5 Mbit/s | -6.3ms | -1.3ms | 2.2ms | 199/199 |

A transfer taking 78% of the bottleneck cost the stream nothing measurable.
Every token arrived in both arms and the p99 moved by 54 microseconds on a
30ms cadence.

That is the answer the live path could not give, and it is worth being precise
about what it covers: the emulator reproduces this path's delay, erasure, burst
structure and knee, and it does not reproduce whatever was making the live link
drift for ten minutes at a time. A contention result is a statement about the
transport's scheduling, and the emulator is where that is a fair question.


## Re-measured with one fixed file

The figures above are medians across eight audio files of 146KB to 405KB,
labelled with the size of whichever request happened to run last. That is not a
labelling slip with no consequence: the median was pulled below the floor for
the size it was attributed to. A tuned client was recorded reaching 225.8ms on
what was described as a 355KB upload, and 355KB cannot be done in 225.8ms on
this path. One round trip is about 200ms and the model is about 30ms, so the
floor is roughly 230ms whatever the transport does.

Re-run with one fixed file, `dashboard.wav` at 354,640 bytes, arms alternating
within the run, contemporaneous round trip 197 to 205ms, after the pacing fix:

| 355KB ASR upload | direct | queqiao |
|---|---|---|
| new connection, p50 | 1185.3ms | **301.6ms** |
| held open and tuned, p50 | 240.9ms | **236.5ms** |
| held open and tuned, p99 | 251.7ms | **246.4ms** |

Paired per-round ratio: 3.96x on new connections, 1.03x warm.

The warm row is the one that took the work. A 197ms round trip and a 30ms model
put the floor around 227ms, and both arms are within ten milliseconds of it.
Before the pacing fix the transport sat 67ms above, all of it the pacer metering
a flow that had produced no evidence of congestion.

The synthesis side was re-measured in the same session and is unchanged by the
pacing work, which is what it should be: that direction erases about 14%, so the
send-side loss guard keeps the gateway metering there. The download leg is
827.7ms direct against 53.4ms through the transport, **15.5x** in the session
these figures come from and 13.9x in the one before, and the leg
containing the model agrees between the arms to 3%, which is the check that both
reached the same server doing the same work.

### Tuning the client makes the erasing direction worse

The sysctl advice is direction-specific, and we found out by accident. Measured
in one session, minutes apart, on the synthesis download:

| direct TCP, 100KB back | download leg |
|---|---|
| new connection | 827.7ms |
| held open, `tcp_slow_start_after_idle=0` | **2281.2ms** |

A second session put the same pair at 945.2ms and 6341.1ms. The direction is
consistent and the size of it is not.

Mathis explains both. At this path's 14% erasure and 200ms round trip the
predicted steady-state rate is 0.155 Mbit/s, which is 5.2 seconds for 100KB.
The warm figures bracket that; the cold ones beat it. A cold flow beats its own
steady state because it never reaches it: slow start is still ramping when the
transfer ends, so the window never gets large enough for a multiplicative
decrease to have much to take away. Warm it up and the flow starts where cubic's
sawtooth actually lives.

So the free client fix is free only on the clean direction. On a direction that
erases, restoring the congestion window hands the controller a larger window to
collapse from, and the transfer is slower than it would have been cold.

Two cautions about the tail figures. An earlier run of the same comparison, on a
minute when the path was dropping about 20% of pings, put direct at 834.3ms and
916.7ms at p90 and p99 against 274.6ms and 289.6ms; this run, with the path
clean, put both arms inside 252ms. The tail advantage is real and it is a
property of the path's condition rather than of the workload, so neither run
should be quoted as the tail behaviour. And the cold figures move by 200ms
between runs an hour apart, which is this link, not this transport.
