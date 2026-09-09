package mobilecore

import (
	"errors"
	"io"
	"sync"
)

// PacketIO is the public packet-flow boundary used by Apple NetworkExtension.
// ReadPacket blocks until one complete IP packet is available or returns an
// empty slice after Close. WritePacket must synchronously copy the packet and
// return false if the platform packet flow has closed.
type PacketIO interface {
	ReadPacket() []byte
	WritePacket(packet []byte) bool
	Close()
}

type callbackPacketDevice struct {
	packetIO PacketIO
	close    sync.Once
}

func (d *callbackPacketDevice) Read(buffer []byte) (n int, err error) {
	defer func() {
		if recovered := recover(); recovered != nil {
			n, err = 0, errors.New("platform packet reader panicked")
		}
	}()
	packet := d.packetIO.ReadPacket()
	if len(packet) == 0 {
		return 0, io.EOF
	}
	if len(packet) > len(buffer) {
		return 0, io.ErrShortBuffer
	}
	return copy(buffer, packet), nil
}

func (d *callbackPacketDevice) Write(packet []byte) (n int, err error) {
	defer func() {
		if recovered := recover(); recovered != nil {
			n, err = 0, errors.New("platform packet writer panicked")
		}
	}()
	if !d.packetIO.WritePacket(packet) {
		return 0, io.ErrClosedPipe
	}
	return len(packet), nil
}

func (d *callbackPacketDevice) Close() error {
	d.close.Do(func() {
		defer func() { _ = recover() }()
		d.packetIO.Close()
	})
	return nil
}
