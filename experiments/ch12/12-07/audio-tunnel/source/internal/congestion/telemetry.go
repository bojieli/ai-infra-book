package congestion

import (
	"sync/atomic"
	"time"
)

// ControllerTelemetry is a read-only, point-in-time projection of a QUIC
// sender. It deliberately contains no destination or application metadata.
// Values are safe to read from the flow telemetry goroutine while quic-go is
// invoking the controller on its packet-processing goroutine.
type ControllerTelemetry struct {
	Kind             string
	Mode             uint32
	MaxBandwidth     uint64
	LatestSample     uint64
	LatestAckRate    uint64
	LatestSendRate   uint64
	Samples          uint64
	NonAppSamples    uint64
	AppSamples       uint64
	StateMisses      uint64
	ZeroSamples      uint64
	Round            uint64
	PacingRate       uint64
	CongestionWindow uint64
	BytesInFlight    uint64
	// BytesLost and PacketsLost are what reached the congestion controller,
	// which on an erasure path is not what the path did. ErasureSender charges
	// the controller only the share of each loss the channel does not explain,
	// so these count congestion and not erasure.
	BytesLost   uint64
	PacketsLost uint64
	// PacketsLostObserved is every loss the sender detected. It is derived
	// independently of PacketsLost above -- one from the sender's own counter,
	// one from the controller's -- and the two now agree, because no loss is
	// withheld from the controller any more.
	//
	// They did not always agree. While loss was classified, only the share the
	// channel could not explain reached the controller, and publishing the
	// controller's figure alone let a gateway erasing a fifth of its downstream
	// report single-digit loss. The pair is kept rather than collapsed to one
	// field so that a divergence between them is visible rather than silent.
	//
	// It is a packet count and not a byte count because a loss rate is a count
	// over a count of trials.
	PacketsLostObserved uint64
	MinRTT              time.Duration
	InRecovery          bool
	// DelayBrake is the share of the sending rate the delay bound is currently
	// removing, in [0,1). It is non-zero only while the path is carrying more
	// than one bandwidth-delay product of queue.
	//
	// It is published because a rate that has been held back by the path's own
	// queue and a rate that simply measured less look identical otherwise, and
	// the two call for opposite responses.
	DelayBrake float64
	// SampleMean, SampleMax, SampleMaxDelivered and SampleMaxInterval describe
	// the delivery-rate samples the bandwidth estimate is built from, which the
	// estimate alone cannot: a rate is high either because the path is fast or
	// because the window it was measured over was short, and only the interval
	// and the delivery behind it tell those apart.
	//
	// A maximum far above the mean is a tail rather than the path. This is here
	// because that distinction could not be settled in a harness and has to be
	// read off a real one.
	SampleMean         uint64
	SampleMax          uint64
	SampleMaxDelivered uint64
	SampleMaxInterval  time.Duration
	// Erasure is the share of packets the path is measured to be erasing on
	// the direction this controller sends into, pooled across the lanes that
	// share it. It is what a code is sized from.
	//
	// ErasureFloor below is not a substitute for it and is not a smaller
	// version of it. The floor is biased low on purpose so that pacing errs
	// towards slowing down, and it is a lower envelope for the lifetime of a
	// connection, so it keeps what a clean window established while this
	// follows the path. On the live incident the two read 1.76% and 19.9%.
	Erasure float64
}

const (
	ControllerModeUnknown uint32 = iota
	ControllerModeStartup
	ControllerModeDrain
	ControllerModeProbeBW
	ControllerModeProbeRTT
	ControllerModeAdaptive
	ControllerModeBrutal
	ControllerModeStock
)

// TelemetryProvider is implemented by the optional controllers. The stock
// quic-go controller does not expose an equivalent public state projection,
// so its mode remains ControllerModeStock only when explicitly supplied by a
// transport adapter.
type TelemetryProvider interface {
	Telemetry() ControllerTelemetry
}

// telemetryState stores every mutable value atomically. Congestion-control
// callbacks are serialized by quic-go, but observation runs independently and
// must not introduce a data race or a lock on the packet hot path.
type telemetryState struct {
	kind           string
	mode           atomic.Uint32
	maxBandwidth   atomic.Uint64
	latestSample   atomic.Uint64
	latestAckRate  atomic.Uint64
	latestSendRate atomic.Uint64
	samples        atomic.Uint64
	nonAppSamples  atomic.Uint64
	appSamples     atomic.Uint64
	stateMisses    atomic.Uint64
	zeroSamples    atomic.Uint64
	round          atomic.Uint64
	// The shape of the samples behind the estimate; see ControllerTelemetry.
	sampleMean          atomic.Uint64
	sampleMax           atomic.Uint64
	sampleMaxDelivered  atomic.Uint64
	sampleMaxIntervalNS atomic.Int64
	pacingRate          atomic.Uint64
	congestionWindow    atomic.Uint64
	bytesInFlight       atomic.Uint64
	bytesLost           atomic.Uint64
	packetsLost         atomic.Uint64
	minRTTNS            atomic.Int64
	inRecovery          atomic.Bool
}

func newTelemetryState(kind string) telemetryState {
	return telemetryState{kind: kind}
}

// observeLoss records loss reported to an external congestion controller.
// quic-go's public controller interface doesn't provide a connection-stats
// handle, so custom controllers must retain their own authoritative counters.
func (t *telemetryState) observeLoss(bytes, packets uint64) {
	t.bytesLost.Add(bytes)
	t.packetsLost.Add(packets)
}

func (t *telemetryState) update(mode uint32, maxBandwidth, pacingRate uint64, congestionWindow, bytesInFlight int64, minRTT time.Duration, inRecovery bool) {
	if congestionWindow < 0 {
		congestionWindow = 0
	}
	if bytesInFlight < 0 {
		bytesInFlight = 0
	}
	if minRTT < 0 {
		minRTT = 0
	}
	t.mode.Store(mode)
	t.maxBandwidth.Store(maxBandwidth)
	t.pacingRate.Store(pacingRate)
	t.congestionWindow.Store(uint64(congestionWindow))
	t.bytesInFlight.Store(uint64(bytesInFlight))
	t.minRTTNS.Store(minRTT.Nanoseconds())
	t.inRecovery.Store(inRecovery)
}

// updateSampler publishes diagnostic delivery-sampler state. Controllers
// that do not use the TUIC packet sampler leave these values at zero.
func (t *telemetryState) updateSampleShape(mean, max, delivered uint64, interval time.Duration) {
	t.sampleMean.Store(mean)
	t.sampleMax.Store(max)
	t.sampleMaxDelivered.Store(delivered)
	t.sampleMaxIntervalNS.Store(int64(interval))
}

func (t *telemetryState) updateSampler(latestSample, latestAckRate, latestSendRate, samples, nonAppSamples, appSamples, stateMisses, zeroSamples, round uint64) {
	t.latestSample.Store(latestSample)
	t.latestAckRate.Store(latestAckRate)
	t.latestSendRate.Store(latestSendRate)
	t.samples.Store(samples)
	t.nonAppSamples.Store(nonAppSamples)
	t.appSamples.Store(appSamples)
	t.stateMisses.Store(stateMisses)
	t.zeroSamples.Store(zeroSamples)
	t.round.Store(round)
}

func (t *telemetryState) snapshot() ControllerTelemetry {
	return ControllerTelemetry{
		Kind:             t.kind,
		Mode:             t.mode.Load(),
		MaxBandwidth:     t.maxBandwidth.Load(),
		LatestSample:     t.latestSample.Load(),
		LatestAckRate:    t.latestAckRate.Load(),
		LatestSendRate:   t.latestSendRate.Load(),
		Samples:          t.samples.Load(),
		NonAppSamples:    t.nonAppSamples.Load(),
		AppSamples:       t.appSamples.Load(),
		StateMisses:      t.stateMisses.Load(),
		ZeroSamples:      t.zeroSamples.Load(),
		Round:            t.round.Load(),
		PacingRate:       t.pacingRate.Load(),
		CongestionWindow: t.congestionWindow.Load(),
		BytesInFlight:    t.bytesInFlight.Load(),
		BytesLost:        t.bytesLost.Load(),
		PacketsLost:      t.packetsLost.Load(),
		// A controller that does not classify loss observed exactly what it
		// was charged. ErasureSender overrides both of these because it does.
		PacketsLostObserved: t.packetsLost.Load(),
		MinRTT:              time.Duration(t.minRTTNS.Load()),
		InRecovery:          t.inRecovery.Load(),
		SampleMean:          t.sampleMean.Load(),
		SampleMax:           t.sampleMax.Load(),
		SampleMaxDelivered:  t.sampleMaxDelivered.Load(),
		SampleMaxInterval:   time.Duration(t.sampleMaxIntervalNS.Load()),
	}
}
