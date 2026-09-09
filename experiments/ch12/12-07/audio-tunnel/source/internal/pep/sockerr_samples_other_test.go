//go:build !windows

package pep

import "syscall"

// The codes a Unix socket reports for each condition the classifiers name.
var (
	transientRouteWriteSamples = []errnoSample{
		{"network down", syscall.ENETDOWN},
		{"network unreachable", syscall.ENETUNREACH},
		{"host down", syscall.EHOSTDOWN},
		{"host unreachable", syscall.EHOSTUNREACH},
		{"send queue full", syscall.ENOBUFS},
	}
	staleSourceWriteSample  = errnoSample{"source address gone", syscall.EADDRNOTAVAIL}
	unreachableRouteSamples = []errnoSample{
		{"network down", syscall.ENETDOWN},
		{"network unreachable", syscall.ENETUNREACH},
		{"host down", syscall.EHOSTDOWN},
		{"host unreachable", syscall.EHOSTUNREACH},
	}
	halfCloseSamples = []errnoSample{
		{"not connected", syscall.ENOTCONN},
		{"broken pipe", syscall.EPIPE},
		{"reset", syscall.ECONNRESET},
		{"aborted", syscall.ECONNABORTED},
	}
	destinationCloseSamples = []errnoSample{
		{"reset", syscall.ECONNRESET},
		{"aborted", syscall.ECONNABORTED},
		{"not connected", syscall.ENOTCONN},
	}
	// permanentSocketError must stay fatal. EBADF is a real error number on
	// both platforms, and on neither does it describe a route.
	// injectedRouteError is the code fault injection uses to stand in for a
	// route that has gone away, so the injected error is one a socket on this
	// platform really reports.
	injectedRouteError   = syscall.ENETUNREACH
	permanentSocketError = syscall.EBADF
)
