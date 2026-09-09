package session

import (
	"encoding/binary"
	"errors"
	"fmt"
	"net"
)

// UDPAssociationMarker is the bounded Open payload used to distinguish a
// SOCKS UDP-associate session from a TCP destination. It is intentionally not
// a valid host:port string, so a future TCP destination cannot collide with
// the UDP control plane.
var UDPAssociationMarker = []byte{'W', 'O', 'U', 'D', 1}

const (
	packetDestinationLength = 2
	packetHeaderLength      = packetDestinationLength
	maxUDPPayload           = 65507
)

// These numbers together fix the largest frame protocol 1 can require a
// receiver to accept, which is why protocol.MaxPayload is the size it is. They
// are exported so the conformance vectors can state that relationship rather
// than leave it a coincidence between two packages.
const (
	// MaxDestinationLength bounds the canonical host:port a frame may name.
	MaxDestinationLength = maxDestinationLength
	// MaxUDPDatagram is the largest datagram a PACKET frame may carry: 65535
	// less the 20-byte IP and 8-byte UDP headers.
	MaxUDPDatagram = maxUDPPayload
	// PacketDestinationPrefix is the width of a PACKET payload's leading
	// destination-length field.
	PacketDestinationPrefix = packetDestinationLength
	// MaxPacketPayload is the largest legal PACKET payload, and therefore the
	// floor under any receiver's frame payload limit.
	MaxPacketPayload = PacketDestinationPrefix + MaxDestinationLength + MaxUDPDatagram
)

func IsUDPAssociation(payload []byte) bool {
	return string(payload) == string(UDPAssociationMarker)
}

// EncodeUDPPacket stores one canonical target and one UDP payload. The
// destination length is explicit and bounded so malformed packets can be
// rejected before a resolver or socket operation is attempted.
func EncodeUDPPacket(destination string, payload []byte) ([]byte, error) {
	destinationBytes, err := EncodeDestination(destination)
	if err != nil {
		return nil, err
	}
	if len(payload) > maxUDPPayload {
		return nil, fmt.Errorf("UDP payload exceeds %d bytes", maxUDPPayload)
	}
	if len(destinationBytes) > 65535 || len(destinationBytes)+packetHeaderLength+len(payload) > maxUDPPayload+maxDestinationLength+packetHeaderLength {
		return nil, errors.New("UDP packet exceeds bounded payload")
	}
	out := make([]byte, packetHeaderLength+len(destinationBytes)+len(payload))
	binary.BigEndian.PutUint16(out[:packetDestinationLength], uint16(len(destinationBytes)))
	copy(out[packetHeaderLength:], destinationBytes)
	copy(out[packetHeaderLength+len(destinationBytes):], payload)
	return out, nil
}

func DecodeUDPPacket(payload []byte) (destination string, packet []byte, err error) {
	if len(payload) < packetHeaderLength+1 {
		return "", nil, errors.New("UDP packet is truncated")
	}
	destinationLength := int(binary.BigEndian.Uint16(payload[:packetDestinationLength]))
	if destinationLength == 0 || destinationLength > maxDestinationLength || packetHeaderLength+destinationLength > len(payload) {
		return "", nil, errors.New("invalid UDP destination length")
	}
	destinationBytes := payload[packetHeaderLength : packetHeaderLength+destinationLength]
	destination, err = DecodeDestination(destinationBytes)
	if err != nil {
		return "", nil, fmt.Errorf("invalid UDP destination: %w", err)
	}
	packet = payload[packetHeaderLength+destinationLength:]
	if len(packet) > maxUDPPayload {
		return "", nil, errors.New("invalid UDP payload length")
	}
	return destination, append([]byte(nil), packet...), nil
}

// DestinationFromUDPAddr canonicalizes an address received from a remote
// datagram socket. UDP replies always use numeric addresses, avoiding a DNS
// lookup on the client side and preventing a response from being redirected
// by later DNS changes.
func DestinationFromUDPAddr(addr *net.UDPAddr) (string, error) {
	if addr == nil || addr.Port < 1 || addr.Port > 65535 || addr.IP == nil {
		return "", errors.New("invalid UDP source address")
	}
	return net.JoinHostPort(addr.IP.String(), fmt.Sprintf("%d", addr.Port)), nil
}

// UDPResumeMarker opens a UDP association whose remote relay may be retained
// and reclaimed. Its distinct marker keeps the parser unambiguous with TCP
// destinations and ordinary UDP association opens.
var UDPResumeMarker = []byte{'W', 'O', 'U', 'D', 2}

// UDPResumeTokenSize is the width of the token naming a retained relay. It is
// an unguessable, single-use handle in addition to principal binding, so a
// different association owned by the same device cannot claim it by accident.
const UDPResumeTokenSize = 16

// EncodeUDPResumeOpen builds the Open payload for a resumable association. A
// nil token asks for a fresh relay and a token to name it by; otherwise the
// token names the relay to reclaim.
func EncodeUDPResumeOpen(token []byte) ([]byte, error) {
	if len(token) != 0 && len(token) != UDPResumeTokenSize {
		return nil, fmt.Errorf("UDP resume token is %d bytes, want %d", len(token), UDPResumeTokenSize)
	}
	return append(append([]byte(nil), UDPResumeMarker...), token...), nil
}

// DecodeUDPResumeOpen reports whether the payload opens a resumable
// association, and which relay it asks to reclaim. A nil token with ok set is
// a request for a fresh one.
func DecodeUDPResumeOpen(payload []byte) (token []byte, ok bool) {
	if len(payload) < len(UDPResumeMarker) || string(payload[:len(UDPResumeMarker)]) != string(UDPResumeMarker) {
		return nil, false
	}
	rest := payload[len(UDPResumeMarker):]
	switch len(rest) {
	case 0:
		return nil, true
	case UDPResumeTokenSize:
		return append([]byte(nil), rest...), true
	default:
		return nil, false
	}
}

// EncodeUDPResumeGrant is the OPEN_OK payload answering a resumable open: the
// token naming this association's relay from now on, and whether the relay is
// the one that was asked for or a fresh one.
//
// The token is reissued on every open, including a successful resume. A token
// that survived its own use would let a lane that failed once be replayed
// against every later relay the association had.
func EncodeUDPResumeGrant(resumed bool, token [UDPResumeTokenSize]byte) []byte {
	out := make([]byte, 1, 1+UDPResumeTokenSize)
	if resumed {
		out[0] = 1
	}
	return append(out, token[:]...)
}

// DecodeUDPResumeGrant parses that answer.
func DecodeUDPResumeGrant(payload []byte) (resumed bool, token [UDPResumeTokenSize]byte, ok bool) {
	if len(payload) != 1+UDPResumeTokenSize || payload[0] > 1 {
		return false, token, false
	}
	copy(token[:], payload[1:])
	return payload[0] == 1, token, true
}
