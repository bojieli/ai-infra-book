package extproxy

import (
	"fmt"
	"net"
	"path/filepath"
	"strconv"
)

// singBoxLaunch answers the two questions in Launch for every sing-box stack:
// one JSON configuration per side, and "run -c" over each of them.
func singBoxLaunch(cfg Config) (Launch, error) {
	server, client, err := buildConfigs(cfg)
	if err != nil {
		return Launch{}, err
	}
	serverPath := filepath.Join(cfg.WorkDir, string(cfg.Kind)+"-server.json")
	clientPath := filepath.Join(cfg.WorkDir, string(cfg.Kind)+"-client.json")
	return Launch{
		Files:      map[string]any{serverPath: server, clientPath: client},
		ServerArgs: []string{"run", "-c", serverPath},
		ClientArgs: []string{"run", "-c", clientPath},
	}, nil
}

// The configurations below are sing-box's schema. They are written as plain
// maps rather than typed structs because the schema is the other project's and
// changes between releases; a map keeps the failure visible in that project's
// own validation output rather than silently dropping a field.

func buildConfigs(cfg Config) (server, client any, err error) {
	serverHost, serverPort, err := splitHostPort(cfg.ServerListen)
	if err != nil {
		return nil, nil, fmt.Errorf("server listen: %w", err)
	}
	remoteHost, remotePort, err := splitHostPort(cfg.ClientRemote)
	if err != nil {
		return nil, nil, fmt.Errorf("client remote: %w", err)
	}
	socksHost, socksPort, err := splitHostPort(cfg.SOCKSListen)
	if err != nil {
		return nil, nil, fmt.Errorf("socks listen: %w", err)
	}

	serverTLS := map[string]any{
		"enabled":          true,
		"server_name":      "queqiao.test",
		"certificate_path": cfg.CertificatePath,
		"key_path":         cfg.KeyPath,
	}
	// The client trusts exactly the server's certificate, so the measurement
	// never needs a verification bypass.
	clientTLS := map[string]any{
		"enabled":          true,
		"server_name":      "queqiao.test",
		"certificate_path": cfg.CertificatePath,
	}

	var inbound, outbound map[string]any
	switch cfg.Kind {
	case TUIC:
		serverTLS["alpn"] = []string{"h3"}
		clientTLS["alpn"] = []string{"h3"}
		inbound = map[string]any{
			"type": "tuic", "tag": "in", "listen": serverHost, "listen_port": serverPort,
			"users":              []any{map[string]any{"name": "bench", "uuid": cfg.UUID, "password": cfg.Credential}},
			"congestion_control": cfg.Congestion,
			"auth_timeout":       "5s",
			"tls":                serverTLS,
		}
		outbound = map[string]any{
			"type": "tuic", "tag": "out", "server": remoteHost, "server_port": remotePort,
			"uuid": cfg.UUID, "password": cfg.Credential,
			"congestion_control": cfg.Congestion,
			"udp_relay_mode":     "native",
			"tls":                clientTLS,
		}
	case Hysteria2:
		serverTLS["alpn"] = []string{"h3"}
		clientTLS["alpn"] = []string{"h3"}
		inbound = map[string]any{
			"type": "hysteria2", "tag": "in", "listen": serverHost, "listen_port": serverPort,
			"users": []any{map[string]any{"name": "bench", "password": cfg.Credential}},
			"tls":   serverTLS,
		}
		outbound = map[string]any{
			"type": "hysteria2", "tag": "out", "server": remoteHost, "server_port": remotePort,
			"password": cfg.Credential,
			"tls":      clientTLS,
		}
	case VLESSTCP, VLESSWebSocket:
		inbound = map[string]any{
			"type": "vless", "tag": "in", "listen": serverHost, "listen_port": serverPort,
			"users": []any{map[string]any{"name": "bench", "uuid": cfg.UUID}},
			"tls":   serverTLS,
		}
		outbound = map[string]any{
			"type": "vless", "tag": "out", "server": remoteHost, "server_port": remotePort,
			"uuid": cfg.UUID,
			"tls":  clientTLS,
		}
		if cfg.Kind == VLESSWebSocket {
			transport := map[string]any{"type": "ws", "path": "/queqiao"}
			inbound["transport"] = transport
			outbound["transport"] = transport
		}
	default:
		return nil, nil, fmt.Errorf("unsupported transport %q", cfg.Kind)
	}

	server = map[string]any{
		"log":       map[string]any{"level": "error", "timestamp": false},
		"inbounds":  []any{inbound},
		"outbounds": []any{map[string]any{"type": "direct", "tag": "direct"}},
	}
	client = map[string]any{
		"log": map[string]any{"level": "error", "timestamp": false},
		"inbounds": []any{map[string]any{
			"type": "socks", "tag": "socks", "listen": socksHost, "listen_port": socksPort,
		}},
		"outbounds": []any{outbound},
	}
	return server, client, nil
}

func splitHostPort(address string) (string, int, error) {
	host, portText, err := net.SplitHostPort(address)
	if err != nil {
		return "", 0, err
	}
	port, err := strconv.Atoi(portText)
	if err != nil || port <= 0 || port > 65535 {
		return "", 0, fmt.Errorf("invalid port %q", portText)
	}
	if host == "" {
		host = "127.0.0.1"
	}
	return host, port, nil
}
