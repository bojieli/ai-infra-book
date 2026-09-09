package pathsim

import (
	"container/heap"
	"sync"
	"time"
)

// deliveryQueue holds packets until their modelled arrival time.
//
// The obvious implementation - one goroutine and one timer per delayed packet -
// does not survive contact with a fast path. At 200 ms of delay every packet in
// flight is a live goroutine, so offered load translates directly into
// scheduler pressure: with a 1 Gbit/s bottleneck configured and no loss at all,
// the emulator delivered 19-30 Mbit/s, *less* than the same path configured at
// 100 Mbit/s, because timer and goroutine overhead inflated the delay the
// transport measured and its controller backed off. An emulator that becomes
// the bottleneck silently caps every result taken with it.
//
// One goroutine per direction, waking on the earliest deadline in a heap,
// removes that coupling: cost is one timer regardless of how many packets are
// in flight.
type deliveryQueue struct {
	mu      sync.Mutex
	pending scheduledHeap
	wake    chan struct{}
	done    chan struct{}
	closed  bool
	started bool
}

type scheduled struct {
	deliver time.Time
	payload []byte
	send    func([]byte)
	// counted lets the direction's byte and packet counters advance at
	// delivery rather than at admission.
	direction *direction
}

type scheduledHeap []scheduled

func (h scheduledHeap) Len() int           { return len(h) }
func (h scheduledHeap) Less(i, j int) bool { return h[i].deliver.Before(h[j].deliver) }
func (h scheduledHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *scheduledHeap) Push(value any)    { *h = append(*h, value.(scheduled)) }
func (h *scheduledHeap) Pop() any {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func newDeliveryQueue(done chan struct{}) *deliveryQueue {
	return &deliveryQueue{wake: make(chan struct{}, 1), done: done}
}

// add schedules one packet. It never blocks the caller, so a reader loop is
// never held up by the delay model.
func (q *deliveryQueue) add(item scheduled) {
	q.mu.Lock()
	if q.closed {
		q.mu.Unlock()
		return
	}
	heap.Push(&q.pending, item)
	earliest := q.pending[0].deliver == item.deliver
	if !q.started {
		q.started = true
		go q.run()
	}
	q.mu.Unlock()
	if earliest {
		select {
		case q.wake <- struct{}{}:
		default:
		}
	}
}

func (q *deliveryQueue) run() {
	timer := time.NewTimer(time.Hour)
	defer timer.Stop()
	for {
		q.mu.Lock()
		if q.closed {
			q.mu.Unlock()
			return
		}
		if len(q.pending) == 0 {
			q.mu.Unlock()
			select {
			case <-q.wake:
				continue
			case <-q.done:
				return
			}
		}
		next := q.pending[0]
		wait := time.Until(next.deliver)
		if wait > 0 {
			q.mu.Unlock()
			if !timer.Stop() {
				select {
				case <-timer.C:
				default:
				}
			}
			timer.Reset(wait)
			select {
			case <-timer.C:
			case <-q.wake:
			case <-q.done:
				return
			}
			continue
		}
		heap.Pop(&q.pending)
		q.mu.Unlock()
		next.direction.packetsOut.Add(1)
		next.direction.bytesOut.Add(uint64(len(next.payload)))
		next.send(next.payload)
	}
}

func (q *deliveryQueue) close() {
	q.mu.Lock()
	q.closed = true
	q.pending = nil
	q.mu.Unlock()
	select {
	case q.wake <- struct{}{}:
	default:
	}
}
