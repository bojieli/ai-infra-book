# quic-early-stream-declared-packets

这是声明数据包和消息依赖的计算；包长不是官方测量值，时间不是真实协议实测。

状态：`await_application_retry_decision`。

## 业务与握手时刻

时间单位为秒，保留精确分数；不存在的完整响应不会以最后消息时刻替代。

| 事件 | 精确时刻（s） |
| --- | ---: |
| client_hello_received | 2 |
| server_flight_received | 5 |
| client_1rtt_keys_installed | 5 |
| server_address_validated | 7 |
| handshake_ack_received | 7 |
| client_finished_received | 8 |

## 有效业务与已建模字节

| 数量 | 值 |
| --- | ---: |
| early_payload_sent_bytes | 4672 |
| one_rtt_payload_sent_bytes | 0 |
| request_payload_sent_bytes | 4672 |
| accepted_unique_request_bytes | 0 |
| discarded_early_payload_bytes | 4672 |
| delivered_response_payload_bytes | 0 |
| application_execution_count | 0 |
| modeled_wire_bytes_by_direction.c2s | 8596 |
| modeled_wire_bytes_by_direction.s2c | 2456 |
| last_modeled_arrival | 8 |

物理字节仅包括本图显式列出的消息，不是包含全部 ACK／控制消息的抓包总量。

## 适用范围

- Declared IPv4/UDP/QUIC layout; no packet codec, congestion, flow control, general ACK, loss or PTO.
- First server datagram supplies ServerHello, remaining server flight uses Handshake keys.
- Handshake ACK optionally sent after second server datagram; blocked graph is not a real QUIC deadlock.
- 0RTT acceptance/rejection and application replay policy are declared; no exactly-once guarantee.
- TLS HRR, QUIC Retry, invalid-ticket fallback, HTTP settings and background tickets remain unimplemented.

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
  "calculation": "quic-early-stream-declared-packets",
  "inputs": {
    "early_result": "reject",
    "application_early_data_authorized": true,
    "application_retry_authorized": false,
    "valid_psk": true,
    "early_credentials_valid": true,
    "address_token_valid": false,
    "server_flight_ack": true,
    "application_policy": "immediate",
    "request_payload_bytes": 7008,
    "response_payload_bytes": 100,
    "packet_payload_bytes": 1168,
    "zero_rtt_overhead_bytes": 32,
    "one_rtt_overhead_bytes": 32,
    "c2s_bits_per_second": 9824,
    "s2c_bits_per_second": 9824,
    "c2s_propagation_seconds": 1,
    "s2c_propagation_seconds": 1,
    "model_seconds": 0,
    "packets": {
      "client_hello": [
        1200
      ],
      "server_flight": [
        1200,
        1200
      ],
      "handshake_ack": [
        1200
      ],
      "client_finished": [
        1200
      ]
    },
    "response_overhead_bytes": 1100
  },
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
  "reference_source_root": "calculations",
  "status": "await_application_retry_decision",
  "milestones": {
    "client_hello_received": "2",
    "server_flight_received": "5",
    "client_1rtt_keys_installed": "5",
    "server_address_validated": "7",
    "handshake_ack_received": "7",
    "client_finished_received": "8"
  },
  "transmissions": [
    {
      "kind": "client_hello",
      "index": 0,
      "udp_bytes": 1200,
      "payload_bytes": 0,
      "direction": "c2s",
      "start": "0",
      "end": "1",
      "arrival": "2",
      "wire_bytes": 1228
    },
    {
      "kind": "request",
      "offset": 0,
      "payload_bytes": 1168,
      "encryption_level": "0rtt",
      "udp_bytes": 1200,
      "packet_number_space": "application",
      "packet_number": 0,
      "stream_id": 0,
      "end_offset": 1168,
      "direction": "c2s",
      "start": "1",
      "end": "2",
      "arrival": "3",
      "wire_bytes": 1228,
      "accepted": false
    },
    {
      "kind": "request",
      "offset": 1168,
      "payload_bytes": 1168,
      "encryption_level": "0rtt",
      "udp_bytes": 1200,
      "packet_number_space": "application",
      "packet_number": 1,
      "stream_id": 0,
      "end_offset": 2336,
      "direction": "c2s",
      "start": "2",
      "end": "3",
      "arrival": "4",
      "wire_bytes": 1228,
      "accepted": false
    },
    {
      "kind": "server_flight",
      "index": 0,
      "udp_bytes": 1200,
      "payload_bytes": 0,
      "direction": "s2c",
      "start": "2",
      "end": "3",
      "arrival": "4",
      "wire_bytes": 1228
    },
    {
      "kind": "request",
      "offset": 2336,
      "payload_bytes": 1168,
      "encryption_level": "0rtt",
      "udp_bytes": 1200,
      "packet_number_space": "application",
      "packet_number": 2,
      "stream_id": 0,
      "end_offset": 3504,
      "direction": "c2s",
      "start": "3",
      "end": "4",
      "arrival": "5",
      "wire_bytes": 1228,
      "accepted": false
    },
    {
      "kind": "server_flight",
      "index": 1,
      "udp_bytes": 1200,
      "payload_bytes": 0,
      "direction": "s2c",
      "start": "3",
      "end": "4",
      "arrival": "5",
      "wire_bytes": 1228
    },
    {
      "kind": "request",
      "offset": 3504,
      "payload_bytes": 1168,
      "encryption_level": "0rtt",
      "udp_bytes": 1200,
      "packet_number_space": "application",
      "packet_number": 3,
      "stream_id": 0,
      "end_offset": 4672,
      "direction": "c2s",
      "start": "4",
      "end": "5",
      "arrival": "6",
      "wire_bytes": 1228,
      "accepted": false
    },
    {
      "kind": "handshake_ack",
      "index": 0,
      "udp_bytes": 1200,
      "payload_bytes": 0,
      "direction": "c2s",
      "start": "5",
      "end": "6",
      "arrival": "7",
      "wire_bytes": 1228
    },
    {
      "kind": "client_finished",
      "index": 0,
      "udp_bytes": 1200,
      "payload_bytes": 0,
      "direction": "c2s",
      "start": "6",
      "end": "7",
      "arrival": "8",
      "wire_bytes": 1228
    }
  ],
  "anti_amplification_blocks": [],
  "summary": {
    "early_payload_sent_bytes": 4672,
    "one_rtt_payload_sent_bytes": 0,
    "request_payload_sent_bytes": 4672,
    "accepted_unique_request_bytes": 0,
    "discarded_early_payload_bytes": 4672,
    "delivered_response_payload_bytes": 0,
    "application_execution_count": 0,
    "modeled_wire_bytes_by_direction": {
      "c2s": 8596,
      "s2c": 2456
    },
    "last_modeled_arrival": "8"
  },
  "limitations": [
    "Declared IPv4/UDP/QUIC layout; no packet codec, congestion, flow control, general ACK, loss or PTO.",
    "First server datagram supplies ServerHello, remaining server flight uses Handshake keys.",
    "Handshake ACK optionally sent after second server datagram; blocked graph is not a real QUIC deadlock.",
    "0RTT acceptance/rejection and application replay policy are declared; no exactly-once guarantee.",
    "TLS HRR, QUIC Retry, invalid-ticket fallback, HTTP settings and background tickets remain unimplemented."
  ]
}
```
