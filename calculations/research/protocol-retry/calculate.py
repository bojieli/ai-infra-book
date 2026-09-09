"""QUIC v1 declared-packet streaming early-data key transition ledger."""

from fractions import Fraction
import hashlib
import heapq
import json
from pathlib import Path


def calculate(inputs):
    p = dict(inputs)
    p.setdefault("handshake_event", "none")
    p.setdefault("send_early", True)
    p.setdefault("client_credentials_available", p.get("valid_psk", False))
    if (
        type(p["send_early"]) is not bool
        or type(p["client_credentials_available"]) is not bool
    ):
        raise ValueError("early mode and client credentials require booleans")
    p.setdefault("retry_early_policy", "reattempt")
    p.setdefault("retry_early_replay_authorized", True)
    p.setdefault("retry_token_valid", True)
    p.setdefault("retry_integrity_valid", True)
    p.setdefault("initial_dcid", "original-server-cid")
    p.setdefault("retry_scid", "retry-server-cid")
    p.setdefault("client_scid", "client-cid")
    p.setdefault("retry_token_bytes", 32)
    p.setdefault("client_hello_crypto_bytes", 400)
    if p["handshake_event"] not in (
        "none",
        "hrr",
        "retry",
        "psk_unknown_fallback",
        "psk_unknown_abort",
        "selected_binder_invalid",
    ):
        raise ValueError("unsupported handshake event or combination")
    if p["retry_early_policy"] not in ("reattempt", "wait_1rtt"):
        raise ValueError("retry early policy")
    if (
        type(p["retry_token_valid"]) is not bool
        or type(p["retry_integrity_valid"]) is not bool
    ):
        raise ValueError("retry validation flags must be boolean")
    if type(p["retry_token_bytes"]) is not int or p["retry_token_bytes"] <= 0:
        raise ValueError("nonempty Retry token required")
    if p["retry_scid"] == p["initial_dcid"] or not all(
        isinstance(p[n], str) and p[n]
        for n in ("initial_dcid", "retry_scid", "client_scid")
    ):
        raise ValueError("declared connection IDs invalid")
    if type(p["retry_early_replay_authorized"]) is not bool:
        raise ValueError("Retry early replay authorization must be boolean")
    if (
        p["send_early"]
        and p["handshake_event"] == "retry"
        and p["retry_early_policy"] == "reattempt"
        and not p["retry_early_replay_authorized"]
    ):
        raise ValueError("Retry early reattempt requires separate authorization")
    effective_reject = p["early_result"] == "reject" or p["handshake_event"] in (
        "hrr",
        "psk_unknown_fallback",
        "psk_unknown_abort",
        "selected_binder_invalid",
    )
    p.setdefault("response_overhead_bytes", p["one_rtt_overhead_bytes"])
    source_root = Path(__file__).resolve().parent.parent / "protocol-handshake"
    sources = json.loads((source_root / "sources.lock.json").read_text())
    for source in sources:
        data = (source_root / source["file"]).read_bytes()
        if (
            len(data) != source["bytes"]
            or hashlib.sha256(data).hexdigest() != source["sha256"]
        ):
            raise ValueError("source integrity mismatch")
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
    if p["send_early"] and not all(
        p[n]
        for n in (
            "application_early_data_authorized",
            "client_credentials_available",
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
    control_names = [
        "client_hello",
        "server_flight",
        "client_finished",
        "handshake_ack",
    ]
    if p["handshake_event"] == "retry":
        control_names += ["retry", "client_hello_retry", "failure"]
    elif p["handshake_event"] == "hrr":
        control_names += ["hrr", "client_hello_hrr"]
    elif p["handshake_event"] in ("psk_unknown_abort", "selected_binder_invalid"):
        control_names += ["failure"]
    for name in control_names:
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
    if "failure" in control_names and len(packets["failure"]) != 1:
        raise ValueError(
            "only one complete Initial CONNECTION_CLOSE datagram is supported"
        )
    worst_case_packets = (
        3 * ((p["request_payload_bytes"] + packet_payload - 1) // packet_payload)
        + ((p["response_payload_bytes"] + packet_payload - 1) // packet_payload)
        + sum(len(packets[name]) for name in control_names)
    )
    if worst_case_packets > 200000:
        raise ValueError(
            "maximum 200000 packets including controls and authorized retry"
        )
    for name in ("client_hello_retry", "client_hello_hrr", "hrr"):
        if name in control_names and any(n < 1200 for n in packets[name]):
            raise ValueError("Initial-carrying datagrams need >=1200 bytes")
    if p["handshake_event"] == "retry" and len(packets["retry"]) != 1:
        raise ValueError(
            "only one Retry datagram supported; repeated Retry trace not implemented"
        )
    if p["handshake_event"] == "retry":
        if any(n < p["retry_token_bytes"] + 48 for n in packets["retry"]):
            raise ValueError("Retry token does not fit declared header/tag budget")
        if any(n < 48 + p["retry_token_bytes"] for n in packets["client_hello_retry"]):
            raise ValueError("token must fit each repeated Initial token field")
        if (
            type(p["client_hello_crypto_bytes"]) is not int
            or p["client_hello_crypto_bytes"] <= 0
            or sum(
                n - 48 - p["retry_token_bytes"] for n in packets["client_hello_retry"]
            )
            < p["client_hello_crypto_bytes"]
        ):
            raise ValueError(
                "declare Initial retry capacity including token; preserve ClientHello payload"
            )
    if (
        type(p["client_hello_crypto_bytes"]) is not int
        or p["client_hello_crypto_bytes"] <= 0
        or sum(n - 48 for n in packets["client_hello"]) < p["client_hello_crypto_bytes"]
    ):
        raise ValueError(
            "original Initial cannot carry declared ClientHello CRYPTO bytes"
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
    control_packet_number = {d: {"initial": 0, "handshake": 0} for d in rates}
    client_epoch = 0
    early_stopped = False
    server_failed = False
    terminated = False
    transitions = []

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
        nonlocal accepted_bytes, response_bytes, client_epoch, early_stopped, server_failed, terminated
        name = packet["kind"]
        if direction == "c2s":
            received_udp += packet["udp_bytes"]
            if name in ("handshake_ack", "client_finished"):
                validated = True
                milestones.setdefault("server_address_validated", str(now))
        if name == "client_hello_retry" and packet["index"] == 0:
            if p["retry_token_valid"]:
                validated = True
                milestones.setdefault("server_address_validated", str(now))
            else:
                server_failed = True
                enqueue("failure", "s2c")
                transitions.append(
                    {"at": str(now), "event": "invalid_Retry_token_server_refuses"}
                )
        if name == "request":
            accepted = not server_failed and (
                packet["encryption_level"] == "1rtt" or not effective_reject
            )
            if p["handshake_event"] == "retry" and packet["attempt_epoch"] == 0:
                accepted = False
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
                    if p["handshake_event"] == "retry":
                        enqueue("retry", "s2c")
                    elif p["handshake_event"] == "hrr":
                        enqueue("hrr", "s2c")
                    elif p["handshake_event"] in (
                        "psk_unknown_abort",
                        "selected_binder_invalid",
                    ):
                        server_failed = True
                        enqueue("failure", "s2c")
                    else:
                        enqueue("server_flight", "s2c")
                elif name == "hrr":
                    early_stopped = True
                    request_enabled = False
                    transitions.append(
                        {
                            "at": str(now),
                            "event": "HRR_early_rejected_CH2_without_early_data",
                        }
                    )
                    enqueue("client_hello_hrr", "c2s")
                elif name == "retry":
                    if not p["retry_integrity_valid"]:
                        transitions.append(
                            {
                                "at": str(now),
                                "event": "invalid_Retry_discarded_no_PTO_modeled",
                            }
                        )
                    else:
                        client_epoch = 1
                        request_enabled = False
                        early_stopped = p["retry_early_policy"] == "wait_1rtt"
                        request_cursor = 0
                        transitions.append(
                            {
                                "at": str(now),
                                "event": "Retry_validated_Initial_keys_changed_PN_retained_recovery_reset_unmodeled",
                            }
                        )
                        enqueue("client_hello_retry", "c2s")
                elif name == "client_hello_hrr":
                    enqueue("server_flight", "s2c")
                elif name == "client_hello_retry":
                    if p["retry_token_valid"]:
                        validated = True
                        milestones.setdefault("server_address_validated", str(now))
                        enqueue("server_flight", "s2c")

                elif name == "failure":
                    terminated = True
                    request_enabled = False
                    transitions.append(
                        {
                            "at": str(now),
                            "event": "handshake_failed_no_application_fallback",
                        }
                    )
                elif name == "server_flight":
                    keys = True
                    milestones["client_1rtt_keys_installed"] = str(now)
                    if p["send_early"] and (
                        effective_reject
                        or (
                            p["handshake_event"] == "retry"
                            and p["retry_early_policy"] == "wait_1rtt"
                        )
                    ):
                        if p["application_retry_authorized"]:
                            # Restart only after rejection. Already-started 0RTT
                            # packets remain non-preemptive and are discarded.
                            request_cursor = 0
                            request_enabled = True
                        else:
                            request_enabled = False
                    elif not p["send_early"]:
                        request_enabled = True
                    enqueue("client_finished", "c2s")
                elif name == "client_finished":
                    maybe_execute()
        wake()

    def pump(direction):
        nonlocal sent_udp, request_cursor, response_cursor, request_enabled, early_sent, normal_sent
        if busy[direction] or (direction == "c2s" and terminated):
            return
        packet = controls[direction][0] if controls[direction] else None
        if (
            packet is None
            and direction == "c2s"
            and request_enabled
            and not terminated
            and (keys or not early_stopped)
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
            packet["attempt_epoch"] = client_epoch
            packet["application_key_epoch"] = (
                0 if packet["encryption_level"] == "0rtt" else 1
            )
            packet["destination_connection_id"] = (
                (p["retry_scid"] if client_epoch else p["initial_dcid"])
                if direction == "c2s"
                else p["client_scid"]
            )
            packet["stream_id"] = 0
            packet["end_offset"] = packet["offset"] + packet["payload_bytes"]
        if packet["kind"] not in ("request", "response"):
            kind = packet["kind"]
            if kind != "retry":
                space = (
                    "initial"
                    if kind
                    in (
                        "client_hello",
                        "client_hello_retry",
                        "client_hello_hrr",
                        "hrr",
                        "failure",
                    )
                    or (kind == "server_flight" and packet["index"] == 0)
                    else "handshake"
                )
                packet["packet_number_space"] = space
                packet["packet_number"] = control_packet_number[direction][space]
                control_packet_number[direction][space] += 1
            packet["initial_key_epoch"] = client_epoch
            if direction == "c2s":
                packet["destination_connection_id"] = (
                    p["retry_scid"] if client_epoch else p["initial_dcid"]
                )
                packet["source_connection_id"] = p["client_scid"]
                packet["retry_token_bytes"] = (
                    p["retry_token_bytes"] if kind == "client_hello_retry" else 0
                )
                if kind in ("client_hello", "client_hello_retry", "client_hello_hrr"):
                    packet["tls_client_hello_identity"] = (
                        "CH2-no-early-data" if kind == "client_hello_hrr" else "CH1"
                    )
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
                packet["kind"] in ("client_hello", "client_hello_retry")
                and packet["index"] == len(packets[packet["kind"]]) - 1
            ):
                request_enabled = (
                    p["send_early"] and not early_stopped and not terminated
                )
            wake()

        event(end, finished, 1)
        event(arrival, lambda: arrived(packet, direction))

    enqueue("client_hello", "c2s")
    while events:
        now, _, _, callback = heapq.heappop(events)
        callback()
    next_server_udp = None
    if controls["s2c"]:
        next_server_udp = controls["s2c"][0]["udp_bytes"]
    elif response_enabled and response_cursor < p["response_payload_bytes"]:
        next_server_udp = (
            min(packet_payload, p["response_payload_bytes"] - response_cursor)
            + p["response_overhead_bytes"]
        )
    budget_waiting = (
        next_server_udp is not None
        and not validated
        and sent_udp + next_server_udp > 3 * received_udp
    )
    if terminated:
        status = "handshake_failed"
    elif response_bytes == p["response_payload_bytes"]:
        status = "complete"
    elif (
        keys
        and (effective_reject or early_stopped)
        and not p["application_retry_authorized"]
    ):
        status = "await_application_retry_decision"
    elif budget_waiting:
        status = "budget_blocked_in_declared_graph"
    else:
        status = "waiting_unmodeled_recovery"
    return {
        "calculation": "quic-retry-declared-packets",
        "inputs": p,
        "reference_sources": sources,
        "reference_source_root": "../protocol-handshake",
        "status": status,
        "milestones": milestones,
        "state_transitions": transitions,
        "transmissions": trace,
        "anti_amplification_blocks": blocks,
        "summary": {
            "early_payload_sent_bytes": early_sent,
            "one_rtt_payload_sent_bytes": normal_sent,
            "request_payload_sent_bytes": early_sent + normal_sent,
            "accepted_unique_request_bytes": accepted_bytes,
            "discarded_early_payload_bytes": (
                sum(
                    t["payload_bytes"]
                    for t in trace
                    if t["kind"] == "request"
                    and t["encryption_level"] == "0rtt"
                    and not t.get("accepted", False)
                )
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
            "First final server_flight datagram supplies ServerHello; its remaining datagrams use Handshake keys.",
            "Handshake ACK optionally sent after second server datagram; blocked graph is not a real QUIC deadlock.",
            "0RTT acceptance/rejection and application replay policy are declared; no exactly-once guarantee.",
            "TCP HRR, combined events, buffered pre-Retry 0RTT, general loss recovery, HTTP settings and background tickets remain unimplemented.",
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
            "retry": [100],
            "client_hello_retry": [1200],
            "hrr": [1200],
            "client_hello_hrr": [1200],
            "failure": [1200],
        },
    }


def scenarios():
    rows = {}
    for event_name in (
        "none",
        "hrr",
        "retry",
        "psk_unknown_fallback",
        "psk_unknown_abort",
        "selected_binder_invalid",
    ):
        for authorized in (True, False):
            p = example()
            p.update(
                handshake_event=event_name, application_retry_authorized=authorized
            )
            if event_name == "psk_unknown_fallback":
                p["packets"]["server_flight"] = [1200, 1200, 1200]
            rows[event_name + "-retry-" + str(authorized)] = p
    for policy in ("reattempt", "wait_1rtt"):
        p = example()
        p.update(
            handshake_event="retry", retry_early_policy=policy, early_result="reject"
        )
        rows["retry-then-tls-reject-" + policy] = p
    for event_name in ("none", "hrr", "retry", "psk_unknown_fallback"):
        p = example()
        p.update(
            handshake_event=event_name,
            send_early=False,
            application_early_data_authorized=False,
            application_retry_authorized=False,
        )
        p["request_payload_bytes"] = 100
        p["response_payload_bytes"] = 200
        rows["noearly-" + event_name] = p
    p = example()
    p.update(
        handshake_event="retry", retry_token_bytes=800, client_hello_crypto_bytes=800
    )
    p["packets"]["retry"] = [900]
    p["packets"]["client_hello_retry"] = [1200, 1200, 1200]
    rows["retry-token-three-initials"] = p
    for valid in (False,):
        p = example()
        p.update(handshake_event="retry", retry_token_valid=valid)
        rows["retry-invalid-token"] = p
    return rows


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = (
        calculate(json.loads(args.inputs.read_text()))
        if args.inputs
        else {k: calculate(v) for k, v in scenarios().items()}
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
