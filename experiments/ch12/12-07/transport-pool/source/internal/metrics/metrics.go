// Package metrics provides the small, dependency-free operational surface
// needed by queqiaod. It intentionally exports aggregate counters only: no
// destinations, session IDs, secrets, or application payload are retained.
package metrics

import (
	"fmt"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

type Registry struct {
	activeFlows      atomic.Int64
	flowsStarted     atomic.Uint64
	flowsCompleted   atomic.Uint64
	flowsFailed      atomic.Uint64
	bytesUp          atomic.Uint64
	bytesDown        atomic.Uint64
	laneFailures     atomic.Uint64
	laneReplacements atomic.Uint64
	fallbacks        atomic.Uint64
	// udpPathUnavailable counts conservative differential failures: QUIC
	// explicitly failed while TLS/TCP reached the same configured endpoint.
	// A pending QUIC handshake and a faster TCP handshake are not failures. It
	// is deliberately separate from fallbacks, which also includes flows sent
	// directly to TCP while UDP is in cooldown.
	udpPathUnavailable atomic.Uint64
	// endpointRaceFailures counts AUTO transport races in which neither QUIC
	// nor TLS/TCP reached the configured endpoint. Keeping this separate from
	// UDP failures tells an operator whether TCP was a usable (but degraded)
	// escape path or whether the endpoint was unreachable on both transports.
	endpointRaceFailures atomic.Uint64
	// transientUDPSendErrors counts local route/buffer failures which were
	// deliberately presented to QUIC as packet loss. Without that translation
	// a sub-second Wi-Fi reassociation would terminate every stream sharing the
	// UDP socket instead of entering ordinary PTO recovery.
	transientUDPSendErrors atomic.Uint64
	udpReconnects          atomic.Uint64
	udpRescueFailures      atomic.Uint64
	completionTimeouts     atomic.Uint64
	flowTimeouts           atomic.Uint64
	portHops               atomic.Uint64
	// The authorization counters below describe the gateway's own state
	// rather than any flow. A store that cannot be re-read leaves the last
	// snapshot in force, which keeps established devices connecting while
	// every enrollment fails - a split that looks healthy from the outside
	// and is invisible without these.
	authorizationRefreshFailures     atomic.Uint64
	authorizationReloads             atomic.Uint64
	authorizationConsecutiveFailures atomic.Uint64
	// authorizationLastGoodUnix is exported as a timestamp rather than an age
	// so the value does not depend on when it was scraped; the age is
	// time() - metric, the way process_start_time_seconds is used.
	authorizationLastGoodUnix atomic.Int64
	classTransitions          [3]atomic.Uint64
	// The rescue window is dropped rather than allowed to throttle the
	// application. That trade has to be visible: a flow that has evicted part
	// of its window will fail rather than recover if its lane dies, so a
	// rising count is the operator's warning that lane rescue is no longer
	// available for the affected traffic.
	replayBytesInUse atomic.Int64
	// bulkIsolations counts bulk flows moved off the shared control
	// connection, which is the mechanism that protects interactive latency.
	bulkIsolations atomic.Uint64
	// reinjections counts frames re-sent on a second lane because the first
	// was holding up the receiver. A rising count means striping is costing
	// duplicate capacity to keep the reorder span bounded.
	reinjections atomic.Uint64
	// peerProtocolViolations counts peers that completed mutual TLS on a
	// protocol-1 ALPN and then behaved in a way protocol 1 forbids. It is
	// deliberately separate from lane failures: a lane that dies is a network
	// event, while this is a peer whose build disagrees about the wire, and the
	// two need different responses from whoever is on call.
	peerProtocolViolations atomic.Uint64
	// laneJoinRefusals counts lane joins this endpoint answered with a reset,
	// by reason. A rescue refused is a flow that will fail, so a rising count
	// here is the other half of a peer's stalling and failing flows -- the
	// half the endpoint doing the refusing can see.
	laneJoinRefusals [LaneJoinReasons]atomic.Uint64
	// flowStallsDetected counts flows whose watchdog saw no forward progress
	// for three round trips while work was pending. A stall is a suspicion,
	// not a failure: the lane stays in service while a rescue runs beside it,
	// so this counter rising without lane_failures is the watchdog doing the
	// job the idle timeout used to do fifteen seconds later.
	flowStallsDetected atomic.Uint64
	// stallSpareAttaches counts stalls where a second healthy lane already
	// existed and took over the flow's new writes immediately, without
	// waiting for a rescue handshake.
	stallSpareAttaches atomic.Uint64
	// laneRescueAttempts counts individual dial+JOIN attempts started by the
	// parallel rescue. One rescue round starts several, so this outpaces
	// lane_replacements: the difference is what the first-wins race cancelled.
	laneRescueAttempts atomic.Uint64
	// laneRescueWins is indexed by the attempt that produced the winning
	// lane. Attempt zero is the established strategy (pooled generation, or
	// the committed TCP handoff); the rest are independent QUIC dials. A win
	// by a later attempt is the parallel rescue paying for itself.
	laneRescueWins [RescueAttemptSlots]atomic.Uint64
	// laneGraceExtensions counts replacement graces this gateway restarted
	// because a rescue JOIN arrived while the flow was still waiting out an
	// outage. Without the extension the hard grace could expire in the middle
	// of the very handshake that was coming to save the flow.
	laneGraceExtensions atomic.Uint64
	// accountAdmissionRefusals counts flow opens this gateway answered with a
	// reset because of the opening account's own policy, by reason. It exists
	// because these refusals used to be the one admission decision the
	// gateway made silently: an account whose limit was set too low to browse
	// through produced a client reporting resets and a server reporting
	// nothing at all, at any log level, with no counter to check. The reason
	// an operator needs is which limit was hit.
	accountAdmissionRefusals [AccountRefusalReasons]atomic.Uint64
	// quicObservationsExpired counts per-flow QUIC telemetry entries dropped
	// because nothing refreshed them within quicObservationTTL. The aggregate
	// below reports round-trip time as a maximum, so an entry that is never
	// refreshed and never removed pins the exported estimate at whatever it
	// last held for as long as the process lives. A rising count means some
	// flow stopped publishing without removing its entry, and it is the only
	// warning an operator gets that the aggregate is being held up by a
	// measurement that is no longer being taken.
	quicObservationsExpired atomic.Uint64
	// quicCounters are the process-wide monotonic QUIC totals.  They are
	// accumulated from per-connection forward deltas rather than derived by
	// summing the live flows, because the connections they measure are shared
	// by many flows and outlive any one of them.  See QUICConnectionCounters.
	quicCounters quicCounterTotals
	telemetryMu  sync.Mutex
	quicFlows    map[uint64]quicObservation
	// clock is the time source for observation freshness. Tests replace it;
	// production leaves it nil and reads the wall clock.
	clock func() time.Time
}

// LaneJoinRefusal is why a lane join was refused.
//
// The set is closed at compile time because these are exported label values.
// A label whose values come off the wire is a label a peer can make unbounded,
// and this exposition deliberately carries no user-controlled labels at all.
type LaneJoinRefusal int

const (
	// LaneJoinInvalidIdentity is a join naming no usable session, lane, or
	// flow: a peer disagreeing about the wire rather than a lost session.
	LaneJoinInvalidIdentity LaneJoinRefusal = iota
	// LaneJoinUnknownSession is a rescue arriving after this endpoint has
	// forgotten the session. It is the refusal that matters operationally:
	// the peer's flow cannot be resumed and will fail.
	LaneJoinUnknownSession
	// LaneJoinFlowMismatch is a join for a live session naming a different
	// flow, and LaneJoinPrincipalMismatch one from a different device than
	// created the session. Neither is a forgotten session, and the second is a
	// peer reaching for identifiers that are routing, not credentials.
	LaneJoinFlowMismatch
	LaneJoinPrincipalMismatch
	// LaneJoinInvalidControlReplacement is a control-lane replacement for a
	// flow that reserved none, or on a transport that cannot carry one.
	LaneJoinInvalidControlReplacement
	// LaneJoinLaneUnavailable is a join refused by this endpoint's own
	// admission ceiling rather than by anything about the peer.
	LaneJoinLaneUnavailable
	// LaneJoinReasons is how many reasons there are.
	LaneJoinReasons
)

// RescueAttemptSlots is how many concurrent dial+JOIN attempts one parallel
// rescue round runs. It is a compile-time bound because the winning attempt
// is an exported label value, and this exposition carries no unbounded
// labels.
const RescueAttemptSlots = 3

var laneJoinRefusalNames = [LaneJoinReasons]string{
	LaneJoinInvalidIdentity:           "invalid_identity",
	LaneJoinUnknownSession:            "unknown_session",
	LaneJoinFlowMismatch:              "flow_mismatch",
	LaneJoinPrincipalMismatch:         "principal_mismatch",
	LaneJoinInvalidControlReplacement: "invalid_control_replacement",
	LaneJoinLaneUnavailable:           "lane_unavailable",
}

// String is the stable label and log value for a refusal reason.
func (r LaneJoinRefusal) String() string {
	if r < 0 || r >= LaneJoinReasons {
		return "unknown"
	}
	return laneJoinRefusalNames[r]
}

// AccountRefusal is why a flow open was refused by the opening account's
// admission policy.
//
// The set is closed at compile time for the same reason LaneJoinRefusal's is:
// these are exported label values, and a label whose values come off the wire
// is a label a peer can make unbounded.
type AccountRefusal int

const (
	// AccountRefusalFlowLimit is an account already holding as many
	// concurrent flows as its policy allows. One flow is one TCP connection
	// or one UDP association, so this is reached by ordinary browsing on any
	// account whose flow ceiling was set as though it counted devices.
	AccountRefusalFlowLimit AccountRefusal = iota
	// AccountRefusalClientLimit is a device that would be one more
	// simultaneously active device than the account's policy allows. Unlike
	// the flow limit it does not move with how hard one device is being used,
	// so it is the refusal an operator should expect to see when a
	// subscription is genuinely oversubscribed.
	AccountRefusalClientLimit
	// AccountRefusalUnauthorized is an account or device that stopped being
	// authorized between the TLS handshake and this flow open.
	AccountRefusalUnauthorized
	// AccountRefusalReasons is how many reasons there are.
	AccountRefusalReasons
)

var accountRefusalNames = [AccountRefusalReasons]string{
	AccountRefusalFlowLimit:    "flow_limit",
	AccountRefusalClientLimit:  "client_limit",
	AccountRefusalUnauthorized: "unauthorized",
}

// String is the stable label and log value for a refusal reason.
func (r AccountRefusal) String() string {
	if r < 0 || r >= AccountRefusalReasons {
		return "unknown"
	}
	return accountRefusalNames[r]
}

// quicObservationTTL is how long one flow's QUIC telemetry keeps contributing
// to the process aggregate without being refreshed. A live flow republishes
// every second, so this is generous by an order of magnitude; its purpose is
// to bound the damage of an entry that is never refreshed again rather than to
// expire a busy flow that was briefly descheduled.
const quicObservationTTL = 15 * time.Second

// quicObservation is one flow's telemetry with the time it was recorded.
type quicObservation struct {
	QUICObservation
	updated time.Time
}

// quicCounterTotals holds the process-wide QUIC counters.  They are atomics
// rather than fields under telemetryMu so that publishing a connection's
// forward movement never contends with a scrape walking the flow map.
type quicCounterTotals struct {
	bytesSent               atomic.Uint64
	bytesReceived           atomic.Uint64
	packetsSent             atomic.Uint64
	packetsReceived         atomic.Uint64
	lossObservedPackets     atomic.Uint64
	codedSources            atomic.Uint64
	codedRecovered          atomic.Uint64
	codedLost               atomic.Uint64
	controllerBytesLost     atomic.Uint64
	controllerPacketsLost   atomic.Uint64
	controllerSamples       atomic.Uint64
	controllerNonAppSamples atomic.Uint64
	controllerAppSamples    atomic.Uint64
	controllerStateMisses   atomic.Uint64
	controllerZeroSamples   atomic.Uint64
}

func (t *quicCounterTotals) add(d QUICConnectionCounters) {
	t.bytesSent.Add(d.BytesSent)
	t.bytesReceived.Add(d.BytesReceived)
	t.packetsSent.Add(d.PacketsSent)
	t.packetsReceived.Add(d.PacketsReceived)
	t.lossObservedPackets.Add(d.LossObservedPackets)
	t.codedSources.Add(d.CodedSources)
	t.codedRecovered.Add(d.CodedRecovered)
	t.codedLost.Add(d.CodedLost)
	t.controllerBytesLost.Add(d.ControllerBytesLost)
	t.controllerPacketsLost.Add(d.ControllerPacketsLost)
	t.controllerSamples.Add(d.ControllerSamples)
	t.controllerNonAppSamples.Add(d.ControllerNonAppSamples)
	t.controllerAppSamples.Add(d.ControllerAppSamples)
	t.controllerStateMisses.Add(d.ControllerStateMisses)
	t.controllerZeroSamples.Add(d.ControllerZeroSamples)
}

func (t *quicCounterTotals) load() QUICConnectionCounters {
	return QUICConnectionCounters{
		BytesSent:               t.bytesSent.Load(),
		BytesReceived:           t.bytesReceived.Load(),
		PacketsSent:             t.packetsSent.Load(),
		PacketsReceived:         t.packetsReceived.Load(),
		LossObservedPackets:     t.lossObservedPackets.Load(),
		CodedSources:            t.codedSources.Load(),
		CodedRecovered:          t.codedRecovered.Load(),
		CodedLost:               t.codedLost.Load(),
		ControllerBytesLost:     t.controllerBytesLost.Load(),
		ControllerPacketsLost:   t.controllerPacketsLost.Load(),
		ControllerSamples:       t.controllerSamples.Load(),
		ControllerNonAppSamples: t.controllerNonAppSamples.Load(),
		ControllerAppSamples:    t.controllerAppSamples.Load(),
		ControllerStateMisses:   t.controllerStateMisses.Load(),
		ControllerZeroSamples:   t.controllerZeroSamples.Load(),
	}
}

type Snapshot struct {
	ActiveFlows, FlowsStarted, FlowsCompleted, FlowsFailed        int64
	BytesUp, BytesDown, LaneFailures, LaneReplacements, Fallbacks uint64
	UDPPathUnavailable, EndpointTransportRaceFailures             uint64
	TransientUDPSendErrors                                        uint64
	UDPAssociationReconnects, UDPAssociationRescueFailures        uint64
	CompletionTimeouts                                            uint64
	FlowTimeouts                                                  uint64
	PortHops                                                      uint64
	AuthorizationRefreshFailures, AuthorizationReloads            uint64
	AuthorizationConsecutiveRefreshFailures                       uint64
	AuthorizationLastGoodUnix                                     int64
	ClassTransitions                                              [3]uint64
	BulkIsolations, Reinjections                                  uint64
	PeerProtocolViolations                                        uint64
	ReplayBytesInUse                                              int64
	QUICLanes                                                     int64
	QUICLatestRTT, QUICSmoothedRTT                                time.Duration
	QUICBytesSent, QUICBytesReceived                              uint64
	QUICPacketsSent, QUICPacketsReceived                          uint64
	QUICLossObservedPackets                                       uint64
	QUICCodedSources, QUICCodedRecovered, QUICCodedLost           uint64
	QUICControllerKind                                            string
	QUICControllerMode                                            uint32
	QUICControllerMaxBandwidth, QUICControllerPacingRate          uint64
	QUICControllerLatestSample, QUICControllerSamples             uint64
	QUICControllerLatestAckRate, QUICControllerLatestSendRate     uint64
	QUICControllerNonAppSamples, QUICControllerAppSamples         uint64
	QUICControllerStateMisses, QUICControllerZeroSamples          uint64
	QUICControllerRound                                           uint64
	QUICControllerCongestionWindow, QUICControllerBytesInFlight   uint64
	QUICControllerBytesLost, QUICControllerPacketsLost            uint64
	QUICControllerMinRTT                                          time.Duration
	QUICSampleMean, QUICSampleMax, QUICSampleDelivered            uint64
	QUICSampleInterval                                            time.Duration
	QUICErasureSend                                               float64
	QUICDelayBrake                                                float64
	QUICControllerInRecovery                                      bool
	// QUICObservationsExpired counts flow telemetry entries dropped because
	// they stopped being refreshed. See quicObservationsExpired.
	QUICObservationsExpired uint64
	// LaneJoinRefusals is indexed by LaneJoinRefusal.
	LaneJoinRefusals [LaneJoinReasons]uint64
	// AccountAdmissionRefusals is indexed by AccountRefusal.
	AccountAdmissionRefusals                [AccountRefusalReasons]uint64
	FlowStallsDetected, StallSpareAttaches  uint64
	LaneRescueAttempts, LaneGraceExtensions uint64
	// LaneRescueWins is indexed by the winning attempt of a rescue round.
	LaneRescueWins [RescueAttemptSlots]uint64
}

// QUICObservation is a point-in-time aggregate over the lanes of one logical
// flow.  RTT is represented as a maximum so an operator can see the worst
// active lane without any user-controlled labels.
//
// Everything here is a gauge: it describes the transport as it stands at the
// moment of the observation, so replacing it wholesale on every publication
// and dropping it when the flow ends are both correct.  The cumulative
// counters a QUIC connection also reports are deliberately not in this type;
// they are connection-scoped and are published separately.  See
// QUICConnectionCounters.
type QUICObservation struct {
	Lanes                      int
	LatestRTT                  time.Duration
	SmoothedRTT                time.Duration
	ControllerKind             string
	ControllerMode             uint32
	ControllerMaxBandwidth     uint64
	ControllerLatestSample     uint64
	ControllerLatestAckRate    uint64
	ControllerLatestSendRate   uint64
	ControllerRound            uint64
	ControllerPacingRate       uint64
	ControllerCongestionWindow uint64
	ControllerBytesInFlight    uint64
	ControllerMinRTT           time.Duration
	ControllerSampleMean       uint64
	ControllerSampleMax        uint64
	ControllerSampleDelivered  uint64
	ControllerSampleInterval   time.Duration
	ControllerErasure          float64
	ControllerDelayBrake       float64
	ControllerInRecovery       bool
}

// QUICConnectionCounters is the cumulative half of one QUIC connection's
// telemetry.  Every field counts since that connection was established and
// only ever moves forward.
//
// These are connection-scoped, and a connection is not a flow.  Connections
// are pooled: many lanes belonging to many flows read the same numbers from
// the same connection.  Summing what every live flow currently reports
// therefore counts one connection once per flow that references it, and makes
// the process total rise and fall as flows and lanes enter and leave the live
// set.  A value that moves in both directions is not a counter, and a
// dashboard differencing it reports whatever the churn happened to be rather
// than what the path did -- a loss rate assembled from two such differences is
// noise in both the numerator and the denominator.
//
// The process totals are accumulated from forward deltas measured once per
// connection instead.  See AddQUICConnectionCounters.
type QUICConnectionCounters struct {
	BytesSent       uint64
	BytesReceived   uint64
	PacketsSent     uint64
	PacketsReceived uint64
	// LossObservedPackets is every loss the sender detected on this
	// connection. LossSuppressedPackets is the part it withheld from the
	// congestion controller as erasure, and ControllerPacketsLost is the part
	// it charged as congestion; the first is the sum of the other two.
	//
	// quic-go's own BytesLost and PacketsLost used to be carried here and are
	// deliberately absent. They are incremented only inside its cubic sender,
	// and this transport installs its own controller through
	// SetCongestionControl, so nothing ever moved them off zero. A counter
	// that cannot be produced is worse than a missing one once it is
	// monotonic, because it then looks like a measurement.
	LossObservedPackets   uint64
	LossSuppressedPackets uint64
	// Coded receive-direction outcomes. Every source symbol the peer sent ends
	// in exactly one of the three, so they are a denominator as well as three
	// counters: arrived, reconstructed by the code, or left the window still
	// missing and re-issued by the session a round trip later.
	//
	// These are the other direction from LossObservedPackets, which is what
	// this sender detected on the direction it sends into. An endpoint has to
	// publish both or a path's two halves cannot be told apart, and on the
	// motivating incident they differed by a factor of five.
	CodedSources            uint64
	CodedRecovered          uint64
	CodedLost               uint64
	ControllerBytesLost     uint64
	ControllerPacketsLost   uint64
	ControllerSamples       uint64
	ControllerNonAppSamples uint64
	ControllerAppSamples    uint64
	ControllerStateMisses   uint64
	ControllerZeroSamples   uint64
}

// Advance returns the forward movement of every counter between two readings
// of the same connection, which is what may be added to a process total.
//
// A field that did not move contributes nothing, and so does a field that
// moved backwards.  Both cases are ordinary rather than defensive: quic-go is
// allowed to un-declare a loss it later decides was reordering, and a pooled
// connection replaced by a new generation restarts its counters at zero.  The
// alternative -- treating a decrease as a huge increase by wrapping the
// subtraction -- is how an unsigned counter reports a terabyte of loss for a
// packet that arrived after all.
func (c QUICConnectionCounters) Advance(previous QUICConnectionCounters) QUICConnectionCounters {
	forward := func(now, before uint64) uint64 {
		if now <= before {
			return 0
		}
		return now - before
	}
	return QUICConnectionCounters{
		BytesSent:               forward(c.BytesSent, previous.BytesSent),
		BytesReceived:           forward(c.BytesReceived, previous.BytesReceived),
		PacketsSent:             forward(c.PacketsSent, previous.PacketsSent),
		PacketsReceived:         forward(c.PacketsReceived, previous.PacketsReceived),
		LossObservedPackets:     forward(c.LossObservedPackets, previous.LossObservedPackets),
		CodedSources:            forward(c.CodedSources, previous.CodedSources),
		CodedRecovered:          forward(c.CodedRecovered, previous.CodedRecovered),
		CodedLost:               forward(c.CodedLost, previous.CodedLost),
		ControllerBytesLost:     forward(c.ControllerBytesLost, previous.ControllerBytesLost),
		ControllerPacketsLost:   forward(c.ControllerPacketsLost, previous.ControllerPacketsLost),
		ControllerSamples:       forward(c.ControllerSamples, previous.ControllerSamples),
		ControllerNonAppSamples: forward(c.ControllerNonAppSamples, previous.ControllerNonAppSamples),
		ControllerAppSamples:    forward(c.ControllerAppSamples, previous.ControllerAppSamples),
		ControllerStateMisses:   forward(c.ControllerStateMisses, previous.ControllerStateMisses),
		ControllerZeroSamples:   forward(c.ControllerZeroSamples, previous.ControllerZeroSamples),
	}
}

// Add folds one connection's forward movement into a running total.
func (c *QUICConnectionCounters) Add(delta QUICConnectionCounters) {
	c.BytesSent += delta.BytesSent
	c.BytesReceived += delta.BytesReceived
	c.PacketsSent += delta.PacketsSent
	c.PacketsReceived += delta.PacketsReceived
	c.LossObservedPackets += delta.LossObservedPackets
	c.CodedSources += delta.CodedSources
	c.CodedRecovered += delta.CodedRecovered
	c.CodedLost += delta.CodedLost
	c.ControllerBytesLost += delta.ControllerBytesLost
	c.ControllerPacketsLost += delta.ControllerPacketsLost
	c.ControllerSamples += delta.ControllerSamples
	c.ControllerNonAppSamples += delta.ControllerNonAppSamples
	c.ControllerAppSamples += delta.ControllerAppSamples
	c.ControllerStateMisses += delta.ControllerStateMisses
	c.ControllerZeroSamples += delta.ControllerZeroSamples
}

// IsZero reports whether nothing moved, which lets a caller skip the atomic
// writes entirely on the common idle publication.
func (c QUICConnectionCounters) IsZero() bool { return c == QUICConnectionCounters{} }

func New() *Registry { return &Registry{quicFlows: make(map[uint64]quicObservation)} }

// now reads the registry's time source. A zero-value Registry is a supported
// "metrics disabled" construction, so this must work without New.
func (r *Registry) now() time.Time {
	if r.clock != nil {
		return r.clock()
	}
	return time.Now()
}

func (r *Registry) FlowStarted() { r.activeFlows.Add(1); r.flowsStarted.Add(1) }

func (r *Registry) FlowFinished(bytesUp, bytesDown uint64, failed bool) {
	// A flow can be torn down concurrently by the accept-limit, context
	// cancellation, and transport-failure paths.  A Load followed by Add is
	// not atomic as a pair and could make the exported gauge negative if two
	// teardown paths race.  Decrement with CAS and clamp at zero instead.
	for {
		active := r.activeFlows.Load()
		if active <= 0 || r.activeFlows.CompareAndSwap(active, active-1) {
			break
		}
	}
	if failed {
		r.flowsFailed.Add(1)
	} else {
		r.flowsCompleted.Add(1)
	}
	r.bytesUp.Add(bytesUp)
	r.bytesDown.Add(bytesDown)
}

func (r *Registry) LaneFailure()     { r.laneFailures.Add(1) }
func (r *Registry) LaneReplacement() { r.laneReplacements.Add(1) }
func (r *Registry) Fallback()        { r.fallbacks.Add(1) }
func (r *Registry) UDPPathUnavailable() {
	r.udpPathUnavailable.Add(1)
}
func (r *Registry) EndpointTransportRaceFailure() {
	r.endpointRaceFailures.Add(1)
}
func (r *Registry) TransientUDPSendError() {
	r.transientUDPSendErrors.Add(1)
}
func (r *Registry) UDPAssociationReconnect() {
	r.udpReconnects.Add(1)
}
func (r *Registry) UDPAssociationRescueFailure() {
	r.udpRescueFailures.Add(1)
}

// ReplayBytes tracks the endpoint's accounted rescue-window memory.
func (r *Registry) ReplayBytes(delta int64) {
	if r == nil || delta == 0 {
		return
	}
	if remaining := r.replayBytesInUse.Add(delta); remaining < 0 {
		r.replayBytesInUse.Store(0)
	}
}

// Reinjected records a frame re-sent on a second lane to unblock the receiver.
func (r *Registry) Reinjected() {
	if r == nil {
		return
	}
	r.reinjections.Add(1)
}

// BulkIsolated records a bulk flow moving off the shared control connection.
func (r *Registry) BulkIsolated() {
	if r == nil {
		return
	}
	r.bulkIsolations.Add(1)
}

// LaneJoinRefused records a lane join answered with a reset.
func (r *Registry) LaneJoinRefused(reason LaneJoinRefusal) {
	if r == nil || reason < 0 || reason >= LaneJoinReasons {
		return
	}
	r.laneJoinRefusals[reason].Add(1)
}

// AccountAdmissionRefused records a flow open answered with a reset because of
// the opening account's admission policy.
func (r *Registry) AccountAdmissionRefused(reason AccountRefusal) {
	if r == nil || reason < 0 || reason >= AccountRefusalReasons {
		return
	}
	r.accountAdmissionRefusals[reason].Add(1)
}

// PeerProtocolViolation records a peer that authenticated as a protocol-1
// endpoint and then did something protocol 1 forbids.
func (r *Registry) PeerProtocolViolation() { r.peerProtocolViolations.Add(1) }

func (r *Registry) CompletionTimeout() { r.completionTimeouts.Add(1) }
func (r *Registry) FlowTimeout()       { r.flowTimeouts.Add(1) }
func (r *Registry) PortHop()           { r.portHops.Add(1) }

// FlowStallDetected records one flow stall episode: work was pending and no
// forward progress was observed for three round trips. It is counted once per
// episode, not per scan, so a flow that stays stalled is one event.
func (r *Registry) FlowStallDetected() { r.flowStallsDetected.Add(1) }

// StallSpareAttached records a stall where an already-healthy lane took over
// the flow's new writes without waiting for a rescue handshake.
func (r *Registry) StallSpareAttached() { r.stallSpareAttaches.Add(1) }

// LaneRescueAttempt records one dial+JOIN attempt started by the parallel
// rescue, winning or not.
func (r *Registry) LaneRescueAttempt() { r.laneRescueAttempts.Add(1) }

// LaneRescueWin records which attempt of a rescue round produced the lane the
// flow kept. Attempt zero is the established recovery strategy; a later index
// is an independent QUIC dial that beat it.
func (r *Registry) LaneRescueWin(attempt int) {
	if attempt < 0 || attempt >= RescueAttemptSlots {
		return
	}
	r.laneRescueWins[attempt].Add(1)
}

// LaneGraceExtended records a replacement grace restarted because a rescue
// JOIN arrived while the flow was waiting out an outage.
func (r *Registry) LaneGraceExtended() { r.laneGraceExtensions.Add(1) }

// AuthorizationRefreshFailed records one failed attempt to re-read the
// authorization store, carrying how many have now failed in a row so a chronic
// outage is distinguishable from a single missed tick.
func (r *Registry) AuthorizationRefreshFailed(consecutive uint64) {
	r.authorizationRefreshFailures.Add(1)
	r.authorizationConsecutiveFailures.Store(consecutive)
}

// AuthorizationRefreshed records a successful read. lastGood is when the
// snapshot now in force was read, and reloaded reports whether it differed
// from the one it replaced.
func (r *Registry) AuthorizationRefreshed(lastGood time.Time, reloaded bool) {
	r.authorizationConsecutiveFailures.Store(0)
	if !lastGood.IsZero() {
		r.authorizationLastGoodUnix.Store(lastGood.Unix())
	}
	if reloaded {
		r.authorizationReloads.Add(1)
	}
}
func (r *Registry) ClassTransition(class int) {
	if class >= 0 && class < len(r.classTransitions) {
		r.classTransitions[class].Add(1)
	}
}

func (r *Registry) ObserveQUIC(key uint64, o QUICObservation) {
	if key == 0 {
		return
	}
	if o.Lanes < 0 {
		o.Lanes = 0
	}
	if o.LatestRTT < 0 {
		o.LatestRTT = 0
	}
	if o.SmoothedRTT < 0 {
		o.SmoothedRTT = 0
	}
	now := r.now()
	r.telemetryMu.Lock()
	if r.quicFlows == nil {
		r.quicFlows = make(map[uint64]quicObservation)
	}
	r.quicFlows[key] = quicObservation{QUICObservation: o, updated: now}
	r.telemetryMu.Unlock()
}

// AddQUICConnectionCounters folds one connection's forward movement into the
// process totals.
//
// The caller measures the delta against a baseline held per connection, so
// two flows sharing a pooled connection do not both contribute it: whichever
// publishes first moves the baseline, and the other adds nothing.  That is
// what makes these totals independent of how many flows happen to reference a
// connection, and what lets a flow's telemetry be dropped the moment it ends
// without the totals moving backwards.
func (r *Registry) AddQUICConnectionCounters(delta QUICConnectionCounters) {
	if r == nil || delta.IsZero() {
		return
	}
	r.quicCounters.add(delta)
}

func (r *Registry) RemoveQUIC(key uint64) {
	if key == 0 {
		return
	}
	r.telemetryMu.Lock()
	delete(r.quicFlows, key)
	r.telemetryMu.Unlock()
}

func (r *Registry) Snapshot() Snapshot {
	s := Snapshot{
		ActiveFlows: r.activeFlows.Load(), FlowsStarted: int64(r.flowsStarted.Load()),
		FlowsCompleted: int64(r.flowsCompleted.Load()), FlowsFailed: int64(r.flowsFailed.Load()),
		BytesUp: r.bytesUp.Load(), BytesDown: r.bytesDown.Load(), LaneFailures: r.laneFailures.Load(),
		LaneReplacements: r.laneReplacements.Load(), Fallbacks: r.fallbacks.Load(),
		UDPPathUnavailable:                      r.udpPathUnavailable.Load(),
		EndpointTransportRaceFailures:           r.endpointRaceFailures.Load(),
		TransientUDPSendErrors:                  r.transientUDPSendErrors.Load(),
		UDPAssociationReconnects:                r.udpReconnects.Load(),
		UDPAssociationRescueFailures:            r.udpRescueFailures.Load(),
		CompletionTimeouts:                      r.completionTimeouts.Load(),
		FlowTimeouts:                            r.flowTimeouts.Load(),
		PortHops:                                r.portHops.Load(),
		AuthorizationRefreshFailures:            r.authorizationRefreshFailures.Load(),
		AuthorizationReloads:                    r.authorizationReloads.Load(),
		AuthorizationConsecutiveRefreshFailures: r.authorizationConsecutiveFailures.Load(),
		AuthorizationLastGoodUnix:               r.authorizationLastGoodUnix.Load(),
		BulkIsolations:                          r.bulkIsolations.Load(),
		Reinjections:                            r.reinjections.Load(),
		PeerProtocolViolations:                  r.peerProtocolViolations.Load(),
		ReplayBytesInUse:                        r.replayBytesInUse.Load(),
	}
	for i := range s.ClassTransitions {
		s.ClassTransitions[i] = r.classTransitions[i].Load()
	}
	for i := range s.LaneJoinRefusals {
		s.LaneJoinRefusals[i] = r.laneJoinRefusals[i].Load()
	}
	for i := range s.AccountAdmissionRefusals {
		s.AccountAdmissionRefusals[i] = r.accountAdmissionRefusals[i].Load()
	}
	s.FlowStallsDetected = r.flowStallsDetected.Load()
	s.StallSpareAttaches = r.stallSpareAttaches.Load()
	s.LaneRescueAttempts = r.laneRescueAttempts.Load()
	s.LaneGraceExtensions = r.laneGraceExtensions.Load()
	for i := range s.LaneRescueWins {
		s.LaneRescueWins[i] = r.laneRescueWins[i].Load()
	}
	now := r.now()
	var expired uint64
	r.telemetryMu.Lock()
	var quicLanes int64
	var latestRTT, smoothedRTT time.Duration
	var controllerKind string
	var controllerMode uint32
	var controllerMaxBandwidth, controllerPacingRate, controllerCwnd, controllerBytesInFlight uint64
	var controllerLatestSample uint64
	var controllerLatestAckRate, controllerLatestSendRate uint64
	var controllerRound uint64
	var controllerMinRTT time.Duration
	var controllerErasure, controllerDelayBrake float64
	var sampleMean, sampleMax, sampleDelivered uint64
	var sampleInterval time.Duration
	var controllerRecovery bool
	for key, entry := range r.quicFlows {
		// An entry nobody refreshes is not a measurement of anything. Because
		// the round-trip aggregate below is a maximum, keeping one would pin
		// the exported estimate at a value the path stopped having, and every
		// live flow measuring a faster path would be invisible underneath it.
		if now.Sub(entry.updated) > quicObservationTTL {
			delete(r.quicFlows, key)
			expired++
			continue
		}
		o := entry.QUICObservation
		quicLanes += int64(o.Lanes)
		if o.LatestRTT > latestRTT {
			latestRTT = o.LatestRTT
		}
		if o.SmoothedRTT > smoothedRTT {
			smoothedRTT = o.SmoothedRTT
		}
		if o.ControllerKind != "" {
			if controllerKind == "" {
				controllerKind = o.ControllerKind
			} else if controllerKind != o.ControllerKind {
				controllerKind = "mixed"
			}
			if o.ControllerMode > controllerMode {
				controllerMode = o.ControllerMode
			}
			if o.ControllerMaxBandwidth > controllerMaxBandwidth {
				controllerMaxBandwidth = o.ControllerMaxBandwidth
			}
			if o.ControllerLatestSample > controllerLatestSample {
				controllerLatestSample = o.ControllerLatestSample
			}
			if o.ControllerLatestAckRate > controllerLatestAckRate {
				controllerLatestAckRate = o.ControllerLatestAckRate
			}
			if o.ControllerLatestSendRate > controllerLatestSendRate {
				controllerLatestSendRate = o.ControllerLatestSendRate
			}
			if o.ControllerRound > controllerRound {
				controllerRound = o.ControllerRound
			}
			if o.ControllerPacingRate > controllerPacingRate {
				controllerPacingRate = o.ControllerPacingRate
			}
			if o.ControllerCongestionWindow > controllerCwnd {
				controllerCwnd = o.ControllerCongestionWindow
			}
			if o.ControllerBytesInFlight > controllerBytesInFlight {
				controllerBytesInFlight = o.ControllerBytesInFlight
			}
			if o.ControllerMinRTT > controllerMinRTT {
				controllerMinRTT = o.ControllerMinRTT
			}
			// Both are already pooled across the lanes of one endpoint pair,
			// so a maximum here selects the worst pair this process is
			// serving rather than the worst lane, which is what a maximum over
			// per-lane estimates would have meant.
			if o.ControllerErasure > controllerErasure {
				controllerErasure = o.ControllerErasure
			}
			// The widest sample any lane produced, with the interval and
			// delivery that produced it, so the three stay from one sample.
			if o.ControllerSampleMax > sampleMax {
				sampleMax = o.ControllerSampleMax
				sampleDelivered = o.ControllerSampleDelivered
				sampleInterval = o.ControllerSampleInterval
			}
			if o.ControllerSampleMean > sampleMean {
				sampleMean = o.ControllerSampleMean
			}
			if o.ControllerDelayBrake > controllerDelayBrake {
				controllerDelayBrake = o.ControllerDelayBrake
			}
			controllerRecovery = controllerRecovery || o.ControllerInRecovery
		}
	}
	r.telemetryMu.Unlock()
	if expired > 0 {
		r.quicObservationsExpired.Add(expired)
	}
	s.QUICObservationsExpired = r.quicObservationsExpired.Load()
	s.QUICLanes = quicLanes
	s.QUICLatestRTT = latestRTT
	s.QUICSmoothedRTT = smoothedRTT
	// The counters come from the process totals, not from the flows above.
	// They must not depend on which flows happen to be live at scrape time.
	counters := r.quicCounters.load()
	s.QUICBytesSent = counters.BytesSent
	s.QUICBytesReceived = counters.BytesReceived
	s.QUICPacketsSent = counters.PacketsSent
	s.QUICPacketsReceived = counters.PacketsReceived
	s.QUICLossObservedPackets = counters.LossObservedPackets
	s.QUICCodedSources = counters.CodedSources
	s.QUICCodedRecovered = counters.CodedRecovered
	s.QUICCodedLost = counters.CodedLost
	s.QUICControllerKind = controllerKind
	s.QUICControllerMode = controllerMode
	s.QUICControllerMaxBandwidth = controllerMaxBandwidth
	s.QUICControllerLatestSample = controllerLatestSample
	s.QUICControllerLatestAckRate = controllerLatestAckRate
	s.QUICControllerLatestSendRate = controllerLatestSendRate
	s.QUICControllerSamples = counters.ControllerSamples
	s.QUICControllerNonAppSamples = counters.ControllerNonAppSamples
	s.QUICControllerAppSamples = counters.ControllerAppSamples
	s.QUICControllerStateMisses = counters.ControllerStateMisses
	s.QUICControllerZeroSamples = counters.ControllerZeroSamples
	s.QUICControllerRound = controllerRound
	s.QUICControllerPacingRate = controllerPacingRate
	s.QUICControllerCongestionWindow = controllerCwnd
	s.QUICControllerBytesInFlight = controllerBytesInFlight
	s.QUICControllerBytesLost = counters.ControllerBytesLost
	s.QUICControllerPacketsLost = counters.ControllerPacketsLost
	s.QUICControllerMinRTT = controllerMinRTT
	s.QUICSampleMean, s.QUICSampleMax = sampleMean, sampleMax
	s.QUICSampleDelivered, s.QUICSampleInterval = sampleDelivered, sampleInterval
	s.QUICErasureSend = controllerErasure
	s.QUICDelayBrake = controllerDelayBrake
	s.QUICControllerInRecovery = controllerRecovery
	return s
}

// ServeHTTP emits a stable Prometheus-compatible exposition subset. Values
// are process-wide aggregates and contain no user-controlled labels.
func (r *Registry) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodGet && req.Method != http.MethodHead {
		w.Header().Set("Allow", http.MethodGet+", "+http.MethodHead)
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s := r.Snapshot()
	w.Header().Set("Content-Type", "text/plain; version=0.0.4")
	fmt.Fprintf(w, "queqiao_active_flows %d\n", s.ActiveFlows)
	fmt.Fprintf(w, "queqiao_flows_started_total %d\n", s.FlowsStarted)
	fmt.Fprintf(w, "queqiao_flows_completed_total %d\n", s.FlowsCompleted)
	fmt.Fprintf(w, "queqiao_flows_failed_total %d\n", s.FlowsFailed)
	fmt.Fprintf(w, "queqiao_bytes_up_total %d\n", s.BytesUp)
	fmt.Fprintf(w, "queqiao_bytes_down_total %d\n", s.BytesDown)
	fmt.Fprintf(w, "queqiao_lane_failures_total %d\n", s.LaneFailures)
	fmt.Fprintf(w, "queqiao_lane_replacements_total %d\n", s.LaneReplacements)
	fmt.Fprintf(w, "queqiao_fallbacks_total %d\n", s.Fallbacks)
	fmt.Fprintf(w, "queqiao_udp_path_unavailable_total %d\n", s.UDPPathUnavailable)
	fmt.Fprintf(w, "queqiao_endpoint_transport_races_failed_total %d\n", s.EndpointTransportRaceFailures)
	fmt.Fprintf(w, "queqiao_udp_transient_send_errors_total %d\n", s.TransientUDPSendErrors)
	fmt.Fprintf(w, "queqiao_udp_association_reconnects_total %d\n", s.UDPAssociationReconnects)
	fmt.Fprintf(w, "queqiao_udp_association_rescue_failures_total %d\n", s.UDPAssociationRescueFailures)
	fmt.Fprintf(w, "queqiao_completion_timeouts_total %d\n", s.CompletionTimeouts)
	fmt.Fprintf(w, "queqiao_flow_timeouts_total %d\n", s.FlowTimeouts)
	fmt.Fprintf(w, "queqiao_port_hops_total %d\n", s.PortHops)
	// A non-zero consecutive count means the gateway is enforcing a snapshot
	// it can no longer re-read: established devices keep working while every
	// enrollment fails. Alert on the consecutive count, and use
	// time() - queqiao_authorization_last_good_timestamp_seconds for the age
	// of the rules actually in force.
	fmt.Fprintf(w, "queqiao_authorization_refresh_failures_total %d\n", s.AuthorizationRefreshFailures)
	fmt.Fprintf(w, "queqiao_authorization_reloads_total %d\n", s.AuthorizationReloads)
	fmt.Fprintf(w, "queqiao_authorization_consecutive_refresh_failures %d\n", s.AuthorizationConsecutiveRefreshFailures)
	fmt.Fprintf(w, "queqiao_authorization_last_good_timestamp_seconds %d\n", s.AuthorizationLastGoodUnix)
	// A rising unreplayable count means lane rescue is no longer available for
	// the affected flows: their rescue window was dropped to keep the
	// application moving, so a lane failure now fails the flow.
	fmt.Fprintf(w, "queqiao_replay_bytes_in_use %d\n", s.ReplayBytesInUse)
	fmt.Fprintf(w, "queqiao_bulk_isolations_total %d\n", s.BulkIsolations)
	fmt.Fprintf(w, "queqiao_lane_reinjections_total %d\n", s.Reinjections)
	fmt.Fprintf(w, "queqiao_peer_protocol_violations_total %d\n", s.PeerProtocolViolations)
	fmt.Fprintf(w, "queqiao_quic_lanes %d\n", s.QUICLanes)
	fmt.Fprintf(w, "queqiao_quic_latest_rtt_seconds %.9f\n", s.QUICLatestRTT.Seconds())
	fmt.Fprintf(w, "queqiao_quic_smoothed_rtt_seconds %.9f\n", s.QUICSmoothedRTT.Seconds())
	fmt.Fprintf(w, "queqiao_quic_bytes_sent %d\n", s.QUICBytesSent)
	fmt.Fprintf(w, "queqiao_quic_bytes_received %d\n", s.QUICBytesReceived)
	fmt.Fprintf(w, "queqiao_quic_packets_sent %d\n", s.QUICPacketsSent)
	fmt.Fprintf(w, "queqiao_quic_packets_received %d\n", s.QUICPacketsReceived)
	// What the path did, and what the controller was told about it. Observed
	// is the one to divide by packets_sent for a loss rate; the controller
	// figure below is congestion only, and on an erasure path the two differ
	// by most of the loss.
	fmt.Fprintf(w, "queqiao_quic_loss_observed_packets_total %d\n", s.QUICLossObservedPackets)
	// A rising expiry count means some flow's telemetry stopped being
	// refreshed without being removed. The RTT values above are maxima, so
	// that is the failure mode which freezes them at a stale constant.
	fmt.Fprintf(w, "queqiao_quic_observations_expired_total %d\n", s.QUICObservationsExpired)
	if s.QUICControllerKind != "" {
		fmt.Fprintf(w, "queqiao_quic_controller_kind{kind=\"%s\"} 1\n", s.QUICControllerKind)
	}
	fmt.Fprintf(w, "queqiao_quic_controller_mode %d\n", s.QUICControllerMode)
	fmt.Fprintf(w, "queqiao_quic_controller_max_bandwidth_bytes_per_second %d\n", s.QUICControllerMaxBandwidth)
	fmt.Fprintf(w, "queqiao_quic_controller_latest_sample_bytes_per_second %d\n", s.QUICControllerLatestSample)
	fmt.Fprintf(w, "queqiao_quic_controller_latest_ack_rate_bytes_per_second %d\n", s.QUICControllerLatestAckRate)
	fmt.Fprintf(w, "queqiao_quic_controller_latest_send_rate_bytes_per_second %d\n", s.QUICControllerLatestSendRate)
	fmt.Fprintf(w, "queqiao_quic_controller_samples_total %d\n", s.QUICControllerSamples)
	fmt.Fprintf(w, "queqiao_quic_controller_non_app_limited_samples_total %d\n", s.QUICControllerNonAppSamples)
	fmt.Fprintf(w, "queqiao_quic_controller_app_limited_samples_total %d\n", s.QUICControllerAppSamples)
	fmt.Fprintf(w, "queqiao_quic_controller_state_misses_total %d\n", s.QUICControllerStateMisses)
	fmt.Fprintf(w, "queqiao_quic_controller_zero_samples_total %d\n", s.QUICControllerZeroSamples)
	fmt.Fprintf(w, "queqiao_quic_controller_round %d\n", s.QUICControllerRound)
	fmt.Fprintf(w, "queqiao_quic_controller_pacing_rate_bytes_per_second %d\n", s.QUICControllerPacingRate)
	fmt.Fprintf(w, "queqiao_quic_controller_congestion_window_bytes %d\n", s.QUICControllerCongestionWindow)
	fmt.Fprintf(w, "queqiao_quic_controller_bytes_in_flight %d\n", s.QUICControllerBytesInFlight)
	fmt.Fprintf(w, "queqiao_quic_controller_bytes_lost %d\n", s.QUICControllerBytesLost)
	fmt.Fprintf(w, "queqiao_quic_controller_packets_lost %d\n", s.QUICControllerPacketsLost)
	fmt.Fprintf(w, "queqiao_quic_controller_min_rtt_seconds %.9f\n", s.QUICControllerMinRTT.Seconds())
	// The erasure the path is measured to be applying, labelled by the
	// direction it was measured on. A gateway's send direction is its
	// downstream, which is the direction that was invisible when the only
	// erasure figure published was the floor below.
	fmt.Fprintf(w, "queqiao_erasure_ratio{direction=\"send\"} %.9f\n", s.QUICErasureSend)
	// The receive direction, measured by this endpoint's decoders rather than
	// inferred from acknowledgements. Every source symbol the peer sent ends in
	// exactly one of the three outcomes below, so they are a denominator and
	// the two ratios are derived from them rather than averaged across flows.
	//
	// The residual is what the code could not repair and the session has to
	// re-issue a round trip later. It is the number the motivating incident was
	// actually made of -- 11% of the payload -- and it had no metric at all.
	fmt.Fprintf(w, "queqiao_coded_symbols_total{outcome=\"arrived\"} %d\n", s.QUICCodedSources)
	fmt.Fprintf(w, "queqiao_coded_symbols_total{outcome=\"recovered\"} %d\n", s.QUICCodedRecovered)
	fmt.Fprintf(w, "queqiao_coded_symbols_total{outcome=\"lost\"} %d\n", s.QUICCodedLost)
	fmt.Fprintf(w, "queqiao_erasure_ratio{direction=\"receive\"} %.9f\n", s.ReceiveErasure())
	fmt.Fprintf(w, "queqiao_erasure_residual_ratio{direction=\"receive\"} %.9f\n", s.ReceiveResidual())
	// How much of the sending rate the delay bound is removing. Non-zero means
	// the path is carrying more than one bandwidth-delay product of queue and
	// is being held back by it, which is a different condition from a path that
	// simply measured less.
	fmt.Fprintf(w, "queqiao_delay_brake_ratio %.9f\n", s.QUICDelayBrake)
	// The shape of the delivery-rate samples the bandwidth estimate is built
	// from. The estimate is a maximum over these, and a maximum far above the
	// mean is a tail rather than the path -- while a tail measured over a short
	// interval is a measurement artefact rather than either.
	fmt.Fprintf(w, "queqiao_quic_sample_mean_bytes_per_second %d\n", s.QUICSampleMean)
	fmt.Fprintf(w, "queqiao_quic_sample_max_bytes_per_second %d\n", s.QUICSampleMax)
	fmt.Fprintf(w, "queqiao_quic_sample_max_delivered_bytes %d\n", s.QUICSampleDelivered)
	fmt.Fprintf(w, "queqiao_quic_sample_max_interval_seconds %.9f\n", s.QUICSampleInterval.Seconds())
	if s.QUICControllerInRecovery {
		fmt.Fprintln(w, "queqiao_quic_controller_in_recovery 1")
	} else {
		fmt.Fprintln(w, "queqiao_quic_controller_in_recovery 0")
	}
	for i, value := range s.ClassTransitions {
		fmt.Fprintf(w, "queqiao_class_transitions_total{class=\"%d\"} %d\n", i, value)
	}
	// The reasons stay separate because they mean different things to whoever
	// is on call: a forgotten session is a peer whose flows are failing, a
	// principal mismatch is a peer reaching for a session that is not its own,
	// and an unavailable lane is this endpoint's own ceiling.
	for i, value := range s.LaneJoinRefusals {
		fmt.Fprintf(w, "queqiao_lane_join_refused_total{reason=\"%s\"} %d\n", LaneJoinRefusal(i), value)
	}
	for i, value := range s.AccountAdmissionRefusals {
		fmt.Fprintf(w, "queqiao_account_admission_refused_total{reason=\"%s\"} %d\n", AccountRefusal(i), value)
	}
	// Stalls are suspicions, not failures: the suspected lane stays in
	// service while the rescue runs beside it. rescue_attempts outpaces
	// rescue wins by what the first-wins race cancelled, and a win by an
	// attempt above zero is a parallel dial beating the established strategy.
	fmt.Fprintf(w, "queqiao_flow_stalls_detected_total %d\n", s.FlowStallsDetected)
	fmt.Fprintf(w, "queqiao_stall_spare_attaches_total %d\n", s.StallSpareAttaches)
	fmt.Fprintf(w, "queqiao_lane_rescue_attempts_total %d\n", s.LaneRescueAttempts)
	for i, value := range s.LaneRescueWins {
		fmt.Fprintf(w, "queqiao_lane_rescue_wins_total{attempt=\"%d\"} %d\n", i, value)
	}
	fmt.Fprintf(w, "queqiao_lane_grace_extensions_total %d\n", s.LaneGraceExtensions)
}

// ReceiveErasure is the share of the peer's source symbols that did not arrive,
// whether the code repaired them or not: the wire loss this endpoint measured
// on the direction it receives.
//
// It is derived from the counters rather than averaged across flows, because a
// mean of per-flow ratios weights a flow that moved a kilobyte the same as one
// that moved a gigabyte.
func (s Snapshot) ReceiveErasure() float64 {
	total := s.QUICCodedSources + s.QUICCodedRecovered + s.QUICCodedLost
	if total == 0 {
		return 0
	}
	return float64(s.QUICCodedRecovered+s.QUICCodedLost) / float64(total)
}

// ReceiveResidual is the share the code could not repair, which the session
// above has to re-issue a round trip later. It is the cost the erasure actually
// imposes once the code has done what it can.
func (s Snapshot) ReceiveResidual() float64 {
	total := s.QUICCodedSources + s.QUICCodedRecovered + s.QUICCodedLost
	if total == 0 {
		return 0
	}
	return float64(s.QUICCodedLost) / float64(total)
}
