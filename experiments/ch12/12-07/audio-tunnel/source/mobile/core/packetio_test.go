package mobilecore

import (
	"context"
	"sync"
	"testing"
	"time"
)

func TestPacketFlowCallbackForwardsIPv4UDP(t *testing.T) {
	socksAddress, closeServer := startSocksUDPServer(t, false)
	defer closeServer()
	flow := newTestPacketIO()
	engine, err := newPacketStackWithDevice(
		context.Background(),
		&callbackPacketDevice{packetIO: flow},
		0,
		defaultMTU,
		8,
		socksClient{address: socksAddress, handshakeTimeout: time.Second},
		nil,
	)
	if err != nil {
		t.Fatal(err)
	}
	engine.start()
	defer engine.Close()

	flow.reads <- makeIPv4UDP(
		mustAddrPort(t, "10.0.0.2:43210"),
		mustAddrPort(t, "198.51.100.7:53"),
		[]byte("packet-flow"),
	)
	select {
	case response := <-flow.writes:
		if len(response) < 28 || string(response[int(response[0]&0x0f)*4+8:]) != "packet-flow" {
			t.Fatalf("unexpected packet-flow response: %x", response)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("timed out waiting for callback packet response")
	}
}

type testPacketIO struct {
	reads     chan []byte
	writes    chan []byte
	closed    chan struct{}
	closeOnce sync.Once
}

func newTestPacketIO() *testPacketIO {
	return &testPacketIO{
		reads: make(chan []byte, 1), writes: make(chan []byte, 1), closed: make(chan struct{}),
	}
}

func (f *testPacketIO) ReadPacket() []byte {
	select {
	case packet := <-f.reads:
		return packet
	case <-f.closed:
		return nil
	}
}

func (f *testPacketIO) WritePacket(packet []byte) bool {
	select {
	case f.writes <- append([]byte(nil), packet...):
		return true
	case <-f.closed:
		return false
	}
}

func (f *testPacketIO) Close() { f.closeOnce.Do(func() { close(f.closed) }) }
