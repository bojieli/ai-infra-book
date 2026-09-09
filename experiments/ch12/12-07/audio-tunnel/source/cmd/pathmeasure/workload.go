package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"fmt"
	"io"
	"math/big"
	"mime/multipart"
	"net"
	"net/http"
	"net/http/httptrace"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// The workload mode exists because every other mode in this command moves
// bytes of its own choosing, and a transport that wins on a 300KB transfer has
// not yet been shown to win on a 300KB request to something that answers.
//
// The difference is not decoration. A speech recognition call uploads a few
// hundred kilobytes and gets a sentence back; a synthesis call sends a
// sentence and gets a few hundred kilobytes back. Those load opposite
// directions of a path whose two directions, on the link this profile was
// built for, behave nothing alike. Measuring one and assuming the other is how
// the first version of this work reached a conclusion it had to retract.
//
// It also keeps the model honest. A synthesis request spends seconds inside a
// GPU, and a transport improves none of it. Reporting only end-to-end latency
// on such a workload buries whatever the transport did under a constant it
// does not control, so this mode reports the legs separately and checks that
// the leg containing the model agrees between arms.

// httpArm is one side of a workload comparison: a name, the proxy it dials
// through, and the samples it produced.
type httpArm struct {
	name  string
	proxy string
	cl    *http.Client

	total    []float64
	connect  []float64
	sendRecv []float64
	download []float64
	failed   int
	lastIn   int64
	lastOut  int64
}

const (
	// serverLegSkew is how far the server leg may differ between arms before
	// the comparison is reported as void.
	serverLegSkew = 0.15
	// serverLegFloorMS is the shortest server leg the skew check applies to.
	serverLegFloorMS = 50
	// smallRequestBytes is the largest request body for which the send is a
	// negligible part of the leg, so that the leg is round trip plus server.
	smallRequestBytes = 32 << 10
)

// legs is where one request's time went.
type legs struct {
	connect  time.Duration
	sendRecv time.Duration
	download time.Duration
	total    time.Duration
	in, out  int64
	status   int
	err      error
}

// workloadRequest describes the request to repeat. It is deliberately generic
// HTTP rather than any vendor's audio API: the shapes that matter here are
// "large body up, small body down" and its reverse, and pinning this to one
// provider's routes would make it useless for the next path we measure.
type workloadRequest struct {
	url         string
	body        []byte
	contentType string
	headers     []string
	fileName    string
}

// buildBody assembles the request body once, so that per-round timing does not
// include reading a file off disk.
func buildBody(postFile, formField, contentType string, formValues []string) (*workloadRequest, error) {
	w := &workloadRequest{contentType: contentType}
	if postFile == "" {
		return w, nil
	}
	data, err := os.ReadFile(postFile)
	if err != nil {
		return nil, err
	}
	w.fileName = filepath.Base(postFile)
	if formField == "" {
		w.body = data
		return w, nil
	}
	var buf bytes.Buffer
	mw := multipart.NewWriter(&buf)
	fw, err := mw.CreateFormFile(formField, w.fileName)
	if err != nil {
		return nil, err
	}
	if _, err := fw.Write(data); err != nil {
		return nil, err
	}
	for _, kv := range formValues {
		k, v, ok := strings.Cut(kv, "=")
		if !ok {
			return nil, fmt.Errorf("form value %q wants key=value", kv)
		}
		if err := mw.WriteField(k, v); err != nil {
			return nil, err
		}
	}
	if err := mw.Close(); err != nil {
		return nil, err
	}
	w.body = buf.Bytes()
	w.contentType = mw.FormDataContentType()
	return w, nil
}

// newWorkloadHTTPRequest builds the request this workload repeats. The body is
// assembled once and re-read from memory each round, so per-round timing never
// includes reading a file off disk.
func newWorkloadHTTPRequest(w *workloadRequest) (*http.Request, error) {
	method := http.MethodPost
	if len(w.body) == 0 {
		method = http.MethodGet
	}
	req, err := http.NewRequest(method, w.url, bytes.NewReader(w.body))
	if err != nil {
		return nil, err
	}
	if w.contentType != "" {
		req.Header.Set("Content-Type", w.contentType)
	}
	for _, h := range w.headers {
		k, v, ok := strings.Cut(h, ":")
		if !ok {
			continue
		}
		req.Header.Set(strings.TrimSpace(k), strings.TrimSpace(v))
	}
	req.ContentLength = int64(len(w.body))
	return req, nil
}

// newWorkloadClient builds a client that dials through this arm's proxy using
// the same dialer every other mode uses, so a tunnel and the path beneath it
// are measured by one instrument.
func newWorkloadClient(proxy, localAddr string, reuse bool) *http.Client {
	tr := &http.Transport{
		DisableKeepAlives:     !reuse,
		MaxIdleConnsPerHost:   4,
		IdleConnTimeout:       10 * time.Minute,
		ResponseHeaderTimeout: 5 * time.Minute,
		DialContext: func(_ context.Context, _, addr string) (net.Conn, error) {
			saved := proxyAddr
			proxyAddr = proxy
			defer func() { proxyAddr = saved }()
			return dialVia(addr, localAddr)
		},
	}
	return &http.Client{Transport: tr, Timeout: 10 * time.Minute}
}

// timeOne issues the request and records where the time went.
//
// Note which figures are comparable across arms and which are not. Through a
// SOCKS5 proxy the client's write completes into a loopback buffer, so
// WroteRequest fires while the bytes have gone nowhere: we measured 0.4ms of
// "upload" for a 355KB file. The real send time reappears as time waiting for
// the first response byte. Only the two together mean anything, so only the
// two together are reported.
func timeOne(cl *http.Client, w *workloadRequest) legs {
	var l legs
	l.out = int64(len(w.body))

	req, err := newWorkloadHTTPRequest(w)
	if err != nil {
		l.err = err
		return l
	}

	var start, conn, first time.Time
	start = time.Now()
	trace := &httptrace.ClientTrace{
		GotConn:              func(httptrace.GotConnInfo) { conn = time.Now() },
		GotFirstResponseByte: func() { first = time.Now() },
	}
	req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))

	resp, err := cl.Do(req)
	if err != nil {
		l.err = err
		l.total = time.Since(start)
		return l
	}
	n, copyErr := io.Copy(io.Discard, resp.Body)
	_ = resp.Body.Close()
	done := time.Now()

	l.status = resp.StatusCode
	l.in = n
	l.total = done.Sub(start)
	if !conn.IsZero() {
		l.connect = conn.Sub(start)
	}
	if !first.IsZero() && !conn.IsZero() {
		l.sendRecv = first.Sub(conn)
	}
	if !first.IsZero() {
		l.download = done.Sub(first)
	}
	if copyErr != nil {
		l.err = copyErr
	}
	return l
}

func (a *httpArm) record(l legs) {
	if l.err != nil || l.status != http.StatusOK {
		a.failed++
		return
	}
	ms := func(d time.Duration) float64 { return float64(d) / float64(time.Millisecond) }
	a.total = append(a.total, ms(l.total))
	a.connect = append(a.connect, ms(l.connect))
	a.sendRecv = append(a.sendRecv, ms(l.sendRecv))
	a.download = append(a.download, ms(l.download))
	a.lastIn, a.lastOut = l.in, l.out
}

// workloadMode alternates the arms every round so that a path drifting during
// the run cannot be read as a property of whichever arm went first, and pairs
// each round against itself so the comparison survives a path that moves.
func workloadMode(url, aSpec, bSpec string, rounds int, reuse bool, localAddr string, w *workloadRequest, spacing time.Duration) error {
	aProxy, err := parseArm(aSpec)
	if err != nil {
		return fmt.Errorf("--a: %w", err)
	}
	bProxy, err := parseArm(bSpec)
	if err != nil {
		return fmt.Errorf("--b: %w", err)
	}
	w.url = url

	a := &httpArm{name: aSpec, proxy: aProxy, cl: newWorkloadClient(aProxy, localAddr, reuse)}
	b := &httpArm{name: bSpec, proxy: bProxy, cl: newWorkloadClient(bProxy, localAddr, reuse)}

	for i := range rounds {
		order := []*httpArm{a, b}
		if i%2 == 1 {
			order = []*httpArm{b, a}
		}
		for _, arm := range order {
			l := timeOne(arm.cl, w)
			arm.record(l)
			if l.err != nil {
				fmt.Printf("# round %d %s: %v\n", i, arm.name, l.err)
			} else if l.status != http.StatusOK {
				fmt.Printf("# round %d %s: HTTP %d\n", i, arm.name, l.status)
			}
			// Space the arms apart so neither inherits the other's queue at
			// the far end, with a little jitter so the spacing itself cannot
			// land in step with something periodic on the path.
			jitter, _ := rand.Int(rand.Reader, big.NewInt(int64(spacing/3)+1))
			time.Sleep(spacing + time.Duration(jitter.Int64()))
		}
	}

	fmt.Printf("# %s  rounds=%d  reuse=%v  sent=%dB received=%dB\n",
		url, rounds, reuse, a.lastOut, a.lastIn)
	fmt.Printf("arm\tok\ttotal50\ttotal90\ttotal99\tconnect\treq->1stB\tdownload\tfail\n")
	for _, arm := range []*httpArm{a, b} {
		fmt.Printf("%s\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%d\n",
			arm.name, len(arm.total),
			pctOf(arm.total, 50), pctOf(arm.total, 90), pctOf(arm.total, 99),
			pctOf(arm.connect, 50), pctOf(arm.sendRecv, 50), pctOf(arm.download, 50),
			arm.failed)
	}
	if len(a.total) == 0 || len(b.total) == 0 {
		fmt.Printf("# one arm produced no samples; nothing to compare\n")
		return nil
	}

	fmt.Printf("# %s/%s at p50: total=%.2fx req->1stB=%.2fx download=%.2fx\n",
		a.name, b.name,
		pctOf(a.total, 50)/nonZero(pctOf(b.total, 50)),
		pctOf(a.sendRecv, 50)/nonZero(pctOf(b.sendRecv, 50)),
		pctOf(a.download, 50)/nonZero(pctOf(b.download, 50)))

	var ratios []float64
	n := min(len(a.total), len(b.total))
	for i := range n {
		if b.total[i] > 0 {
			ratios = append(ratios, a.total[i]/b.total[i])
		}
	}
	fmt.Printf("# paired per-round ratio: median=%.2fx p10=%.2fx p90=%.2fx n=%d\n",
		pctOf(ratios, 50), pctOf(ratios, 10), pctOf(ratios, 90), len(ratios))

	reportServerLeg(a, b, int64(len(w.body)))
	return nil
}

// reportServerLeg checks the one leg that should not differ between arms.
//
// Request-to-first-byte is the send, one round trip, and whatever the server
// does. On a download-shaped request the send is a few hundred bytes, so the
// leg is round trip plus server, and the server is the same server: the arms
// have to agree, and if they don't, something other than the transport differs
// and the comparison is void. That check caught nothing on our runs, which is
// the point of running it.
//
// On an upload-shaped request the send is most of the leg, and through a proxy
// it is the only place the send time can appear at all, so the arms are
// supposed to differ and the check would fire on every correct result. Saying
// which case applies is more useful than a warning the reader learns to ignore.
func reportServerLeg(a, b *httpArm, requestBytes int64) {
	sa, sb := pctOf(a.sendRecv, 50), pctOf(b.sendRecv, 50)
	if requestBytes > smallRequestBytes {
		fmt.Printf("# request is %dB, so the send dominates req->1stB and the arms are expected\n", requestBytes)
		fmt.Printf("# to differ there. The server-leg equality check does not apply to this shape.\n")
		return
	}
	// Below a few tens of milliseconds the ratio is measuring scheduler noise
	// rather than a difference between arms, so the check only applies where
	// the leg is long enough for a percentage of it to mean something.
	if max(sa, sb) < serverLegFloorMS {
		return
	}
	skew := absDiff(sa, sb) / nonZero(max(sa, sb))
	if skew <= serverLegSkew {
		fmt.Printf("# server leg agrees between arms (%.1fms vs %.1fms, %.0f%% apart), which is the\n", sa, sb, skew*100)
		fmt.Printf("# check that both arms reached the same server doing the same work.\n")
		return
	}
	fmt.Printf("# WARNING: the server leg differs by %.0f%% between arms (%.1fms vs %.1fms).\n", skew*100, sa, sb)
	fmt.Printf("# On this request shape that leg is a round trip plus the server, and the server\n")
	fmt.Printf("# is the same one. Something other than the transport differs; the comparison\n")
	fmt.Printf("# below is not measuring what it claims to.\n")
}

func pctOf(v []float64, p float64) float64 {
	if len(v) == 0 {
		return 0
	}
	s := append([]float64(nil), v...)
	sort.Float64s(s)
	i := int(p / 100 * float64(len(s)-1))
	return s[i]
}

func nonZero(f float64) float64 {
	if f <= 0 {
		return 0.01
	}
	return f
}

// repeatedValue collects a flag given more than once, in the order it was
// given.
type repeatedValue []string

func (r *repeatedValue) String() string { return strings.Join(*r, ",") }

func (r *repeatedValue) Set(v string) error {
	*r = append(*r, v)
	return nil
}
