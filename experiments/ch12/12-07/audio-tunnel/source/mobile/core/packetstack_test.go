package mobilecore

import (
	"context"
	"encoding/binary"
	"net/netip"
	"os"
	"testing"
	"time"

	"golang.org/x/sys/unix"
	"gvisor.dev/gvisor/pkg/tcpip"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv4"
	"gvisor.dev/gvisor/pkg/tcpip/network/ipv6"
)

func mustAddrPort(t *testing.T, address string) netip.AddrPort {
	t.Helper()
	return netip.MustParseAddrPort(address)
}

func TestPacketProtocolAndPlatformHeader(t *testing.T) {
	if protocol, ok := packetProtocol(make([]byte, 20)); ok || protocol != 0 {
		t.Fatal("accepted a packet without an IP version")
	}
	v4 := make([]byte, 20)
	v4[0] = 0x45
	if protocol, ok := packetProtocol(v4); !ok || protocol != ipv4.ProtocolNumber {
		t.Fatal("did not recognize IPv4")
	}
	v6 := make([]byte, 40)
	v6[0] = 0x60
	if protocol, ok := packetProtocol(v6); !ok || protocol != ipv6.ProtocolNumber {
		t.Fatal("did not recognize IPv6")
	}
	stack := &packetStack{offset: 4}
	var header [4]byte
	binary.BigEndian.PutUint32(header[:], unix.AF_INET6)
	if !stack.validPlatformHeader(header[:], ipv6.ProtocolNumber) {
		t.Fatal("rejected a valid utun IPv6 header")
	}
	if stack.validPlatformHeader(header[:], ipv4.ProtocolNumber) {
		t.Fatal("accepted a mismatched utun family header")
	}
}

func TestEndpointAddress(t *testing.T) {
	address := netip.MustParseAddr("2001:db8::42")
	raw := address.As16()
	got, err := endpointAddress(tcpip.AddrFrom16(raw), 443)
	if err != nil {
		t.Fatal(err)
	}
	if got != netip.MustParseAddrPort("[2001:db8::42]:443") {
		t.Fatalf("endpoint = %s", got)
	}
}

func TestBridgeShutdownWaitsForEveryWorker(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	done := make(chan struct{}, 2)
	closed := false
	waitForBridgeWorkers(ctx, done, 2, func() {
		closed = true
		done <- struct{}{}
		done <- struct{}{}
	})
	if !closed || len(done) != 0 {
		t.Fatalf("bridge shutdown left resources open: closed=%t pending=%d", closed, len(done))
	}
}

func TestPacketStackAdmissionReclaimsLargeCapacity(t *testing.T) {
	p := &packetStack{ctx: context.Background(), admission: make(chan struct{}, 1024)}
	for index := 0; index < 1024; index++ {
		if !p.acquire() {
			t.Fatalf("session %d was rejected", index)
		}
	}
	if p.acquire() {
		t.Fatal("admission exceeded its configured capacity")
	}
	for index := 0; index < 1024; index++ {
		p.release()
		p.sessionWG.Done()
	}
	if !p.acquire() {
		t.Fatal("released session capacity was not reusable")
	}
	p.release()
	p.sessionWG.Done()
	p.sessionMu.Lock()
	p.closing.Store(true)
	p.sessionMu.Unlock()
	if p.acquire() {
		t.Fatal("session was admitted during upper-layer shutdown")
	}
}

func TestPacketStackForwardsIPv4UDPThroughOwnedSocksClient(t *testing.T) {
	socksAddress, closeServer := startSocksUDPServer(t, false)
	defer closeServer()
	pair, err := unix.Socketpair(unix.AF_UNIX, unix.SOCK_DGRAM, 0)
	if err != nil {
		t.Fatal(err)
	}
	original := os.NewFile(uintptr(pair[0]), "test-tun")
	defer original.Close()
	defer unix.Close(pair[1])
	engine, err := newPacketStack(context.Background(), pair[0], 0, defaultMTU, 8,
		socksClient{address: socksAddress, handshakeTimeout: time.Second}, nil)
	if err != nil {
		t.Fatal(err)
	}
	engine.start()
	defer engine.Close()

	request := makeIPv4UDP(
		netip.MustParseAddrPort("10.0.0.2:43210"),
		netip.MustParseAddrPort("198.51.100.7:53"),
		[]byte("queqiao-mobile-udp"),
	)
	if _, err := unix.Write(pair[1], request); err != nil {
		t.Fatal(err)
	}
	poll := []unix.PollFd{{Fd: int32(pair[1]), Events: unix.POLLIN}}
	ready, err := unix.Poll(poll, 3000)
	if err != nil {
		t.Fatal(err)
	}
	if ready != 1 {
		t.Fatal("timed out waiting for UDP response from packet engine")
	}
	response := make([]byte, defaultMTU)
	n, err := unix.Read(pair[1], response)
	if err != nil {
		t.Fatal(err)
	}
	response = response[:n]
	if len(response) < 28 || response[9] != 17 {
		t.Fatalf("unexpected IPv4 response (%d bytes)", len(response))
	}
	headerLength := int(response[0]&0x0f) * 4
	if string(response[headerLength+8:]) != "queqiao-mobile-udp" {
		t.Fatalf("UDP response payload = %q", response[headerLength+8:])
	}
	deadline := time.Now().Add(time.Second)
	for {
		got := engine.snapshot()
		if got.PacketsIn > 0 && got.PacketsOut > 0 {
			break
		}
		if time.Now().After(deadline) {
			t.Fatalf("packet counters = %+v", got)
		}
		time.Sleep(time.Millisecond)
	}
}

func makeIPv4UDP(source, destination netip.AddrPort, payload []byte) []byte {
	packet := make([]byte, 20+8+len(payload))
	packet[0] = 0x45
	binary.BigEndian.PutUint16(packet[2:4], uint16(len(packet)))
	packet[8] = 64
	packet[9] = 17
	sourceAddress := source.Addr().As4()
	destinationAddress := destination.Addr().As4()
	copy(packet[12:16], sourceAddress[:])
	copy(packet[16:20], destinationAddress[:])
	binary.BigEndian.PutUint16(packet[10:12], internetChecksum(packet[:20]))
	binary.BigEndian.PutUint16(packet[20:22], source.Port())
	binary.BigEndian.PutUint16(packet[22:24], destination.Port())
	binary.BigEndian.PutUint16(packet[24:26], uint16(8+len(payload)))
	copy(packet[28:], payload)
	return packet
}

func internetChecksum(data []byte) uint16 {
	var sum uint32
	for len(data) >= 2 {
		sum += uint32(binary.BigEndian.Uint16(data[:2]))
		data = data[2:]
	}
	if len(data) == 1 {
		sum += uint32(data[0]) << 8
	}
	for sum>>16 != 0 {
		sum = sum&0xffff + sum>>16
	}
	return ^uint16(sum)
}
