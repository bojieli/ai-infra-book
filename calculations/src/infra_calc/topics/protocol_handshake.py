"""Finite, declared-packet TLS 1.3 / QUIC v1 dependency graph.

No packet capture, encryption, TCP congestion, PTO or HTTP codec is simulated.
Lengths are inputs: TCP lists count IP packets, QUIC lists count UDP payloads.
"""

from fractions import Fraction
import heapq
import json
from ..sources import provenance, read_source


def calculate(inputs=None):
    sources = provenance("protocol-rfc")
    if len(sources) != 7:
        raise ValueError("protocol-rfc requires seven pinned official sources")
    for source in sources:
        read_source(source["file"])
    p = dict(example() if inputs is None else inputs)
    protocol = p["protocol"]
    mode = p["mode"]
    if protocol not in ("tcp_tls13", "quic_v1"):
        raise ValueError("unknown protocol")
    if mode not in ("fresh", "resume", "early_accept", "early_reject", "reused"):
        raise ValueError("unknown mode")
    early = mode.startswith("early_")
    policy = p.get("application_policy", "wait_client_finished")
    if policy not in ("immediate", "wait_client_finished"):
        raise ValueError("unknown application policy")
    for name in (
        "application_retry_authorized",
        "address_token_valid",
        "connection_usable",
        "server_flight_ack",
        "valid_psk",
        "early_credentials_valid",
        "application_early_data_authorized",
    ):
        if name in p and not isinstance(p[name], bool):
            raise ValueError(name + " must be boolean")
    if mode == "reused" and not p.get("connection_usable", False):
        raise ValueError("reused requires an explicitly usable connection")
    if mode in ("resume", "early_accept", "early_reject") and not p.get(
        "valid_psk", False
    ):
        raise ValueError(
            "resumption requires valid PSK; invalid-ticket fallback not implemented"
        )
    if early and not p.get("application_early_data_authorized", False):
        raise ValueError("application must authorize sending replayable early data")
    if early and not p.get("early_credentials_valid", False):
        raise ValueError("early-data credentials/remembered limits must be validated")
    request = p["request_payload_bytes"]
    response = p["response_payload_bytes"]
    if type(response) is not int or response <= 0:
        raise ValueError("response payload must be positive integer")
    if type(request) is not int or request <= 0:
        raise ValueError("request payload must be positive integer")
    rate = {d: Fraction(str(p[d + "_bits_per_second"])) for d in ("c2s", "s2c")}
    delay = {d: Fraction(str(p[d + "_propagation_seconds"])) for d in rate}
    model = Fraction(str(p.get("model_seconds", 0)))
    if min(rate.values()) <= 0 or min(delay.values()) < 0 or model < 0:
        raise ValueError("invalid rate/delay/model")
    packets = p["packets"]
    for name, sizes in packets.items():
        if (
            not isinstance(sizes, list)
            or not sizes
            or any(type(n) is not int or n <= 0 for n in sizes)
        ):
            raise ValueError("packet lists require positive integer lengths: " + name)
        if len(sizes) > 10000:
            raise ValueError("packet limit")
    overhead = 28 if protocol == "quic_v1" else 0
    if protocol == "quic_v1":
        if mode != "reused" and any(n < 1200 for n in packets["client_hello"]):
            raise ValueError("client Initial UDP payload must be >=1200")
        if mode != "reused" and packets["server_flight"][0] < 1200:
            raise ValueError(
                "declared server first ack-eliciting Initial must be padded >=1200"
            )
        if any(n > 65507 for sizes in packets.values() for n in sizes):
            raise ValueError("IPv4 UDP payload maximum exceeded")
    elif any(n < 40 or n > 65535 for sizes in packets.values() for n in sizes):
        raise ValueError("declared IPv4 TCP packet size outside bounds")
    payloads = p["payload_bytes_by_packet"]
    for name in (
        ("request", "early_request", "response") if early else ("request", "response")
    ):
        distribution = payloads[name]
        if (
            not isinstance(distribution, list)
            or len(distribution) != len(packets[name])
            or any(type(n) is not int or n <= 0 for n in distribution)
            or sum(distribution) != (response if name == "response" else request)
        ):
            raise ValueError("payload distribution must sum to request bytes: " + name)
        # Explicit conservative overhead floor, not a complete packet codec.
        floor = 32 if protocol == "quic_v1" else 62
        if any(
            size - payload < floor for size, payload in zip(packets[name], distribution)
        ):
            raise ValueError(
                "packet cannot carry declared payload plus overhead: " + name
            )
    clock = Fraction(0)
    serial = 0
    events = []
    queue = {"c2s": [], "s2c": []}
    free = {d: Fraction(0) for d in rate}
    received_udp = 0
    sent_udp = 0
    validated = mode == "reused" or p.get("address_token_valid", False)
    trace, blocks, milestones = [], [], {}
    executed = False
    payload_sent = 0
    flights = {}

    def schedule(t, callback):
        nonlocal serial
        serial += 1
        heapq.heappush(events, (t, serial, callback))

    def pump(direction):
        nonlocal sent_udp
        q = queue[direction]
        while q:
            name, index, size, ready, callback, packet_callback = q[0]
            if (
                protocol == "quic_v1"
                and direction == "s2c"
                and not validated
                and sent_udp + size > 3 * received_udp
            ):
                state = {
                    "at": str(clock),
                    "flight": name,
                    "packet": index,
                    "received_udp": received_udp,
                    "sent_udp": sent_udp,
                    "next_udp": size,
                    "limit_udp": 3 * received_udp,
                }
                if not blocks or blocks[-1] != state:
                    blocks.append(state)
                return
            q.pop(0)
            start = max(clock, free[direction], ready)
            end = start + Fraction(8 * (size + overhead), 1) / rate[direction]
            arrival = end + delay[direction]
            free[direction] = end
            if protocol == "quic_v1" and direction == "s2c":
                sent_udp += (
                    size  # irrevocable FIFO reservation; budget conservatively reserved
                )
            trace.append(
                {
                    "flight": name,
                    "packet": index,
                    "direction": direction,
                    "declared_bytes": size,
                    "wire_bytes": size + overhead,
                    "ready": str(ready),
                    "start": str(start),
                    "end": str(end),
                    "arrival": str(arrival),
                }
            )

            def arrive(
                name=name,
                index=index,
                size=size,
                callback=callback,
                packet_callback=packet_callback,
            ):
                nonlocal received_udp, validated
                if protocol == "quic_v1" and direction == "c2s":
                    received_udp += size
                    if name in ("client_finished", "handshake_ack"):
                        validated = True
                        milestones.setdefault("server_address_validated", str(clock))
                packet_callback(index)
                flights[name] -= 1
                if flights[name] == 0:
                    milestones[name + "_received"] = str(clock)
                    callback()
                pump("s2c")

            schedule(arrival, arrive)

    def send(
        name, direction, callback=lambda: None, packet_callback=lambda index: None
    ):
        flights[name] = len(packets[name])
        for index, size in enumerate(packets[name]):
            queue[direction].append(
                (name, index, size, clock, callback, packet_callback)
            )
        pump(direction)

    def response_ready():
        send("response", "s2c", lambda: milestones.update(complete_response=str(clock)))

    def maybe_execute():
        nonlocal executed
        if executed or "accepted_request" not in milestones:
            return
        if (
            mode != "reused"
            and policy == "wait_client_finished"
            and "client_finished_received" not in milestones
        ):
            return
        executed = True
        milestones["application_execution"] = str(clock)
        # Server application data cannot precede the server's TLS flight.
        schedule(clock + model, response_ready)

    def accept_request():
        milestones["accepted_request"] = str(clock)
        maybe_execute()

    def normal_request():
        nonlocal payload_sent
        payload_sent += request
        send("request", "c2s", accept_request)

    def client_finished_arrived():
        milestones["server_handshake_complete"] = str(clock)
        maybe_execute()

    def server_flight_arrived():
        milestones["client_peer_authenticated"] = str(clock)
        if protocol == "quic_v1" and early:
            if any(
                t["flight"] == "early_request" and Fraction(t["end"]) > clock
                for t in trace
            ):
                raise ValueError(
                    "early request crosses client 1RTT key installation; packet payload/offset key switching not implemented"
                )
        # TCP accepted early data includes EndOfEarlyData in this declared flight;
        # QUIC has only TLS Finished and explicitly no EndOfEarlyData.
        send("client_finished", "c2s", client_finished_arrived)
        if not early or (
            mode == "early_reject" and p.get("application_retry_authorized", False)
        ):
            normal_request()

    def server_packet_arrived(index):
        if protocol == "quic_v1" and p.get("server_flight_ack", False):
            # First packet is Initial; second is Handshake. On second arrival,
            # this declared immediate Handshake ACK proves address possession.
            if index == 1:
                send("handshake_ack", "c2s")

    def hello_arrived():
        send("server_flight", "s2c", server_flight_arrived, server_packet_arrived)

    def start_tls():
        nonlocal payload_sent
        send("client_hello", "c2s", hello_arrived)
        if early:
            payload_sent += request
            send(
                "early_request",
                "c2s",
                accept_request if mode == "early_accept" else lambda: None,
            )

    if mode == "reused":
        normal_request()
    elif protocol == "tcp_tls13":
        # ClientHello packet also carries final TCP ACK. No TCP Fast Open.
        send("syn", "c2s", lambda: send("syn_ack", "s2c", start_tls))
    else:
        start_tls()
    while events:
        clock, _, callback = heapq.heappop(events)
        callback()
    pending = [
        {"direction": d, "flight": item[0], "packet": item[1], "bytes": item[2]}
        for d in queue
        for item in queue[d]
    ]
    status = (
        "complete"
        if "complete_response" in milestones
        else (
            "budget_blocked_in_declared_graph"
            if pending
            else "await_application_retry_decision"
        )
    )
    return {
        "reference_sources": sources,
        "calculation": "protocol-handshake-declared-packet-graph",
        "inputs": p,
        "status": status,
        "milestones": milestones,
        "transmissions": trace,
        "anti_amplification_blocks": blocks,
        "pending_packets": pending,
        "summary": {
            "request_payload_sent_bytes": payload_sent,
            "accepted_unique_request_bytes": (
                request if "accepted_request" in milestones else 0
            ),
            "rejected_early_payload_bytes": request if mode == "early_reject" else 0,
            "application_execution_count": int(executed),
            "delivered_response_payload_bytes": (
                response if "complete_response" in milestones else 0
            ),
            "modeled_wire_bytes_by_direction": {
                d: sum(t["wire_bytes"] for t in trace if t["direction"] == d)
                for d in rate
            },
            "last_modeled_arrival": str(clock),
        },
        "limitations": [
            "Declared packet lengths; no encryption or packet capture.",
            "No HRR, Retry, ticket fallback, background ticket/token issuance, HTTP or HTTP/3 SETTINGS state machine.",
            "No loss, congestion, flow-control, TCP data ACK, or general QUIC ACK/PTO simulation.",
            "Optional immediate ACK of second server Handshake datagram only; a blocked graph is not a claim of protocol deadlock.",
            "IPv4 without options; QUIC wire adds 20B IP + 8B UDP; TCP declarations already include IP/TCP.",
            "Reused connection starts idle with sufficient flow/congestion credit; no inherited traffic.",
            "Immediate early execution is an explicit application policy and conveys no replay/exactly-once guarantee.",
        ],
    }


def example(protocol="quic_v1", mode="fresh"):
    quic = protocol == "quic_v1"
    return {
        "protocol": protocol,
        "mode": mode,
        "valid_psk": True,
        "early_credentials_valid": True,
        "connection_usable": True,
        "address_token_valid": False,
        "server_flight_ack": True,
        "application_early_data_authorized": True,
        "payload_bytes_by_packet": {
            "request": [100],
            "early_request": [100],
            "response": [200],
        },
        "application_policy": "immediate",
        "application_retry_authorized": True,
        "request_payload_bytes": 100,
        "response_payload_bytes": 200,
        "model_seconds": "0.01",
        "c2s_bits_per_second": 20000000,
        "s2c_bits_per_second": 100000000,
        "c2s_propagation_seconds": "0.05",
        "s2c_propagation_seconds": "0.05",
        "packets": {
            "syn": [60],
            "syn_ack": [60],
            "client_hello": [1200] if quic else [560],
            "server_flight": (
                [1200, 1200] if quic else ([1400, 1400] if mode == "fresh" else [500])
            ),
            "client_finished": (
                [100] if quic else [140 if mode == "early_accept" else 120]
            ),
            "handshake_ack": [80],
            "request": [180],
            "early_request": [180],
            "response": [280],
        },
    }


def markdown(result):
    """Render business milestones and byte ledgers before the exact event trace."""
    rows = [
        "# " + result["calculation"],
        "",
        "这是声明数据包和消息依赖的计算；包长不是官方测量值，时间不是真实协议实测。",
        "",
        "状态：`" + result["status"] + "`。",
        "",
        "## 业务与握手时刻",
        "",
        "时间单位为秒，保留精确分数；不存在的完整响应不会以最后消息时刻替代。",
        "",
        "| 事件 | 精确时刻（s） |",
        "| --- | ---: |",
    ]
    rows.extend(
        "| " + key + " | " + str(value) + " |"
        for key, value in result["milestones"].items()
    )
    rows.extend(["", "## 有效业务与已建模字节", "", "| 数量 | 值 |", "| --- | ---: |"])
    for key, value in result["summary"].items():
        if isinstance(value, dict):
            rows.extend(
                "| " + key + "." + direction + " | " + str(count) + " |"
                for direction, count in value.items()
            )
        else:
            rows.append("| " + key + " | " + str(value) + " |")
    rows.extend(
        [
            "",
            "物理字节仅包括本图显式列出的消息，不是包含全部 ACK／控制消息的抓包总量。",
            "",
            "## 适用范围",
            "",
        ]
    )
    rows.extend("- " + limitation for limitation in result["limitations"])
    rows.extend(["", "## 固定官方来源", ""])
    rows.extend(
        "- ["
        + source["revision"]
        + "]("
        + source["url"]
        + ")：`"
        + source["sha256"]
        + "`。"
        for source in result["reference_sources"]
    )
    rows.extend(
        [
            "",
            "## 完整输入与逐包事件",
            "",
            "```json",
            json.dumps(result, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(rows)
