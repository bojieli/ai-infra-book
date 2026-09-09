package main

import (
	"crypto/rand"
	"fmt"
	"io"
	"math/big"
	"net/http"
	"strings"
	"time"
)

// A token stream is the workload none of the other modes describes.
//
// A request is one burst and a bulk transfer is one long one. A language model
// answering is neither: a short prompt goes up, and then the answer comes back
// a few dozen bytes at a time, for as long as the answer takes. What the user
// experiences is not the total, which they never wait for in one piece, but
// the time until the first token and whether the ones after it keep arriving.
//
// That shape is the hardest case for a path that erases. Every other workload
// has traffic behind it: lose a packet in the middle of a transfer and the
// packets that follow expose the loss within a round trip. A token has nothing
// behind it for another thirty milliseconds, so a loss is discovered by
// timeout, and one timeout on a two-hundred-millisecond path is ten tokens the
// reader is waiting on. Measuring the total would hide it entirely, because
// the total is dominated by how fast the model generates.
//
// So this mode reports the gaps between arrivals rather than their sum, and
// counts stalls against fixed wall-clock thresholds rather than against each
// arm's own median. A relative threshold gives the faster arm more room under
// its own bar and reports fewer stalls for that reason alone, which is a
// mistake this project has already made once.

// streamThresholds are the gaps that matter to somebody reading the output, in
// milliseconds. They are absolute on purpose.
var streamThresholds = []float64{200, 500, 1000}

// streamResult is one consumed stream.
type streamResult struct {
	ttft   time.Duration
	gaps   []float64
	excess []float64
	tokens int
	reads  int
	bytes  int64
	total  time.Duration
	status int
	err    error
}

// consumeStream issues the request and timestamps every token, not every read.
//
// Those are not the same thing, and the difference is the whole measurement. At
// a thirty-millisecond cadence over a two-hundred-millisecond path several
// tokens are in flight at once, and the kernel hands them over in whatever
// grouping the segments happened to take: measured on the live path, one arm
// saw 907 reads deliver what the other saw as 1536, for the same 2400 tokens.
// Counting reads would have compared two groupings and called the difference
// latency.
//
// Tokens delivered in one read arrived at the same instant, which is the truth
// about when a reader could see them, so each event is stamped with the read
// that completed it.
func consumeStream(cl *http.Client, w *workloadRequest, expect time.Duration) streamResult {
	var r streamResult
	req, err := newWorkloadHTTPRequest(w)
	if err != nil {
		r.err = err
		return r
	}
	start := time.Now()
	resp, err := cl.Do(req)
	if err != nil {
		r.err = err
		r.total = time.Since(start)
		return r
	}
	defer func() { _ = resp.Body.Close() }()
	r.status = resp.StatusCode
	if resp.StatusCode != http.StatusOK {
		_, _ = io.Copy(io.Discard, resp.Body)
		r.total = time.Since(start)
		return r
	}

	var (
		buf     = make([]byte, 8192)
		pending string
		firstAt time.Time
		lastAt  time.Time
	)
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			now := time.Now()
			r.reads++
			r.bytes += int64(n)
			pending += string(buf[:n])
			for {
				idx := strings.Index(pending, "\n\n")
				if idx < 0 {
					break
				}
				event := pending[:idx]
				pending = pending[idx+2:]
				if !strings.Contains(event, "data:") || strings.Contains(event, "[DONE]") {
					continue
				}
				if r.tokens == 0 {
					firstAt = now
					r.ttft = now.Sub(start)
				} else {
					r.gaps = append(r.gaps, float64(now.Sub(lastAt))/float64(time.Millisecond))
					if expect > 0 {
						// How far behind the generator's own schedule this
						// token is, measured from the first one so the path's
						// fixed delay cancels. A stall shows as a jump, and a
						// catch-up burst brings it back down, which is what a
						// reader actually experiences.
						want := time.Duration(r.tokens) * expect
						r.excess = append(r.excess,
							float64(now.Sub(firstAt)-want)/float64(time.Millisecond))
					}
				}
				lastAt = now
				r.tokens++
			}
		}
		if err != nil {
			if err != io.EOF {
				r.err = err
			}
			break
		}
	}
	r.total = time.Since(start)
	return r
}

// streamArm accumulates one arm's streams.
type streamArm struct {
	name string
	cl   *http.Client

	ttft   []float64
	gaps   []float64
	excess []float64
	totals []float64
	late   map[float64]int
	behind map[float64]int
	tokens int
	reads  int
	failed int
}

func newStreamArm(name, proxy, localAddr string, reuse bool) *streamArm {
	return &streamArm{
		name:   name,
		cl:     newWorkloadClient(proxy, localAddr, reuse),
		late:   map[float64]int{},
		behind: map[float64]int{},
	}
}

func (a *streamArm) record(r streamResult) {
	if r.err != nil || r.status != http.StatusOK || r.tokens == 0 {
		a.failed++
		return
	}
	a.ttft = append(a.ttft, float64(r.ttft)/float64(time.Millisecond))
	a.totals = append(a.totals, float64(r.total)/float64(time.Millisecond))
	a.gaps = append(a.gaps, r.gaps...)
	a.excess = append(a.excess, r.excess...)
	a.tokens += r.tokens
	a.reads += r.reads
	for _, t := range streamThresholds {
		for _, g := range r.gaps {
			if g > t {
				a.late[t]++
			}
		}
		for _, e := range r.excess {
			if e > t {
				a.behind[t]++
			}
		}
	}
}

// streamMode alternates arms every round, the same discipline the workload
// mode uses and for the same reason.
func streamMode(url, aSpec, bSpec string, rounds int, reuse bool, localAddr string, w *workloadRequest, spacing, expect time.Duration) error {
	aProxy, err := parseArm(aSpec)
	if err != nil {
		return fmt.Errorf("--a: %w", err)
	}
	bProxy, err := parseArm(bSpec)
	if err != nil {
		return fmt.Errorf("--b: %w", err)
	}
	w.url = url

	a := newStreamArm(aSpec, aProxy, localAddr, reuse)
	b := newStreamArm(bSpec, bProxy, localAddr, reuse)

	for i := range rounds {
		order := []*streamArm{a, b}
		if i%2 == 1 {
			order = []*streamArm{b, a}
		}
		for _, arm := range order {
			r := consumeStream(arm.cl, w, expect)
			arm.record(r)
			if r.err != nil {
				fmt.Printf("# round %d %s: %v\n", i, arm.name, r.err)
			} else if r.status != http.StatusOK {
				fmt.Printf("# round %d %s: HTTP %d\n", i, arm.name, r.status)
			}
			jitter, _ := rand.Int(rand.Reader, big.NewInt(int64(spacing/3)+1))
			time.Sleep(spacing + time.Duration(jitter.Int64()))
		}
	}

	fmt.Printf("# %s  rounds=%d reuse=%v expect=%s\n", url, rounds, reuse, expect)
	fmt.Printf("arm\tstreams\ttokens\treads\tttft50\tttft99\tgap50\tgap99\tgapmax\tlate200\tlate500\tlate1s\tfail\n")
	for _, arm := range []*streamArm{a, b} {
		fmt.Printf("%s\t%d\t%d\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%d\t%d\t%d\t%d\n",
			arm.name, len(arm.ttft), arm.tokens, arm.reads,
			pctOf(arm.ttft, 50), pctOf(arm.ttft, 99),
			pctOf(arm.gaps, 50), pctOf(arm.gaps, 99), pctOf(arm.gaps, 100),
			arm.late[200], arm.late[500], arm.late[1000], arm.failed)
	}
	if len(a.gaps) == 0 || len(b.gaps) == 0 {
		fmt.Printf("# one arm produced no stream; nothing to compare\n")
		return nil
	}
	if a.tokens != b.tokens {
		fmt.Printf("# NOTE: arms saw %d and %d tokens. Rates below are per token, but a\n", a.tokens, b.tokens)
		fmt.Printf("# difference this large means one arm lost or truncated a stream.\n")
	}
	fmt.Printf("# %s/%s: ttft50=%.2fx\n", a.name, b.name,
		pctOf(a.ttft, 50)/nonZero(pctOf(b.ttft, 50)))

	if expect > 0 {
		// Lateness against the generator's own schedule is the figure that
		// says whether a reader saw the stream stutter. Inter-token gaps
		// cannot: a stall followed by a catch-up burst produces one long gap
		// and a run of zero-length ones, and the median of that looks healthy.
		fmt.Printf("arm\tbehind50\tbehind90\tbehind99\tbehindmax\tover200\tover500\tover1s\n")
		for _, arm := range []*streamArm{a, b} {
			fmt.Printf("%s\t%.1f\t%.1f\t%.1f\t%.1f\t%d\t%d\t%d\n",
				arm.name,
				pctOf(arm.excess, 50), pctOf(arm.excess, 90),
				pctOf(arm.excess, 99), pctOf(arm.excess, 100),
				arm.behind[200], arm.behind[500], arm.behind[1000])
		}
		for _, t := range streamThresholds {
			fmt.Printf("# tokens over %.0fms behind schedule: %s %.2f%% (%d/%d), %s %.2f%% (%d/%d)\n", t,
				a.name, 100*float64(a.behind[t])/float64(max(len(a.excess), 1)), a.behind[t], len(a.excess),
				b.name, 100*float64(b.behind[t])/float64(max(len(b.excess), 1)), b.behind[t], len(b.excess))
		}
	}
	for _, t := range streamThresholds {
		fmt.Printf("# gaps over %.0fms: %s %.2f%% (%d/%d), %s %.2f%% (%d/%d)\n", t,
			a.name, 100*float64(a.late[t])/float64(max(len(a.gaps), 1)), a.late[t], len(a.gaps),
			b.name, 100*float64(b.late[t])/float64(max(len(b.gaps), 1)), b.late[t], len(b.gaps))
	}
	return nil
}

// streamServe emits tokens at a fixed cadence, so the generator is not a
// variable in the comparison.
//
// A real model is the authentic thing to measure and a poor instrument: its
// cadence depends on batch occupancy, so two arms measured minutes apart saw
// different generators. This one produces the same stream every time, which is
// what isolates the path.
func streamServe(listen string, tokens int, interval time.Duration, tokenBytes int) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		_, _ = io.Copy(io.Discard, r.Body)
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "streaming unsupported", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.WriteHeader(http.StatusOK)
		flusher.Flush()
		payload := strings.Repeat("x", tokenBytes)
		tick := time.NewTicker(interval)
		defer tick.Stop()
		for i := range tokens {
			select {
			case <-r.Context().Done():
				return
			case <-tick.C:
			}
			if _, err := fmt.Fprintf(w, "data: {\"i\":%d,\"t\":\"%s\"}\n\n", i, payload); err != nil {
				return
			}
			flusher.Flush()
		}
		_, _ = io.WriteString(w, "data: [DONE]\n\n")
		flusher.Flush()
	})
	srv := &http.Server{Addr: listen, Handler: mux, ReadHeaderTimeout: 30 * time.Second}
	fmt.Printf("# streamserve on %s: %d tokens of %dB every %s\n", listen, tokens, tokenBytes, interval)
	return srv.ListenAndServe()
}
