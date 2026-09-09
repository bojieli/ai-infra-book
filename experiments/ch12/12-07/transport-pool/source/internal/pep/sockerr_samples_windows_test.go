//go:build windows

package pep

import "golang.org/x/sys/windows"

// The codes Winsock reports for each condition the classifiers name. These are
// the WSA values, not the syscall constants of the same name: on Windows those
// are synthetic APPLICATION_ERROR values no socket returns, which is the whole
// reason the classifiers are build-tagged.
var (
	transientRouteWriteSamples = []errnoSample{
		{"network down", windows.WSAENETDOWN},
		{"network unreachable", windows.WSAENETUNREACH},
		{"host down", windows.WSAEHOSTDOWN},
		{"host unreachable", windows.WSAEHOSTUNREACH},
		{"send queue full", windows.WSAENOBUFS},
	}
	staleSourceWriteSample  = errnoSample{"source address gone", windows.WSAEADDRNOTAVAIL}
	unreachableRouteSamples = []errnoSample{
		{"network down", windows.WSAENETDOWN},
		{"network unreachable", windows.WSAENETUNREACH},
		{"host down", windows.WSAEHOSTDOWN},
		{"host unreachable", windows.WSAEHOSTUNREACH},
	}
	halfCloseSamples = []errnoSample{
		{"not connected", windows.WSAENOTCONN},
		{"already shut down", windows.WSAESHUTDOWN},
		{"reset", windows.WSAECONNRESET},
		{"aborted", windows.WSAECONNABORTED},
		{"netname deleted", windows.ERROR_NETNAME_DELETED},
	}
	destinationCloseSamples = []errnoSample{
		{"reset", windows.WSAECONNRESET},
		{"aborted", windows.WSAECONNABORTED},
		{"not connected", windows.WSAENOTCONN},
		{"netname deleted", windows.ERROR_NETNAME_DELETED},
	}
	// injectedRouteError is the code fault injection uses to stand in for a
	// route that has gone away, so the injected error is one a socket on this
	// platform really reports.
	injectedRouteError   = windows.WSAENETUNREACH
	permanentSocketError = windows.WSAEBADF
)
