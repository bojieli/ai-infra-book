// Command pathprobe measures what a path does to an offered rate, which is a
// different question from what a transport achieves on it.
//
// Every transport measurement this project has taken confounds two things: the
// path's behaviour and the transport's reaction to it. A congestion controller
// that under-uses a link and a link that refuses the offered rate produce the
// same goodput number. Separating them needs an open-loop probe: send at a rate
// nobody is allowed to adjust, and count what arrives.
//
// Two questions it exists to answer, both about the real China-US path rather
// than an emulator:
//
//   - Given an offered rate, what fraction is delivered? Sweeping that finds
//     the knee, which is the path's rate limit for one 4-tuple.
//   - Does opening N connections between the same two endpoints deliver N times
//     as much? That is the entire premise of this project's multipath design.
//     If the answer is one, lanes cannot help and the design is wrong; if it is
//     N, the policing is per connection and lanes are the correct response.
//
// The probe is deliberately open-loop. It has no congestion control and must
// never be pointed at a path that is not yours.
package main

import (
	"encoding/binary"
	"errors"
	"flag"
	"fmt"
	"net"
	"os"
	"sync"
	"time"

	"github.com/bojieli/queqiao/internal/lossmodel"
	"github.com/bojieli/queqiao/internal/udperr"
)

const (
	magic        = 0x574f5052 // "WOPR"
	magicSummary = 0x574f5053 // the sender's own count, sent after the run
	// requestSize is the fixed control packet: magic, rate, duration, payload,
	// burst.
	requestSize = 4 + 8 + 8 + 4 + 4
	// headerSize prefixes every data packet with magic, stream and sequence,
	// so the receiver can attribute losses to a connection.
	headerSize = 4 + 4 + 8
)

type request struct {
	rateBytesPerSec uint64
	duration        time.Duration
	payload         int
	// burst bounds how many packets the sender may release back to back. It is
	// a property of the sender, not of the path, and it has to be controllable
	// because it contaminates exactly the statistic the loss pattern is read
	// for: a sender that releases 64 packets at once into a policer with a
	// small bucket produces a loss run of nearly 64, and that run is the
	// sender's rather than the path's.
	burst int
}

func (r request) encode() []byte {
	b := make([]byte, requestSize)
	binary.BigEndian.PutUint32(b[0:], magic)
	binary.BigEndian.PutUint64(b[4:], r.rateBytesPerSec)
	binary.BigEndian.PutUint64(b[12:], uint64(r.duration))
	binary.BigEndian.PutUint32(b[20:], uint32(r.payload))
	binary.BigEndian.PutUint32(b[24:], uint32(r.burst))
	return b
}

func decodeRequest(b []byte) (request, bool) {
	if len(b) < requestSize || binary.BigEndian.Uint32(b) != magic {
		return request{}, false
	}
	r := request{
		rateBytesPerSec: binary.BigEndian.Uint64(b[4:]),
		duration:        time.Duration(binary.BigEndian.Uint64(b[12:])),
		payload:         int(binary.BigEndian.Uint32(b[20:])),
		burst:           int(binary.BigEndian.Uint32(b[24:])),
	}
	if r.burst <= 0 || r.burst > 1024 {
		r.burst = defaultBurst
	}
	if r.payload < headerSize || r.payload > 1500 || r.duration <= 0 || r.duration > time.Minute {
		return request{}, false
	}
	if r.rateBytesPerSec == 0 || r.rateBytesPerSec > 4<<30 {
		return request{}, false
	}
	return r, true
}

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "pathprobe: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	fs := flag.NewFlagSet("pathprobe", flag.ContinueOnError)
	mode := fs.String("mode", "", "server or client")
	listen := fs.String("listen", ":12599", "server listen address")
	remote := fs.String("remote", "", "client: server address")
	rate := fs.Float64("rate", 10, "client: offered rate in Mbit/s per connection")
	streams := fs.Int("streams", 1, "client: number of independent connections, each its own 4-tuple")
	seconds := fs.Float64("duration", 5, "client: seconds to send for")
	payload := fs.Int("payload", 1200, "client: UDP payload size in bytes")
	sweep := fs.String("sweep", "", "client: comma-separated per-connection rates in Mbit/s to try in turn")
	burst := fs.Int("burst", defaultBurst, "client: bound the sender's back-to-back packet burst, which shapes the loss pattern independently of the path")
	pattern := fs.Bool("pattern", false, "client: also report the loss pattern, not only its rate")
	localAddr := fs.String("local-address", "", "client: bind the probe socket to this local IP, so a host TUN route does not carry the probe through a tunnel to the very server being measured")
	if err := fs.Parse(args); err != nil {
		return err
	}
	switch *mode {
	case "server":
		return serve(*listen)
	case "client":
		if *remote == "" {
			return errors.New("client needs --remote")
		}
		rates := []float64{*rate}
		if *sweep != "" {
			rates = nil
			for _, field := range splitCommas(*sweep) {
				var v float64
				if _, err := fmt.Sscanf(field, "%f", &v); err != nil || v <= 0 {
					return fmt.Errorf("bad rate in --sweep: %q", field)
				}
				rates = append(rates, v)
			}
		}
		analysePattern = *pattern
		return probe(*remote, rates, *streams, time.Duration(*seconds*float64(time.Second)), *payload, *burst, *localAddr)
	default:
		return errors.New("--mode must be server or client")
	}
}

// analysePattern turns on loss-structure reporting.
var analysePattern bool

// defaultBurst is the sender's back-to-back packet limit. It is large enough
// that the pacer is not the bottleneck at high rates, and small enough to stay
// under any plausible policer bucket.
const defaultBurst = 64

func splitCommas(s string) []string {
	var out []string
	start := 0
	for i := 0; i <= len(s); i++ {
		if i == len(s) || s[i] == ',' {
			if i > start {
				out = append(out, s[start:i])
			}
			start = i + 1
		}
	}
	return out
}

// serve answers each request by sending at the requested rate back to the
// address it came from, so the reply travels the same 4-tuple the request did.
// That is what makes N clients N connections as a policer sees them.
func serve(listen string) error {
	conn, err := net.ListenPacket("udp", listen)
	if err != nil {
		return err
	}
	defer conn.Close()
	fmt.Fprintf(os.Stderr, "pathprobe server on %s\n", conn.LocalAddr())
	buf := make([]byte, 2048)
	for {
		n, from, err := conn.ReadFrom(buf)
		if err != nil {
			// A blast to a client that has stopped listening draws an ICMP
			// port-unreachable, and the host reports it here on a later read
			// -- on Windows even for an unconnected socket. That describes one
			// datagram, so the server must not exit on it: this is the one
			// process whose whole job is sending to peers that may go away.
			if udperr.Transient(err) {
				continue
			}
			return err
		}
		req, ok := decodeRequest(buf[:n])
		if !ok {
			continue
		}
		go blast(conn, from, req)
	}
}

// blast paces packets at the requested rate with a token bucket, sending in
// bursts and sleeping only when it is ahead.
//
// Sleeping once per packet cannot work: Go's timer granularity is around a
// millisecond, so a per-packet sleep caps the sender near a thousand packets a
// second -- about 10 Mbit/s at this payload -- and every measurement above that
// would report the sender's limit as the path's. The first version of this
// probe did exactly that and reported 3 Mbit/s delivered against 80 offered
// with zero loss, which is the signature of a sender that never sent.
func blast(conn net.PacketConn, to net.Addr, req request) {
	packet := make([]byte, req.payload)
	binary.BigEndian.PutUint32(packet, magic)
	deadline := time.Now().Add(req.duration)
	start := time.Now()
	var seq, refused uint64
	defer func() {
		_ = conn.SetWriteDeadline(time.Time{})
		elapsed := time.Since(start)
		fmt.Fprintf(os.Stderr, "blast to=%v asked=%.1fMbit/s sent=%d refused=%d in %v => %.2f Mbit/s\n",
			to, float64(req.rateBytesPerSec)*8/1e6, seq, refused, elapsed.Round(time.Millisecond),
			float64(seq)*float64(req.payload)*8/elapsed.Seconds()/1e6)
		sendSummary(conn, to, seq)
	}()
	for {
		now := time.Now()
		if !now.Before(deadline) {
			return
		}
		// Tokens are whole packets earned since the start, so rounding cannot
		// accumulate into drift over a long run.
		earned := uint64(float64(req.rateBytesPerSec) * now.Sub(start).Seconds() / float64(req.payload))
		if earned <= seq {
			time.Sleep(200 * time.Microsecond)
			continue
		}
		// Bound one burst so a long sleep does not release a huge train at
		// once, which would measure the receiver's buffer rather than the path.
		burst := earned - seq
		if limit := uint64(req.burst); burst > limit {
			burst = limit
		}
		// A write that blocks makes this probe closed-loop: the socket's
		// backpressure becomes the rate, and the result reads as the path's
		// answer when it is the sender's. A short deadline turns that blocking
		// into a countable refusal instead.
		_ = conn.SetWriteDeadline(time.Now().Add(2 * time.Millisecond))
		for i := uint64(0); i < burst; i++ {
			binary.BigEndian.PutUint64(packet[8:], seq)
			if _, err := conn.WriteTo(packet, to); err != nil {
				// A UDP send can fail transiently -- ENOBUFS when the qdisc is
				// full is the usual one -- and returning here ends the run.
				// The first version did, which made every high offered rate
				// report a low sent count and zero loss: the signature of a
				// probe that stopped, read as a path that was slow.
				refused++
				break
			}
			seq++
		}
	}
}

// summary tells the receiver how many packets the sender actually put on the
// wire. Without it the receiver can only infer that from the highest sequence
// it saw, which cannot tell a sender that never sent from a path that dropped
// everything after a point -- and those have opposite meanings.
func sendSummary(conn net.PacketConn, to net.Addr, sent uint64) {
	b := make([]byte, headerSize+8)
	binary.BigEndian.PutUint32(b, magicSummary)
	binary.BigEndian.PutUint64(b[headerSize:], sent)
	for i := 0; i < 5; i++ {
		if _, err := conn.WriteTo(b, to); err != nil {
			return
		}
		time.Sleep(20 * time.Millisecond)
	}
}

type result struct {
	stream    int
	packets   uint64
	bytes     uint64
	firstSeen time.Time
	lastSeen  time.Time
	highest   uint64
	// sent is what the sender reported putting on the wire.
	sent uint64
	// seen records which sequence numbers arrived, so the loss pattern can be
	// characterised rather than only its rate. A rate alone cannot choose a
	// recovery strategy: independent loss is cheap to repair with a little
	// forward error correction, and bursty loss of the same average rate needs
	// interleaving deep enough to span a burst or it repairs nothing.
	seen map[uint64]bool
}

func probe(remote string, rates []float64, streams int, duration time.Duration, payload, burst int, localAddr string) error {
	fmt.Printf("# offered rate is per connection; %d connection(s), %v, %d-byte payloads\n",
		streams, duration, payload)
	fmt.Printf("offered_each\toffered_total\tsent_total\tdelivered_total\tdelivered_each\tloss_pct\tdeliv/sent\n")
	for _, mbits := range rates {
		perConn := uint64(mbits * 1e6 / 8)
		results := make([]result, streams)
		var wg sync.WaitGroup
		for i := 0; i < streams; i++ {
			wg.Add(1)
			go func(i int) {
				defer wg.Done()
				r, err := probeOne(remote, request{rateBytesPerSec: perConn, duration: duration, payload: payload, burst: burst}, localAddr)
				if err != nil {
					fmt.Fprintf(os.Stderr, "stream %d: %v\n", i, err)
					return
				}
				r.stream = i
				results[i] = r
			}(i)
		}
		wg.Wait()

		var totalBytes, totalPackets, highest, totalSent uint64
		missingSummary := 0
		for _, r := range results {
			totalBytes += r.bytes
			totalPackets += r.packets
			highest += r.highest
			if r.sent > 0 {
				totalSent += r.sent
			} else {
				// No summary arrived. Fall back to the highest sequence seen,
				// and say so: without this the fallback makes sent equal
				// delivered and loss identically zero, which reads like a
				// clean measurement and is the absence of one.
				totalSent += r.highest
				missingSummary++
			}
		}
		deliveredTotal := float64(totalBytes) * 8 / duration.Seconds() / 1e6
		// sent is what the sender actually put on the wire, taken from the
		// highest sequence number seen. Reporting it separately from the
		// offered rate is what keeps a slow sender from being read as a slow
		// path.
		sentTotal := float64(totalSent) * float64(payload) * 8 / duration.Seconds() / 1e6
		offeredTotal := mbits * float64(streams)
		loss := 0.0
		if totalSent > 0 {
			loss = 100 * (1 - float64(totalPackets)/float64(totalSent))
		}
		ratio := 0.0
		if sentTotal > 0 {
			ratio = deliveredTotal / sentTotal
		}
		if analysePattern {
			for _, r := range results {
				if r.sent == 0 || r.seen == nil {
					continue
				}
				arrived := make([]bool, r.sent)
				for seq := range r.seen {
					if seq < r.sent {
						arrived[seq] = true
					}
				}
				p := lossmodel.Analyze(arrived)
				fmt.Printf("#   stream %d: loss=%.1f%% P(loss|prev ok)=%.3f P(ok|prev lost)=%.3f "+
					"mean_burst=%.2f burst_factor=%.2f longest_burst=%d\n",
					r.stream, 100*p.Loss, p.LossAfterArrival, p.ArrivalAfterLoss,
					p.MeanBurst, p.BurstFactor, p.LongestBurst)
				fmt.Printf("#   stream %d: burst length histogram", r.stream)
				for _, l := range []int{1, 2, 3, 4, 5, 10, 20, 50} {
					fmt.Printf("  %d:%d", l, p.Bursts[l])
				}
				fmt.Println()
			}
		}
		note := ""
		if missingSummary > 0 {
			note = fmt.Sprintf("\t(no sender report from %d/%d streams)", missingSummary, streams)
		}
		fmt.Printf("%.1f\t%.1f\t%.2f\t%.2f\t%.2f\t%.1f\t%.2f%s\n",
			mbits, offeredTotal, sentTotal, deliveredTotal, deliveredTotal/float64(streams), loss, ratio, note)
	}
	return nil
}

func probeOne(remote string, req request, localAddr string) (result, error) {
	addr, err := net.ResolveUDPAddr("udp", remote)
	if err != nil {
		return result{}, err
	}
	var local *net.UDPAddr
	if localAddr != "" {
		local, err = net.ResolveUDPAddr("udp", net.JoinHostPort(localAddr, "0"))
		if err != nil {
			return result{}, err
		}
	}
	conn, err := net.DialUDP("udp", local, addr)
	if err != nil {
		return result{}, err
	}
	defer conn.Close()
	if _, err := conn.Write(req.encode()); err != nil {
		return result{}, err
	}
	// Read past the end of the send window so packets still in flight arrive.
	_ = conn.SetReadDeadline(time.Now().Add(req.duration + 3*time.Second))
	buf := make([]byte, 2048)
	var r result
	for {
		n, err := conn.Read(buf)
		if err != nil {
			break
		}
		if n >= headerSize+8 && binary.BigEndian.Uint32(buf) == magicSummary {
			r.sent = binary.BigEndian.Uint64(buf[headerSize:])
			continue
		}
		if n < headerSize || binary.BigEndian.Uint32(buf) != magic {
			continue
		}
		seq := binary.BigEndian.Uint64(buf[8:])
		if seq+1 > r.highest {
			r.highest = seq + 1
		}
		if r.seen == nil {
			r.seen = make(map[uint64]bool)
		}
		r.seen[seq] = true
		r.packets++
		r.bytes += uint64(n)
		now := time.Now()
		if r.firstSeen.IsZero() {
			r.firstSeen = now
		}
		r.lastSeen = now
	}
	return r, nil
}
