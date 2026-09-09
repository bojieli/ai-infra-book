# protocol-handshake-declared-packet-graph

这是声明数据包和消息依赖的计算；包长不是官方测量值，时间不是真实协议实测。

状态：`complete`。

## 业务与握手时刻

时间单位为秒，保留精确分数；不存在的完整响应不会以最后消息时刻替代。

| 事件 | 精确时刻（s） |
| --- | ---: |
| syn_received | 6253/125000 |
| syn_ack_received | 31259/312500 |
| client_hello_received | 23477/156250 |
| server_flight_received | 62649/312500 |
| client_peer_authenticated | 62649/312500 |
| client_finished_received | 78289/312500 |
| server_handshake_complete | 78289/312500 |
| request_received | 156623/625000 |
| accepted_request | 156623/625000 |
| application_execution | 156623/625000 |
| response_received | 194137/625000 |
| complete_response | 194137/625000 |

## 有效业务与已建模字节

| 数量 | 值 |
| --- | ---: |
| request_payload_sent_bytes | 100 |
| accepted_unique_request_bytes | 100 |
| rejected_early_payload_bytes | 0 |
| application_execution_count | 1 |
| delivered_response_payload_bytes | 200 |
| modeled_wire_bytes_by_direction.c2s | 920 |
| modeled_wire_bytes_by_direction.s2c | 3140 |
| last_modeled_arrival | 194137/625000 |

物理字节仅包括本图显式列出的消息，不是包含全部 ACK／控制消息的抓包总量。

## 适用范围

- Declared packet lengths; no encryption or packet capture.
- No HRR, Retry, ticket fallback, background ticket/token issuance, HTTP or HTTP/3 SETTINGS state machine.
- No loss, congestion, flow-control, TCP data ACK, or general QUIC ACK/PTO simulation.
- Optional immediate ACK of second server Handshake datagram only; a blocked graph is not a claim of protocol deadlock.
- IPv4 without options; QUIC wire adds 20B IP + 8B UDP; TCP declarations already include IP/TCP.
- Reused connection starts idle with sufficient flow/congestion credit; no inherited traffic.
- Immediate early execution is an explicit application policy and conveys no replay/exactly-once guarantee.

## 固定官方来源

- [RFC9293](https://www.rfc-editor.org/rfc/rfc9293.txt)：`6d9ac8be4b0286f8c3d337addf442b2eb6a9b14e1366594ea7fbc273f93dc2d9`。
- [RFC8446](https://www.rfc-editor.org/rfc/rfc8446.txt)：`47871bc8820a2c3b6ea89f061055577058862cf543686b82d10131239702b3bd`。
- [RFC9000](https://www.rfc-editor.org/rfc/rfc9000.txt)：`f88aae47f8b18e102024916e975e919201d8dde689cba79b01079eaedd402e22`。
- [RFC9001](https://www.rfc-editor.org/rfc/rfc9001.txt)：`3bbaecdf5afd278052a2c48348ce118c4ff8d0cf6b9915549858171b3f98a591`。
- [RFC9002](https://www.rfc-editor.org/rfc/rfc9002.txt)：`3a8a54eea1ad5d1c134a548bf15edfa0e21bfb4106dbd7db3c09cace842099af`。
- [RFC5681](https://www.rfc-editor.org/rfc/rfc5681.txt)：`a2d99a2421d5c57b248394f26ba44fc364aa546680fbf10ff0aa7034dad8b87d`。
- [RFC9114](https://www.rfc-editor.org/rfc/rfc9114.txt)：`6b84555c88eeebcf5d2b2e1d9d7b58630abc97ab877b2cf62dee4cd635db34e4`。

## 完整输入与逐包事件

```json
{
  "reference_sources": [
    {
      "file": "sources/protocol-rfc/rfc9293.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc9293.txt",
      "revision": "RFC9293",
      "sha256": "6d9ac8be4b0286f8c3d337addf442b2eb6a9b14e1366594ea7fbc273f93dc2d9"
    },
    {
      "file": "sources/protocol-rfc/rfc8446.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc8446.txt",
      "revision": "RFC8446",
      "sha256": "47871bc8820a2c3b6ea89f061055577058862cf543686b82d10131239702b3bd"
    },
    {
      "file": "sources/protocol-rfc/rfc9000.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc9000.txt",
      "revision": "RFC9000",
      "sha256": "f88aae47f8b18e102024916e975e919201d8dde689cba79b01079eaedd402e22"
    },
    {
      "file": "sources/protocol-rfc/rfc9001.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc9001.txt",
      "revision": "RFC9001",
      "sha256": "3bbaecdf5afd278052a2c48348ce118c4ff8d0cf6b9915549858171b3f98a591"
    },
    {
      "file": "sources/protocol-rfc/rfc9002.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc9002.txt",
      "revision": "RFC9002",
      "sha256": "3a8a54eea1ad5d1c134a548bf15edfa0e21bfb4106dbd7db3c09cace842099af"
    },
    {
      "file": "sources/protocol-rfc/rfc5681.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc5681.txt",
      "revision": "RFC5681",
      "sha256": "a2d99a2421d5c57b248394f26ba44fc364aa546680fbf10ff0aa7034dad8b87d"
    },
    {
      "file": "sources/protocol-rfc/rfc9114.txt",
      "url": "https://www.rfc-editor.org/rfc/rfc9114.txt",
      "revision": "RFC9114",
      "sha256": "6b84555c88eeebcf5d2b2e1d9d7b58630abc97ab877b2cf62dee4cd635db34e4"
    }
  ],
  "calculation": "protocol-handshake-declared-packet-graph",
  "inputs": {
    "protocol": "tcp_tls13",
    "mode": "fresh",
    "valid_psk": true,
    "early_credentials_valid": true,
    "connection_usable": true,
    "address_token_valid": false,
    "server_flight_ack": true,
    "application_early_data_authorized": true,
    "payload_bytes_by_packet": {
      "request": [
        100
      ],
      "early_request": [
        100
      ],
      "response": [
        200
      ]
    },
    "application_policy": "immediate",
    "application_retry_authorized": true,
    "request_payload_bytes": 100,
    "response_payload_bytes": 200,
    "model_seconds": "0.01",
    "c2s_bits_per_second": 20000000,
    "s2c_bits_per_second": 100000000,
    "c2s_propagation_seconds": "0.05",
    "s2c_propagation_seconds": "0.05",
    "packets": {
      "syn": [
        60
      ],
      "syn_ack": [
        60
      ],
      "client_hello": [
        560
      ],
      "server_flight": [
        1400,
        1400
      ],
      "client_finished": [
        120
      ],
      "handshake_ack": [
        80
      ],
      "request": [
        180
      ],
      "early_request": [
        180
      ],
      "response": [
        280
      ]
    }
  },
  "status": "complete",
  "milestones": {
    "syn_received": "6253/125000",
    "syn_ack_received": "31259/312500",
    "client_hello_received": "23477/156250",
    "server_flight_received": "62649/312500",
    "client_peer_authenticated": "62649/312500",
    "client_finished_received": "78289/312500",
    "server_handshake_complete": "78289/312500",
    "request_received": "156623/625000",
    "accepted_request": "156623/625000",
    "application_execution": "156623/625000",
    "response_received": "194137/625000",
    "complete_response": "194137/625000"
  },
  "transmissions": [
    {
      "flight": "syn",
      "packet": 0,
      "direction": "c2s",
      "declared_bytes": 60,
      "wire_bytes": 60,
      "ready": "0",
      "start": "0",
      "end": "3/125000",
      "arrival": "6253/125000"
    },
    {
      "flight": "syn_ack",
      "packet": 0,
      "direction": "s2c",
      "declared_bytes": 60,
      "wire_bytes": 60,
      "ready": "6253/125000",
      "start": "6253/125000",
      "end": "7817/156250",
      "arrival": "31259/312500"
    },
    {
      "flight": "client_hello",
      "packet": 0,
      "direction": "c2s",
      "declared_bytes": 560,
      "wire_bytes": 560,
      "ready": "31259/312500",
      "start": "31259/312500",
      "end": "31329/312500",
      "arrival": "23477/156250"
    },
    {
      "flight": "server_flight",
      "packet": 0,
      "direction": "s2c",
      "declared_bytes": 1400,
      "wire_bytes": 1400,
      "ready": "23477/156250",
      "start": "23477/156250",
      "end": "46989/312500",
      "arrival": "31307/156250"
    },
    {
      "flight": "server_flight",
      "packet": 1,
      "direction": "s2c",
      "declared_bytes": 1400,
      "wire_bytes": 1400,
      "ready": "23477/156250",
      "start": "46989/312500",
      "end": "11756/78125",
      "arrival": "62649/312500"
    },
    {
      "flight": "client_finished",
      "packet": 0,
      "direction": "c2s",
      "declared_bytes": 120,
      "wire_bytes": 120,
      "ready": "62649/312500",
      "start": "62649/312500",
      "end": "15666/78125",
      "arrival": "78289/312500"
    },
    {
      "flight": "request",
      "packet": 0,
      "direction": "c2s",
      "declared_bytes": 180,
      "wire_bytes": 180,
      "ready": "62649/312500",
      "start": "15666/78125",
      "end": "125373/625000",
      "arrival": "156623/625000"
    },
    {
      "flight": "response",
      "packet": 0,
      "direction": "s2c",
      "declared_bytes": 280,
      "wire_bytes": 280,
      "ready": "162873/625000",
      "start": "162873/625000",
      "end": "162887/625000",
      "arrival": "194137/625000"
    }
  ],
  "anti_amplification_blocks": [],
  "pending_packets": [],
  "summary": {
    "request_payload_sent_bytes": 100,
    "accepted_unique_request_bytes": 100,
    "rejected_early_payload_bytes": 0,
    "application_execution_count": 1,
    "delivered_response_payload_bytes": 200,
    "modeled_wire_bytes_by_direction": {
      "c2s": 920,
      "s2c": 3140
    },
    "last_modeled_arrival": "194137/625000"
  },
  "limitations": [
    "Declared packet lengths; no encryption or packet capture.",
    "No HRR, Retry, ticket fallback, background ticket/token issuance, HTTP or HTTP/3 SETTINGS state machine.",
    "No loss, congestion, flow-control, TCP data ACK, or general QUIC ACK/PTO simulation.",
    "Optional immediate ACK of second server Handshake datagram only; a blocked graph is not a claim of protocol deadlock.",
    "IPv4 without options; QUIC wire adds 20B IP + 8B UDP; TCP declarations already include IP/TCP.",
    "Reused connection starts idle with sufficient flow/congestion credit; no inherited traffic.",
    "Immediate early execution is an explicit application policy and conveys no replay/exactly-once guarantee."
  ]
}
```
