"""QUIC v1 declared-packet streaming early-data key transition ledger."""

from fractions import Fraction
import heapq
import json
from ..sources import provenance, read_source


def calculate(inputs=None):
    p = dict(example() if inputs is None else inputs)
    p.setdefault("response_overhead_bytes", p["one_rtt_overhead_bytes"])
    sources = provenance("protocol-rfc")
    if len(sources) != 7:
        raise ValueError("protocol-rfc requires seven pinned official sources")
    for source in sources:
        read_source(source["file"])
    for name in (
        "application_early_data_authorized",
        "application_retry_authorized",
        "valid_psk",
        "early_credentials_valid",
        "address_token_valid",
        "server_flight_ack",
    ):
        if type(p[name]) is not bool:
            raise ValueError(name + " must be boolean")
    if not all(
        p[n]
        for n in (
            "application_early_data_authorized",
            "valid_psk",
            "early_credentials_valid",
        )
    ):
        raise ValueError(
            "early sending needs application authorization and valid credentials"
        )
    if p["early_result"] not in ("accept", "reject"):
        raise ValueError("early_result")
    if p["application_policy"] not in ("immediate", "wait_client_finished"):
        raise ValueError("application_policy")
    for name in (
        "request_payload_bytes",
        "response_payload_bytes",
        "packet_payload_bytes",
        "zero_rtt_overhead_bytes",
        "one_rtt_overhead_bytes",
        "response_overhead_bytes",
    ):
        if type(p[name]) is not int or p[name] <= 0:
            raise ValueError(name + " must be positive integer")
    if (
        min(
            p["zero_rtt_overhead_bytes"],
            p["one_rtt_overhead_bytes"],
            p["response_overhead_bytes"],
        )
        < 32
    ):
        raise ValueError("declared QUIC frame/header/tag overhead must be >=32B")
    packet_payload = p["packet_payload_bytes"]
    if (
        packet_payload
        + max(
            p["zero_rtt_overhead_bytes"],
            p["one_rtt_overhead_bytes"],
            p["response_overhead_bytes"],
        )
        > 65507
    ):
        raise ValueError("UDP payload exceeds IPv4 maximum")
    total_packets = sum(
        (p[n] + packet_payload - 1) // packet_payload
        for n in ("request_payload_bytes", "response_payload_bytes")
    )
    if total_packets > 100000:
        raise ValueError("maximum 100000 original application packets")
    packets = p["packets"]
    for name in ("client_hello", "server_flight", "client_finished", "handshake_ack"):
        if (
            not isinstance(packets[name], list)
            or not packets[name]
            or any(type(n) is not int or n < 32 or n > 65507 for n in packets[name])
        ):
            raise ValueError("invalid packet list: " + name)
    if (
        any(n < 1200 for n in packets["client_hello"])
        or packets["server_flight"][0] < 1200
    ):
        raise ValueError("Initial datagram minimum 1200B")
    worst_case_packets = (
        2 * ((p["request_payload_bytes"] + packet_payload - 1) // packet_payload)
        + ((p["response_payload_bytes"] + packet_payload - 1) // packet_payload)
        + sum(
            len(packets[name])
            for name in (
                "client_hello",
                "server_flight",
                "client_finished",
                "handshake_ack",
            )
        )
    )
    if worst_case_packets > 200000:
        raise ValueError(
            "maximum 200000 packets including controls and authorized retry"
        )
    rates = {d: Fraction(str(p[d + "_bits_per_second"])) for d in ("c2s", "s2c")}
    delays = {d: Fraction(str(p[d + "_propagation_seconds"])) for d in rates}
    model = Fraction(str(p["model_seconds"]))
    if min(rates.values()) <= 0 or min(delays.values()) < 0 or model < 0:
        raise ValueError("invalid timing input")
    now = Fraction(0)
    serial = 0
    events = []
    controls = {d: [] for d in rates}
    busy = {d: False for d in rates}
    trace, blocks, milestones = [], [], {}
    received_udp = sent_udp = 0
    validated = p["address_token_valid"]
    keys = False
    request_enabled = False
    request_cursor = 0
    response_cursor = 0
    response_enabled = False
    accepted_offsets = set()
    response_offsets = set()
    accepted_bytes = response_bytes = early_sent = normal_sent = 0
    executed = False
    remaining = {}
    application_packet_number = {d: 0 for d in rates}

    def event(t, callback, priority=0):
        nonlocal serial
        serial += 1
        heapq.heappush(events, (t, priority, serial, callback))

    def wake():
        event(now, lambda: pump("c2s"), 2)
        event(now, lambda: pump("s2c"), 2)

    def enqueue(name, direction):
        remaining[name] = len(packets[name])
        controls[direction].extend(
            {"kind": name, "index": i, "udp_bytes": size, "payload_bytes": 0}
            for i, size in enumerate(packets[name])
        )
        wake()

    def response_ready():
        nonlocal response_enabled
        response_enabled = True
        milestones["response_ready"] = str(now)
        wake()

    def maybe_execute():
        nonlocal executed
        if executed or accepted_bytes != p["request_payload_bytes"]:
            return
        if (
            p["application_policy"] == "wait_client_finished"
            and "client_finished_received" not in milestones
        ):
            return
        executed = True
        milestones["application_execution"] = str(now)
        event(now + model, response_ready)

    def arrived(packet, direction):
        nonlocal received_udp, validated, keys, request_enabled, request_cursor
        nonlocal accepted_bytes, response_bytes
        name = packet["kind"]
        if direction == "c2s":
            received_udp += packet["udp_bytes"]
            if name in ("handshake_ack", "client_finished"):
                validated = True
                milestones.setdefault("server_address_validated", str(now))
        if name == "request":
            accepted = (
                packet["encryption_level"] == "1rtt" or p["early_result"] == "accept"
            )
            packet["accepted"] = accepted
            if accepted and packet["offset"] not in accepted_offsets:
                accepted_offsets.add(packet["offset"])
                accepted_bytes += packet["payload_bytes"]
                if accepted_bytes == p["request_payload_bytes"]:
                    milestones["complete_request"] = str(now)
                maybe_execute()
        elif name == "response":
            if packet["offset"] not in response_offsets:
                response_offsets.add(packet["offset"])
                response_bytes += packet["payload_bytes"]
                if response_bytes == p["response_payload_bytes"]:
                    milestones["complete_response"] = str(now)
        else:
            remaining[name] -= 1
            if (
                name == "server_flight"
                and packet["index"] == 1
                and p["server_flight_ack"]
            ):
                enqueue("handshake_ack", "c2s")
            if remaining[name] == 0:
                milestones[name + "_received"] = str(now)
                if name == "client_hello":
                    enqueue("server_flight", "s2c")
                elif name == "server_flight":
                    keys = True
                    milestones["client_1rtt_keys_installed"] = str(now)
                    if p["early_result"] == "reject":
                        if p["application_retry_authorized"]:
                            # Restart only after rejection. Already-started 0RTT
                            # packets remain non-preemptive and are discarded.
                            request_cursor = 0
                        else:
                            request_enabled = False
                    enqueue("client_finished", "c2s")
                elif name == "client_finished":
                    maybe_execute()
        wake()

    def pump(direction):
        nonlocal sent_udp, request_cursor, response_cursor, request_enabled, early_sent, normal_sent
        if busy[direction]:
            return
        packet = controls[direction][0] if controls[direction] else None
        if (
            packet is None
            and direction == "c2s"
            and request_enabled
            and request_cursor < p["request_payload_bytes"]
        ):
            level = "1rtt" if keys else "0rtt"
            size = min(packet_payload, p["request_payload_bytes"] - request_cursor)
            packet = {
                "kind": "request",
                "offset": request_cursor,
                "payload_bytes": size,
                "encryption_level": level,
                "udp_bytes": size
                + p["one_rtt_overhead_bytes" if keys else "zero_rtt_overhead_bytes"],
            }
        elif (
            packet is None
            and direction == "s2c"
            and response_enabled
            and response_cursor < p["response_payload_bytes"]
        ):
            size = min(packet_payload, p["response_payload_bytes"] - response_cursor)
            packet = {
                "kind": "response",
                "offset": response_cursor,
                "payload_bytes": size,
                "encryption_level": "1rtt",
                "udp_bytes": size + p["response_overhead_bytes"],
            }
        if packet is None:
            return
        if (
            direction == "s2c"
            and not validated
            and sent_udp + packet["udp_bytes"] > 3 * received_udp
        ):
            block = {
                "at": str(now),
                "kind": packet["kind"],
                "sent_udp": sent_udp,
                "received_udp": received_udp,
                "next_udp": packet["udp_bytes"],
            }
            if not blocks or blocks[-1] != block:
                blocks.append(block)
            return
        if packet["kind"] not in ("request", "response"):
            controls[direction].pop(0)
        elif direction == "c2s":
            request_cursor += packet["payload_bytes"]
            if keys:
                normal_sent += packet["payload_bytes"]
            else:
                early_sent += packet["payload_bytes"]
        else:
            response_cursor += packet["payload_bytes"]
        if packet["kind"] in ("request", "response"):
            packet["packet_number_space"] = "application"
            packet["packet_number"] = application_packet_number[direction]
            application_packet_number[direction] += 1
            packet["stream_id"] = 0
            packet["end_offset"] = packet["offset"] + packet["payload_bytes"]
        busy[direction] = True
        if direction == "s2c":
            sent_udp += packet["udp_bytes"]
        wire = packet["udp_bytes"] + 28
        end = now + Fraction(8 * wire, 1) / rates[direction]
        arrival = end + delays[direction]
        packet.update(
            direction=direction,
            start=str(now),
            end=str(end),
            arrival=str(arrival),
            wire_bytes=wire,
        )
        trace.append(packet)

        def finished():
            nonlocal request_enabled
            busy[direction] = False
            # App upload becomes eligible once the final ClientHello packet
            # has left its sender; it need not reach the server first.
            if (
                packet["kind"] == "client_hello"
                and packet["index"] == len(packets["client_hello"]) - 1
            ):
                request_enabled = True
            wake()

        event(end, finished, 1)
        event(arrival, lambda: arrived(packet, direction))

    enqueue("client_hello", "c2s")
    while events:
        now, _, _, callback = heapq.heappop(events)
        callback()
    status = (
        "complete"
        if response_bytes == p["response_payload_bytes"]
        else (
            "await_application_retry_decision"
            if keys
            and p["early_result"] == "reject"
            and not p["application_retry_authorized"]
            else "budget_blocked_in_declared_graph"
        )
    )
    return {
        "calculation": "quic-early-stream-declared-packets",
        "inputs": p,
        "reference_sources": sources,
        "reference_source_root": "calculations",
        "status": status,
        "milestones": milestones,
        "transmissions": trace,
        "anti_amplification_blocks": blocks,
        "summary": {
            "early_payload_sent_bytes": early_sent,
            "one_rtt_payload_sent_bytes": normal_sent,
            "request_payload_sent_bytes": early_sent + normal_sent,
            "accepted_unique_request_bytes": accepted_bytes,
            "discarded_early_payload_bytes": (
                early_sent if p["early_result"] == "reject" else 0
            ),
            "delivered_response_payload_bytes": response_bytes,
            "application_execution_count": int(executed),
            "modeled_wire_bytes_by_direction": {
                d: sum(t["wire_bytes"] for t in trace if t["direction"] == d)
                for d in rates
            },
            "last_modeled_arrival": str(now),
        },
        "limitations": [
            "Declared IPv4/UDP/QUIC layout; no packet codec, congestion, flow control, general ACK, loss or PTO.",
            "First server datagram supplies ServerHello, remaining server flight uses Handshake keys.",
            "Handshake ACK optionally sent after second server datagram; blocked graph is not a real QUIC deadlock.",
            "0RTT acceptance/rejection and application replay policy are declared; no exactly-once guarantee.",
            "TLS HRR, QUIC Retry, invalid-ticket fallback, HTTP settings and background tickets remain unimplemented.",
        ],
    }


def example():
    return {
        "early_result": "accept",
        "application_early_data_authorized": True,
        "application_retry_authorized": True,
        "valid_psk": True,
        "early_credentials_valid": True,
        "address_token_valid": False,
        "server_flight_ack": True,
        "application_policy": "immediate",
        "request_payload_bytes": 30000000,
        "response_payload_bytes": 5000000,
        "packet_payload_bytes": 1100,
        "zero_rtt_overhead_bytes": 64,
        "one_rtt_overhead_bytes": 48,
        "c2s_bits_per_second": 20000000,
        "s2c_bits_per_second": 100000000,
        "c2s_propagation_seconds": "0.05",
        "s2c_propagation_seconds": "0.05",
        "model_seconds": "0.3",
        "packets": {
            "client_hello": [1200],
            "server_flight": [1200, 1200],
            "client_finished": [100],
            "handshake_ack": [80],
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
