//go:build linux

package userfaultfd

// https://docs.kernel.org/admin-guide/mm/userfaultfd.html
// https://man7.org/linux/man-pages/man2/userfaultfd.2.html
// https://github.com/torvalds/linux/blob/master/fs/userfaultfd.c
// https://github.com/loopholelabs/userfaultfd-go/blob/main/pkg/constants/cgo.go

/*
#include <sys/syscall.h>
#include <fcntl.h>
#include <linux/userfaultfd.h>
#include <sys/ioctl.h>

struct uffd_pagefault {
	__u64 flags;
	__u64 address;
	__u32 ptid;
};

#ifndef UFFD_FEATURE_WP_ASYNC
#define UFFD_FEATURE_WP_ASYNC (1 << 15)
#endif

struct uffd_remove {
	__u64 start;
	__u64 end;
};
*/
import "C"

import (
	"errors"
	"fmt"
	"runtime"
	"syscall"
	"unsafe"
)

const (
	NR_userfaultfd = C.__NR_userfaultfd

	UFFD_API = C.UFFD_API

	UFFD_EVENT_PAGEFAULT = C.UFFD_EVENT_PAGEFAULT
	UFFD_EVENT_REMOVE    = C.UFFD_EVENT_REMOVE

	UFFDIO_REGISTER_MODE_MISSING = C.UFFDIO_REGISTER_MODE_MISSING
	UFFDIO_REGISTER_MODE_WP      = C.UFFDIO_REGISTER_MODE_WP

	UFFDIO_COPY_MODE_WP       = C.UFFDIO_COPY_MODE_WP
	UFFDIO_COPY_MODE_DONTWAKE = C.UFFDIO_COPY_MODE_DONTWAKE

	UFFDIO_WRITEPROTECT_MODE_WP = C.UFFDIO_WRITEPROTECT_MODE_WP

	UFFDIO_ZEROPAGE_MODE_DONTWAKE = C.UFFDIO_ZEROPAGE_MODE_DONTWAKE

	UFFDIO_API          = C.UFFDIO_API
	UFFDIO_REGISTER     = C.UFFDIO_REGISTER
	UFFDIO_UNREGISTER   = C.UFFDIO_UNREGISTER
	UFFDIO_COPY         = C.UFFDIO_COPY
	UFFDIO_ZEROPAGE     = C.UFFDIO_ZEROPAGE
	UFFDIO_WRITEPROTECT = C.UFFDIO_WRITEPROTECT
	UFFDIO_WAKE         = C.UFFDIO_WAKE

	UFFD_PAGEFAULT_FLAG_WRITE = C.UFFD_PAGEFAULT_FLAG_WRITE
	UFFD_PAGEFAULT_FLAG_MINOR = C.UFFD_PAGEFAULT_FLAG_MINOR
	UFFD_PAGEFAULT_FLAG_WP    = C.UFFD_PAGEFAULT_FLAG_WP

	UFFD_FEATURE_MISSING_HUGETLBFS = C.UFFD_FEATURE_MISSING_HUGETLBFS
	UFFD_FEATURE_EVENT_REMOVE      = C.UFFD_FEATURE_EVENT_REMOVE
	UFFD_FEATURE_WP_ASYNC          = C.UFFD_FEATURE_WP_ASYNC
)

type (
	CULong = C.ulonglong
	CUChar = C.uchar
	CLong  = C.longlong

	UffdMsg       = C.struct_uffd_msg
	UffdPagefault = C.struct_uffd_pagefault
	UffdRemove    = C.struct_uffd_remove

	UffdioAPI          = C.struct_uffdio_api
	UffdioRegister     = C.struct_uffdio_register
	UffdioRange        = C.struct_uffdio_range
	UffdioCopy         = C.struct_uffdio_copy
	UffdioZero         = C.struct_uffdio_zeropage
	UffdioWriteProtect = C.struct_uffdio_writeprotect
)

func newUffdioAPI(api, features CULong) UffdioAPI {
	return UffdioAPI{
		api:      api,
		features: features,
	}
}

func newUffdioRange(start, length CULong) UffdioRange {
	return UffdioRange{
		start: start,
		len:   length,
	}
}

func newUffdioRegister(start, length, mode CULong) UffdioRegister {
	return UffdioRegister{
		_range: newUffdioRange(start, length),
		mode:   mode,
	}
}

func newUffdioCopy(b []byte, address CULong, pagesize CULong, mode CULong, bytesCopied CLong) UffdioCopy {
	return UffdioCopy{
		src:  CULong(uintptr(unsafe.Pointer(&b[0]))),
		dst:  address,
		len:  pagesize,
		mode: mode,
		copy: bytesCopied,
	}
}

func newUffdioZero(address, pagesize, mode CULong) UffdioZero {
	return UffdioZero{
		_range:   newUffdioRange(address, pagesize),
		mode:     mode,
		zeropage: 0,
	}
}

func newUffdioWriteProtect(address, pagesize, mode CULong) UffdioWriteProtect {
	return UffdioWriteProtect{
		_range: newUffdioRange(address, pagesize),
		mode:   mode,
	}
}

func getMsgEvent(msg *UffdMsg) CUChar {
	return msg.event
}

func getMsgArg(msg *UffdMsg) [24]byte {
	return msg.arg
}

func getPagefaultAddress(pagefault *UffdPagefault) uintptr {
	return uintptr(pagefault.address)
}

// Fd is a helper type that wraps uffd fd.
type Fd uintptr

// copy requires UFFDIO_COPY_MODE_WP when both MISSING and WP tracking are active.
func (f Fd) copy(addr, pagesize uintptr, data []byte, mode CULong) error {
	if len(data) == 0 {
		return errors.New("cannot copy from an empty buffer")
	}

	// UFFDIO_COPY hides src as an integer, so keep data pinned while the kernel reads it.
	var pinner runtime.Pinner
	pinner.Pin(&data[0])
	defer pinner.Unpin()

	cpy := newUffdioCopy(data, CULong(addr)&^CULong(pagesize-1), CULong(pagesize), mode, 0)

	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(f), UFFDIO_COPY, uintptr(unsafe.Pointer(&cpy))); errno != 0 {
		return errno
	}

	return classifyCopyResult(int64(cpy.copy), int64(pagesize))
}

// classifyCopyResult turns the UFFDIO_COPY cpy.copy field into a Go error.
// The kernel encodes a negated errno on failure (most commonly -EAGAIN when
// mmap_changing is set), and a short positive count when the copy was
// preempted mid-page (e.g. hugetlb). Both partial outcomes surface as EAGAIN;
// the caller defers the fault for retry on the next poll iteration (via the
// deferred queue + wakeup pipe), the kernel does not auto-redeliver.
func classifyCopyResult(bytesCopied, pagesize int64) error {
	if bytesCopied < 0 {
		return syscall.Errno(-bytesCopied)
	}

	if bytesCopied != pagesize {
		return syscall.EAGAIN
	}

	return nil
}

func (f Fd) zero(addr, pagesize uintptr, mode CULong) error {
	zero := newUffdioZero(CULong(addr)&^CULong(pagesize-1), CULong(pagesize), mode)

	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(f), UFFDIO_ZEROPAGE, uintptr(unsafe.Pointer(&zero))); errno != 0 {
		return errno
	}

	if zero.zeropage != CLong(pagesize) {
		return fmt.Errorf("UFFDIO_ZEROPAGE copied %d bytes, expected %d", zero.zeropage, pagesize)
	}

	return nil
}

// writeProtectRange write-protects (mode UFFDIO_WRITEPROTECT_MODE_WP) or
// unprotects (mode 0) the range [start, start+length), spanning any number of
// pages of size pagesize. start and length must be page-aligned (fault
// addresses need aligning down to their page base first); no masking is
// applied. Clearing protection also wakes any threads blocked on a WP fault
// in the range.
func (f Fd) writeProtectRange(start, length, pagesize uintptr, mode CULong) error {
	if start&(pagesize-1) != 0 {
		return fmt.Errorf("writeProtectRange: start %#x is not aligned to page size %#x", start, pagesize)
	}
	if length&(pagesize-1) != 0 {
		return fmt.Errorf("writeProtectRange: length %#x is not aligned to page size %#x", length, pagesize)
	}

	writeProtect := newUffdioWriteProtect(CULong(start), CULong(length), mode)

	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(f), UFFDIO_WRITEPROTECT, uintptr(unsafe.Pointer(&writeProtect))); errno != 0 {
		return errno
	}

	return nil
}

func (f Fd) wake(addr, pagesize uintptr) error {
	uffdRange := newUffdioRange(CULong(addr)&^CULong(pagesize-1), CULong(pagesize))

	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, uintptr(f), UFFDIO_WAKE, uintptr(unsafe.Pointer(&uffdRange))); errno != 0 {
		return errno
	}

	return nil
}

func (f Fd) close() error {
	return syscall.Close(int(f))
}
