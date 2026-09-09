package socks5

import (
	"bytes"
	"encoding/binary"
	"strings"
	"testing"
)

// connectRequest is the request alone, with no preceding greeting, so tests
// can put a different method negotiation in front of it.
func connectRequest(atyp byte, address []byte, port uint16) []byte {
	b := []byte{5, 1, 0, atyp}
	b = append(b, address...)
	var p [2]byte
	binary.BigEndian.PutUint16(p[:], port)
	return append(b, p[:]...)
}

func requestBytes(atyp byte, address []byte, port uint16) []byte {
	return append([]byte{5, 1, methodNone}, connectRequest(atyp, address, port)...)
}

// readWriter keeps the reply stream separate from the request stream so a test
// can assert on exactly what the negotiation wrote.
type readWriter struct {
	r *bytes.Buffer
	w bytes.Buffer
}

func (rw *readWriter) Read(p []byte) (int, error)  { return rw.r.Read(p) }
func (rw *readWriter) Write(p []byte) (int, error) { return rw.w.Write(p) }

func TestReadDomainConnect(t *testing.T) {
	b := requestBytes(3, append([]byte{11}, []byte("example.com")...), 443)
	rw := bytes.NewBuffer(b)
	req, err := ReadRequest(rw, nil)
	if err != nil {
		t.Fatal(err)
	}
	if req.Destination != "example.com:443" {
		t.Fatalf("destination %q", req.Destination)
	}
	reply := rw.Bytes()
	if len(reply) != 2 || reply[0] != 5 || reply[1] != 0 {
		t.Fatalf("method reply %v", reply)
	}
}

func TestWriteMethodUnavailableUsesGreetingResponse(t *testing.T) {
	var out bytes.Buffer
	if err := WriteMethodUnavailable(&out); err != nil {
		t.Fatal(err)
	}
	if got, want := out.Bytes(), []byte{version5, methodNoneAcceptable}; !bytes.Equal(got, want) {
		t.Fatalf("method rejection = %v, want %v", got, want)
	}
}

func TestRejectUnsupportedCommand(t *testing.T) {
	b := []byte{5, 1, 0, 5, 2, 0, 1, 127, 0, 0, 1, 0, 53}
	rw := bytes.NewBuffer(b)
	if _, err := ReadRequest(rw, nil); err == nil {
		t.Fatal("expected rejection")
	}
	got := rw.Bytes()
	if len(got) < 10 || got[len(got)-9] != ReplyCommandNotSupported {
		t.Fatalf("unexpected reply %v", got)
	}
}

func TestReadUDPAssociateAllowsZeroBindPort(t *testing.T) {
	b := []byte{5, 1, 0, 5, CommandUDPAssociate, 0, 1, 0, 0, 0, 0, 0, 0}
	req, err := ReadRequest(bytes.NewBuffer(b), nil)
	if err != nil {
		t.Fatal(err)
	}
	if req.Command != CommandUDPAssociate || req.Destination != "0.0.0.0:0" {
		t.Fatalf("unexpected request %#v", req)
	}
}

func TestUDPDatagramRoundTrip(t *testing.T) {
	payload := []byte("dns-payload")
	var b bytes.Buffer
	if err := WriteUDPDatagram(&b, "example.com:53", payload); err != nil {
		t.Fatal(err)
	}
	datagram, err := ReadUDPDatagram(b.Bytes())
	if err != nil {
		t.Fatal(err)
	}
	if datagram.Destination != "example.com:53" || !bytes.Equal(datagram.Payload, payload) {
		t.Fatalf("got destination=%q payload=%q", datagram.Destination, datagram.Payload)
	}
}

func TestUDPDatagramRejectsFragmentsAndMalformedAddresses(t *testing.T) {
	if _, err := ReadUDPDatagram([]byte{0, 0, 1, 1, 127, 0, 0, 1, 0, 53, 1}); err == nil {
		t.Fatal("fragmented datagram accepted")
	}
	if _, err := ReadUDPDatagram([]byte{0, 0, 0, 3, 0, 0, 0, 53, 1}); err == nil {
		t.Fatal("empty domain accepted")
	}
}

// authGreeting builds a complete username/password exchange followed by one
// CONNECT, which is what a configured consumer such as v2rayNG or mihomo
// actually sends to an export-mode listener.
func authGreeting(username, password string, request []byte) []byte {
	out := []byte{5, 1, methodUserPass, userPassVersion, byte(len(username))}
	out = append(out, username...)
	out = append(out, byte(len(password)))
	out = append(out, password...)
	return append(out, request...)
}

func TestUserPassAuthenticationAcceptsMatchingCredentials(t *testing.T) {
	connect := connectRequest(1, []byte{127, 0, 0, 1}, 8080)
	rw := &readWriter{r: bytes.NewBuffer(authGreeting("user", "secret", connect))}
	req, err := ReadRequest(rw, &Credentials{Username: "user", Password: "secret"})
	if err != nil {
		t.Fatalf("read request: %v", err)
	}
	if req.Destination != "127.0.0.1:8080" {
		t.Fatalf("destination = %q", req.Destination)
	}
	// The method selection and the sub-negotiation success both precede the
	// reply, and a client that does not see them will not send the request.
	if got := rw.w.Bytes(); !bytes.Equal(got, []byte{5, methodUserPass, userPassVersion, userPassSuccess}) {
		t.Fatalf("negotiation wrote %v", got)
	}
}

func TestUserPassAuthenticationRejectsWrongCredentials(t *testing.T) {
	connect := connectRequest(1, []byte{127, 0, 0, 1}, 8080)
	for _, bad := range []struct{ user, pass string }{
		{"user", "wrong"},
		{"wrong", "secret"},
		{"", "secret"},
	} {
		rw := &readWriter{r: bytes.NewBuffer(authGreeting(bad.user, bad.pass, connect))}
		if _, err := ReadRequest(rw, &Credentials{Username: "user", Password: "secret"}); err == nil {
			t.Fatalf("accepted %q/%q", bad.user, bad.pass)
		}
		// A rejected client has to be told it was rejected. Closing the
		// connection instead makes a wrong password look like a broken tunnel.
		if got := rw.w.Bytes(); len(got) < 2 || got[len(got)-1] != userPassFailure {
			t.Fatalf("rejection wrote %v", got)
		}
	}
}

// An exported listener shares loopback with every other app on the device, so
// a client offering no-authentication must not be able to negotiate the
// requirement away.
func TestConfiguredAuthenticationRejectsNoAuthClient(t *testing.T) {
	connect := connectRequest(1, []byte{127, 0, 0, 1}, 8080)
	greeting := append([]byte{5, 1, methodNone}, connect...)
	rw := &readWriter{r: bytes.NewBuffer(greeting)}
	if _, err := ReadRequest(rw, &Credentials{Username: "user", Password: "secret"}); err == nil {
		t.Fatal("accepted a client that offered only no-authentication")
	}
	if got := rw.w.Bytes(); !bytes.Equal(got, []byte{5, methodNoneAcceptable}) {
		t.Fatalf("wrote %v", got)
	}
}

// The unauthenticated listener is the desktop and packet-tunnel default, and
// must keep rejecting a client that offers only username/password rather than
// falling through to an unauthenticated request.
func TestUnauthenticatedListenerRejectsUserPassOnlyClient(t *testing.T) {
	rw := &readWriter{r: bytes.NewBuffer([]byte{5, 1, methodUserPass})}
	if _, err := ReadRequest(rw, nil); err == nil {
		t.Fatal("accepted a client that offered only username/password")
	}
}

func TestCredentialsValidateBounds(t *testing.T) {
	if err := (*Credentials)(nil).Validate(); err != nil {
		t.Fatalf("nil credentials must be valid: %v", err)
	}
	if err := (&Credentials{Username: "", Password: "p"}).Validate(); err == nil {
		t.Fatal("accepted an empty username")
	}
	long := strings.Repeat("a", maxUserPassFieldLength+1)
	if err := (&Credentials{Username: long, Password: "p"}).Validate(); err == nil {
		t.Fatal("accepted an over-long username")
	}
	if err := (&Credentials{Username: "u", Password: long}).Validate(); err == nil {
		t.Fatal("accepted an over-long password")
	}
}
