// Package tcpinfo reads the kernel's own account of what a TCP connection is
// doing, which is the only place several of the answers exist.
//
// A transport measurement taken from userspace sees goodput and nothing else.
// Goodput is the product of every constraint at once, so a connection limited
// by its congestion window, one limited by the receiver's advertised window,
// one limited by its pacing rate and one whose application simply had nothing
// to send all look identical from above. They need different fixes, and three
// of the four are invisible without asking the kernel.
//
// TCP_INFO answers all four. tcpi_snd_cwnd and tcpi_snd_ssthresh describe the
// congestion window; tcpi_rwnd_limited and tcpi_sndbuf_limited count the
// microseconds spent blocked on the receiver and on the socket buffer;
// tcpi_pacing_rate is what the sender is allowed to release; and
// tcpi_delivery_rate_app_limited says whether the delivery rate beneath it is
// evidence about the path at all. That last bit is the one this project needed
// most: a sender that never filled its window has learned nothing about what
// the path could have carried, and a rate estimate built from such samples
// describes the application rather than the link.
//
// The struct is read as raw bytes rather than through a typed binding because
// the kernel has appended fields to it for a decade and intends to continue.
// A binding compiled against one layout silently misreads a longer one; a
// length-checked offset table reads what is present and reports the rest as
// absent, which is the honest answer on an older kernel.
package tcpinfo

import "encoding/binary"

// Info is the subset of struct tcp_info this project has a use for. Fields the
// running kernel did not supply are left zero and reported by Truncated.
type Info struct {
	// State is the TCP state machine value; 1 is ESTABLISHED.
	State uint8
	// CAState is the congestion-avoidance state: 0 open, 1 disorder,
	// 2 CWR, 3 recovery, 4 loss.
	CAState uint8
	// AppLimited is the kernel's judgement that DeliveryRate below was
	// measured while the application had nothing more to send. Such a sample
	// is not evidence about the path's capacity and must not be allowed to
	// raise a bandwidth estimate, nor to lower one that was measured properly.
	AppLimited bool

	SndMSS      uint32
	RTT         uint32 // microseconds, smoothed
	RTTVar      uint32 // microseconds
	MinRTT      uint32 // microseconds, minimum seen on this connection
	SndCwnd     uint32 // packets
	SndSsthresh uint32
	// Unacked is packets in flight. Multiplied by SndMSS it is the closest
	// thing TCP_INFO offers to bytes in flight.
	Unacked      uint32
	Lost         uint32
	Retrans      uint32
	TotalRetrans uint32
	// NotsentBytes is data queued in the socket that the sender has chosen not
	// to release yet. A large value with a small cwnd means the window binds;
	// a zero value means the application is the constraint.
	NotsentBytes uint32
	SndWnd       uint32 // peer's advertised receive window, bytes

	PacingRate    uint64 // bytes/sec, 0 when unset
	MaxPacingRate uint64
	BytesAcked    uint64
	BytesSent     uint64
	BytesRetrans  uint64
	// DeliveryRate is the kernel's own delivery-rate sample in bytes/sec. It
	// is only evidence about the path when AppLimited is false.
	DeliveryRate uint64
	// BusyTime, RwndLimited and SndbufLimited are cumulative microseconds and
	// are the direct answer to "what was this connection waiting on". Their
	// ratio over an interval attributes the interval to a cause.
	BusyTime      uint64
	RwndLimited   uint64
	SndbufLimited uint64

	Delivered uint32

	// Truncated is the number of bytes the kernel returned. A short buffer
	// means an older kernel and some fields above are absent rather than zero.
	Truncated int
}

// Offsets into struct tcp_info as laid out by Linux on a little-endian
// 64-bit architecture. The struct has only ever grown at the end, so an offset
// that fits inside the returned length is the field the kernel meant.
const (
	offState        = 0
	offCAState      = 1
	offAppLimited   = 7
	offSndMSS       = 16
	offUnacked      = 24
	offLost         = 32
	offRetrans      = 36
	offRTT          = 68
	offRTTVar       = 72
	offSndSsthresh  = 76
	offSndCwnd      = 80
	offTotalRetrans = 100
	offPacingRate   = 104
	offMaxPacing    = 112
	offBytesAcked   = 120
	offSegsOut      = 136
	offNotsent      = 144
	offMinRTT       = 148
	offDeliveryRate = 160
	offBusyTime     = 168
	offRwndLimited  = 176
	offSndbufLimit  = 184
	offDelivered    = 192
	offBytesSent    = 200
	offBytesRetrans = 208
	offSndWnd       = 228
	// wantLen is the length of the struct this package knows how to read in
	// full. A kernel returning less is older, not broken.
	wantLen = 232
)

func u32(b []byte, off int) uint32 {
	if off+4 > len(b) {
		return 0
	}
	return binary.LittleEndian.Uint32(b[off:])
}

func u64(b []byte, off int) uint64 {
	if off+8 > len(b) {
		return 0
	}
	return binary.LittleEndian.Uint64(b[off:])
}

// Parse reads the raw TCP_INFO bytes a getsockopt returned. It never fails:
// a buffer shorter than a field leaves that field zero and records the length,
// because the alternative -- refusing to report anything because one trailing
// counter is missing -- discards the fields that are present and were the
// reason for asking.
func Parse(b []byte) Info {
	var i Info
	i.Truncated = len(b)
	if len(b) > offState {
		i.State = b[offState]
	}
	if len(b) > offCAState {
		i.CAState = b[offCAState]
	}
	if len(b) > offAppLimited {
		i.AppLimited = b[offAppLimited]&0x1 != 0
	}
	i.SndMSS = u32(b, offSndMSS)
	i.Unacked = u32(b, offUnacked)
	i.Lost = u32(b, offLost)
	i.Retrans = u32(b, offRetrans)
	i.RTT = u32(b, offRTT)
	i.RTTVar = u32(b, offRTTVar)
	i.SndSsthresh = u32(b, offSndSsthresh)
	i.SndCwnd = u32(b, offSndCwnd)
	i.TotalRetrans = u32(b, offTotalRetrans)
	i.NotsentBytes = u32(b, offNotsent)
	i.MinRTT = u32(b, offMinRTT)
	i.Delivered = u32(b, offDelivered)
	i.SndWnd = u32(b, offSndWnd)
	i.PacingRate = u64(b, offPacingRate)
	i.MaxPacingRate = u64(b, offMaxPacing)
	i.BytesAcked = u64(b, offBytesAcked)
	i.BytesSent = u64(b, offBytesSent)
	i.BytesRetrans = u64(b, offBytesRetrans)
	i.DeliveryRate = u64(b, offDeliveryRate)
	i.BusyTime = u64(b, offBusyTime)
	i.RwndLimited = u64(b, offRwndLimited)
	i.SndbufLimited = u64(b, offSndbufLimit)
	return i
}

// BytesInFlight is the closest TCP_INFO comes to the quantity a rate
// controller actually reasons about. It is packets times the sender's MSS
// rather than a byte count the kernel keeps, so it is an estimate.
func (i Info) BytesInFlight() uint64 {
	return uint64(i.Unacked) * uint64(i.SndMSS)
}

// CwndBytes expresses the congestion window in the same units as the
// bandwidth-delay product it should be compared against.
func (i Info) CwndBytes() uint64 {
	return uint64(i.SndCwnd) * uint64(i.SndMSS)
}

// Limiter names what was binding at the moment of the sample, which is the
// question every phase gate in this project's datacenter plan has to answer.
// It reports the constraint rather than the symptom: a connection can be slow
// because the window is small, because the peer will not accept more, because
// the socket buffer is full, or because nobody handed it anything to send, and
// only the last of those is not a transport problem.
//
// prev is the previous sample from the same connection; the limited counters
// are cumulative, so only their increments describe this interval.
func (i Info) Limiter(prev Info) string {
	switch {
	case i.RwndLimited > prev.RwndLimited:
		return "receiver-window"
	case i.SndbufLimited > prev.SndbufLimited:
		return "send-buffer"
	case i.AppLimited:
		return "application"
	case i.BytesInFlight()+uint64(i.SndMSS) >= i.CwndBytes():
		return "congestion-window"
	default:
		return "unattributed"
	}
}

// ErrUnsupportedSentinel lets a caller distinguish a platform that has no
// TCP_INFO from a socket that failed to answer. The distinction matters
// because the first is a known limit to be reported once and worked around,
// and the second is a bug.
var ErrUnsupportedSentinel = errUnsupported{}

type errUnsupported struct{}

func (errUnsupported) Error() string { return "tcpinfo: not supported on this platform" }
