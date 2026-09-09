package mobilecore

import (
	"bufio"
	"context"
	"errors"
	"io"
	"net"
	"net/netip"
	"strconv"
	"testing"
	"time"
)

func TestSocksTCPConnect(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	destination := netip.MustParseAddrPort("203.0.113.8:443")
	serverErr := make(chan error, 1)
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			serverErr <- err
			return
		}
		defer conn.Close()
		reader := bufio.NewReader(conn)
		command, got, err := acceptSocksRequest(reader, conn)
		if err != nil {
			serverErr <- err
			return
		}
		if command != socksConnect || got != destination {
			serverErr <- io.ErrUnexpectedEOF
			return
		}
		if err := writeSocksSuccess(conn, netip.MustParseAddrPort("127.0.0.1:1")); err != nil {
			serverErr <- err
			return
		}
		buffer := make([]byte, 4)
		if _, err := io.ReadFull(reader, buffer); err != nil {
			serverErr <- err
			return
		}
		serverErr <- writeFull(conn, buffer)
	}()

	client := socksClient{address: listener.Addr().String(), handshakeTimeout: time.Second}
	conn, err := client.dialTCP(context.Background(), destination)
	if err != nil {
		t.Fatal(err)
	}
	if err := writeFull(conn, []byte("ping")); err != nil {
		t.Fatal(err)
	}
	response := make([]byte, 4)
	if _, err := io.ReadFull(conn, response); err != nil {
		t.Fatal(err)
	}
	_ = conn.Close()
	if string(response) != "ping" {
		t.Fatalf("echo = %q", response)
	}
	if err := <-serverErr; err != nil {
		t.Fatal(err)
	}
}

func TestSocksUDPAssociate(t *testing.T) {
	server, closeServer := startSocksUDPServer(t, false)
	defer closeServer()
	destination := netip.MustParseAddrPort("198.51.100.7:53")
	association, err := (socksClient{address: server, handshakeTimeout: time.Second}).dialUDP(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	defer association.Close()
	_ = association.SetDeadline(time.Now().Add(2 * time.Second))
	if err := association.WriteTo([]byte("dns"), destination); err != nil {
		t.Fatal(err)
	}
	response := make([]byte, 32)
	n, err := association.ReadFrom(response, destination)
	if err != nil {
		t.Fatal(err)
	}
	if string(response[:n]) != "dns" {
		t.Fatalf("UDP echo = %q", response[:n])
	}
}

func TestSocksUDPRejectsUnexpectedSource(t *testing.T) {
	server, closeServer := startSocksUDPServer(t, true)
	defer closeServer()
	destination := netip.MustParseAddrPort("198.51.100.7:53")
	association, err := (socksClient{address: server, handshakeTimeout: time.Second}).dialUDP(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	defer association.Close()
	_ = association.SetDeadline(time.Now().Add(2 * time.Second))
	if err := association.WriteTo([]byte("dns"), destination); err != nil {
		t.Fatal(err)
	}
	if _, err := association.ReadFrom(make([]byte, 32), destination); err == nil {
		t.Fatal("accepted a SOCKS UDP packet from a different source")
	}
}

func TestSocksRequestSupportsIPv6(t *testing.T) {
	destination := netip.MustParseAddrPort("[2001:db8::1]:8443")
	request, err := socksRequest(socksConnect, destination)
	if err != nil {
		t.Fatal(err)
	}
	if request[3] != socksIPv6 || len(request) != 22 {
		t.Fatalf("IPv6 request length/type = %d/%d", len(request), request[3])
	}
}

func TestSocksHandshakeReportsMethodMismatch(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	go func() {
		conn, err := listener.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		greeting := make([]byte, 3)
		_, _ = io.ReadFull(conn, greeting)
		_, _ = conn.Write([]byte{socksVersion, 0xff})
	}()
	_, err = (socksClient{address: listener.Addr().String(), handshakeTimeout: time.Second}).dialTCP(context.Background(), netip.MustParseAddrPort("203.0.113.8:443"))
	if err == nil || !errors.Is(err, errSocksMethodUnavailable) {
		t.Fatalf("handshake error = %v, want method mismatch", err)
	}
}

func startSocksUDPServer(t *testing.T, changeSource bool) (string, func()) {
	t.Helper()
	udp, err := net.ListenUDP("udp", &net.UDPAddr{IP: net.IPv4(127, 0, 0, 1)})
	if err != nil {
		t.Fatal(err)
	}
	tcpListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		udp.Close()
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		conn, err := tcpListener.Accept()
		if err != nil {
			return
		}
		defer conn.Close()
		command, _, err := acceptSocksRequest(bufio.NewReader(conn), conn)
		if err != nil || command != socksUDPAssociate {
			return
		}
		relay := udp.LocalAddr().(*net.UDPAddr).AddrPort()
		if writeSocksSuccess(conn, relay) != nil {
			return
		}
		<-ctx.Done()
	}()
	go func() {
		packet := make([]byte, maxUDPPacket+22)
		for {
			n, peer, err := udp.ReadFromUDP(packet)
			if err != nil {
				return
			}
			response := append([]byte(nil), packet[:n]...)
			if changeSource && len(response) > 7 && response[3] == socksIPv4 {
				response[4] ^= 1
			}
			_, _ = udp.WriteToUDP(response, peer)
		}
	}()
	return tcpListener.Addr().String(), func() {
		cancel()
		_ = tcpListener.Close()
		_ = udp.Close()
	}
}

func acceptSocksRequest(reader *bufio.Reader, writer io.Writer) (byte, netip.AddrPort, error) {
	var greeting [3]byte
	if _, err := io.ReadFull(reader, greeting[:]); err != nil {
		return 0, netip.AddrPort{}, err
	}
	if err := writeFull(writer, []byte{socksVersion, socksNoAuth}); err != nil {
		return 0, netip.AddrPort{}, err
	}
	var header [3]byte
	if _, err := io.ReadFull(reader, header[:]); err != nil {
		return 0, netip.AddrPort{}, err
	}
	address, err := readSocksAddr(reader)
	if err != nil {
		return 0, netip.AddrPort{}, err
	}
	parsed, err := netip.ParseAddrPort(net.JoinHostPort(address.host, netPort(address.port)))
	return header[1], parsed, err
}

func writeSocksSuccess(writer io.Writer, address netip.AddrPort) error {
	encoded, err := appendSocksAddr([]byte{socksVersion, socksSucceeded, 0}, address)
	if err != nil {
		return err
	}
	return writeFull(writer, encoded)
}

func netPort(port uint16) string {
	return strconv.Itoa(int(port))
}
