"""Finite selective-ID ACK/advertised-prefix window teaching protocol.

This is not TCP/QUIC or any RFC congestion-control implementation.
"""

from fractions import Fraction as F
from collections import Counter
import heapq
import json


def number(value, name, positive=False):
    if type(value) not in (int, str):
        raise ValueError(name + " requires integer/rational string")
    try:
        out = F(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(name) from exc
    if out < 0 or positive and out == 0:
        raise ValueError(name)
    return out


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name)
    return value


def calculate(
    input_bytes=30_000_000,
    output_bytes=5_000_000,
    segment_bytes=25_000,
    upload_bits_per_second=20_000_000,
    download_bits_per_second=100_000_000,
    forward_propagation_seconds="1/20",
    reverse_propagation_seconds="1/20",
    initial_window_bytes=50_000,
    max_window_bytes=1_000_000,
    receive_window_bytes=1_000_000,
    ack_growth_bytes=25_000,
    data_header_bytes=40,
    ack_bytes=40,
    rto_seconds="1",
    drop_upload_packet=None,
    drop_download_packet=None,
    model_seconds="3/10",
    connection_ready_seconds="0",
    handshake=None,
    max_total_packets=10000,
    request_count=4,
    strategy="reuse_warm",
    submit_on="complete_received",
    think_seconds="0",
    initial_upload_window_bytes=None,
    initial_download_window_bytes=None,
    loss_request_id=1,
):
    scenario = locals().copy()
    integer(request_count, "request_count", 1)
    if request_count > 100:
        raise ValueError("At most 100 requests")
    if strategy not in ("fresh", "ticket", "reuse_reset", "reuse_warm"):
        raise ValueError("strategy")
    if submit_on not in ("complete_received", "quiet"):
        raise ValueError("submit_on")
    think = number(think_seconds, "think time")
    integer(loss_request_id, "loss_request_id", 1)
    if loss_request_id > request_count:
        raise ValueError("loss request outside sequence")
    for name in (
        "input_bytes",
        "output_bytes",
        "segment_bytes",
        "initial_window_bytes",
        "max_window_bytes",
        "receive_window_bytes",
        "max_total_packets",
    ):
        integer(scenario[name], name, 1)
    for name in ("ack_growth_bytes", "data_header_bytes", "ack_bytes"):
        integer(scenario[name], name)
    if max_total_packets > 100000:
        raise ValueError("Hard safety cap100000 packets")
    initial = {
        "upload": (
            initial_window_bytes
            if initial_upload_window_bytes is None
            else initial_upload_window_bytes
        ),
        "download": (
            initial_window_bytes
            if initial_download_window_bytes is None
            else initial_download_window_bytes
        ),
    }
    for name, value in initial.items():
        integer(value, name + " initial window", 1)
        if value > max_window_bytes:
            raise ValueError("Initial direction window exceeds cap")
        size = input_bytes if name == "upload" else output_bytes
        if value < min(segment_bytes, size):
            raise ValueError("Initial direction window cannot fit segment")
    if receive_window_bytes < min(segment_bytes, max(input_bytes, output_bytes)):
        raise ValueError("Receive window must fit the largest data segment")
    counts = {
        name: (count + segment_bytes - 1) // segment_bytes
        for name, count in (("upload", input_bytes), ("download", output_bytes))
    }
    if request_count * sum(counts.values()) > max_total_packets:
        raise ValueError("Packet count exceeds explicit simulation cap")
    for name, drop in (
        ("upload", drop_upload_packet),
        ("download", drop_download_packet),
    ):
        if drop is not None and (type(drop) is not int or not 0 <= drop < counts[name]):
            raise ValueError("Loss packet-ID outside transfer")
    if drop_upload_packet is not None and drop_download_packet is not None:
        raise ValueError(
            "At most one deliberately dropped first transmission per request"
        )
    rates = {
        "c2s": number(upload_bits_per_second, "upload rate", True),
        "s2c": number(download_bits_per_second, "download rate", True),
    }
    propagation = {
        "c2s": number(forward_propagation_seconds, "forward propagation"),
        "s2c": number(reverse_propagation_seconds, "reverse propagation"),
    }
    rto = number(rto_seconds, "RTO", True)
    model = number(model_seconds, "model")
    ready = number(connection_ready_seconds, "connection ready")
    if handshake is not None:
        if ready != 0:
            raise ValueError(
                "Sequence starts at zero; external connection ready unsupported"
            )
        if not isinstance(handshake, list) or len(handshake) > 8:
            raise ValueError("Handshake requires0..8 sequential messages")
        for row in handshake:
            if (
                not isinstance(row, dict)
                or set(row) != {"direction", "bytes"}
                or row["direction"] not in rates
            ):
                raise ValueError("Invalid handshake message")
            integer(row["bytes"], "handshake bytes", 1)
    if ready != 0:
        raise ValueError(
            "Sequence starts at zero; external connection ready unsupported"
        )
    links = {"c2s": F(0), "s2c": F(0)}
    transmissions = []
    arrivals = []
    acks = []
    windows = []
    timers = []
    application = []
    queue = []
    sequence = 0
    now = F(0)
    recovery_count = 0
    last_ack_event = F(0)

    def enqueue(time, priority, kind, data):
        nonlocal sequence
        sequence += 1
        heapq.heappush(queue, (time, priority, sequence, kind, data))

    def wire(direction, count, kind, **identity):
        start = max(now, links[direction])
        end = start + F(8 * count, rates[direction])
        links[direction] = end
        record = dict(
            id=len(transmissions),
            kind=kind,
            direction=direction,
            bytes=count,
            queued_seconds_exact=str(now),
            start_seconds_exact=str(start),
            end_seconds_exact=str(end),
            **identity,
        )
        transmissions.append(record)
        return end, end + propagation[direction], record

    # A connection owns directional congestion credit; file prefixes belong to requests.
    connections = {}
    requests = {}
    states = {}
    default_graph = [
        dict(direction="c2s", bytes=400),
        dict(direction="s2c", bytes=800),
    ] * 2
    graph = default_graph if handshake is None else handshake

    def submit(rid):
        new = strategy in ("fresh", "ticket") or rid == 1
        cid = rid if strategy in ("fresh", "ticket") else 1
        if new:
            connections[cid] = {
                name: dict(cwnd=value, outstanding=0) for name, value in initial.items()
            }
        elif strategy == "reuse_reset":
            for name in initial:
                connections[cid][name]["cwnd"] = initial[name]
        r = dict(
            request_id=rid,
            connection_id=cid,
            submit=now,
            ready=None,
            submitted_next=False,
            initial_cwnd={name: connections[cid][name]["cwnd"] for name in initial},
            quiet=None,
            complete_windows=None,
            quiet_windows=None,
        )
        requests[rid] = r
        application.append(
            dict(
                event="request_submit",
                request_id=rid,
                connection_id=cid,
                time_seconds_exact=str(now),
                cwnd_bytes=dict(r["initial_cwnd"]),
                outstanding_unique_bytes={
                    name: connections[cid][name]["outstanding"] for name in initial
                },
            )
        )
        for name, size, link, drop in (
            ("upload", input_bytes, "c2s", drop_upload_packet),
            ("download", output_bytes, "s2c", drop_download_packet),
        ):
            states[(rid, name)] = dict(
                request_id=rid,
                connection_id=cid,
                name=name,
                size=size,
                link=link,
                reverse="s2c" if link == "c2s" else "c2s",
                drop=drop if rid == loss_request_id else None,
                count=counts[name],
                active=False,
                next_packet=0,
                outstanding=0,
                acked=set(),
                received=set(),
                attempts={},
                sender_prefix=0,
                receiver_prefix=0,
                receiver_next=0,
                received_unique=0,
                peak_reorder_bytes=0,
                all_received=None,
                all_acked=None,
                last_ack=None,
                start=None,
            )
        selected = (graph[:2] if strategy == "ticket" else graph) if new else []
        r["handshake"] = selected
        if selected:
            enqueue(now, 2, "handshake", (rid, 0))
        else:
            r["ready"] = now
            enqueue(now, 2, "start", (rid, "upload"))

    def connection(s):
        return connections[s["connection_id"]][s["name"]]

    def maybe_next(rid):
        r = requests[rid]
        pair = [states[(rid, name)] for name in ("upload", "download")]
        if all(s["all_acked"] is not None for s in pair):
            r["quiet"] = max(s["last_ack"] for s in pair)
            r["quiet_windows"] = {
                name: dict(connections[r["connection_id"]][name]) for name in initial
            }
        if (
            states[(rid, "download")]["all_received"] is not None
            and r["complete_windows"] is None
        ):
            r["complete_windows"] = {
                name: dict(connections[r["connection_id"]][name]) for name in initial
            }
        endpoint = (
            states[(rid, "download")]["all_received"]
            if submit_on == "complete_received"
            else r["quiet"]
        )
        if endpoint is not None and not r["submitted_next"] and rid < request_count:
            r["submitted_next"] = True
            enqueue(endpoint + think, 2, "submit", rid + 1)

    def payload(s, p):
        return min(segment_bytes, s["size"] - p * segment_bytes)

    def snapshot(s, reason, **extra):
        windows.append(
            dict(
                transfer=s["name"],
                time_seconds_exact=str(now),
                reason=reason,
                request_id=s["request_id"],
                connection_id=s["connection_id"],
                cwnd_bytes=connection(s)["cwnd"],
                connection_outstanding_unique_bytes=connection(s)["outstanding"],
                outstanding_unique_bytes=s["outstanding"],
                sender_known_prefix_bytes=s["sender_prefix"],
                advertised_right_edge_bytes=s["sender_prefix"] + receive_window_bytes,
                receiver_prefix_bytes=s["receiver_prefix"],
                next_packet=s["next_packet"],
                **extra,
            )
        )

    def transmit(s, p, retransmit=False):
        length = payload(s, p)
        attempt = s["attempts"].get(p, 0) + 1
        s["attempts"][p] = attempt
        dropped = s["drop"] == p and attempt == 1
        end, arrival, record = wire(
            s["link"],
            length + data_header_bytes,
            "data",
            transfer=s["name"],
            request_id=s["request_id"],
            connection_id=s["connection_id"],
            packet=p,
            offset=p * segment_bytes,
            payload_bytes=length,
            attempt=attempt,
            dropped=dropped,
            retransmission=retransmit,
        )
        if not dropped:
            enqueue(
                arrival,
                1,
                "data",
                ((s["request_id"], s["name"]), p, attempt, record["id"]),
            )
        enqueue(
            end + rto,
            3,
            "timer",
            ((s["request_id"], s["name"]), p, attempt, record["id"]),
        )

    def pump(s):
        if not s["active"]:
            return
        while s["next_packet"] < s["count"]:
            p = s["next_packet"]
            length = payload(s, p)
            if (
                connection(s)["outstanding"] + length > connection(s)["cwnd"]
                or p * segment_bytes + length
                > s["sender_prefix"] + receive_window_bytes
            ):
                break
            s["outstanding"] += length
            connection(s)["outstanding"] += length
            s["next_packet"] += 1
            snapshot(s, "admit_new", packet=p, payload_bytes=length)
            transmit(s, p)
        if s["next_packet"] < s["count"]:
            p = s["next_packet"]
            length = payload(s, p)
            snapshot(
                s,
                "blocked",
                packet=p,
                send_window_blocked=connection(s)["outstanding"] + length
                > connection(s)["cwnd"],
                receive_window_blocked=p * segment_bytes + length
                > s["sender_prefix"] + receive_window_bytes,
            )

    enqueue(ready, 2, "submit", 1)
    processed = 0
    while queue:
        now = queue[0][0]
        # Drain all arrivals/ACKs before same-time timers; only then admit new data.
        while queue and queue[0][0] == now:
            _, _, _, kind, data = heapq.heappop(queue)
            processed += 1
            if processed > request_count * (sum(counts.values()) * 20 + 100):
                raise ValueError("Finite event budget exceeded")
            if kind == "submit":
                submit(data)
            elif kind == "handshake":
                rid, index = data
                r = requests[rid]
                row = r["handshake"][index]
                _, arrival, record = wire(
                    row["direction"],
                    row["bytes"],
                    "handshake",
                    request_id=rid,
                    connection_id=r["connection_id"],
                    message=index,
                )
                record["arrival_seconds_exact"] = str(arrival)
                if index + 1 < len(r["handshake"]):
                    enqueue(arrival, 2, "handshake", (rid, index + 1))
                else:
                    r["ready"] = arrival
                    enqueue(arrival, 2, "start", (rid, "upload"))
            elif kind == "start":
                s = states[data]
                s["active"] = True
                s["start"] = now
                snapshot(s, "start")
            elif kind == "data":
                name, p, attempt, tx = data
                s = states[name]
                duplicate = p in s["received"]
                if not duplicate:
                    s["received"].add(p)
                    s["received_unique"] += payload(s, p)
                    while s["receiver_next"] in s["received"]:
                        s["receiver_prefix"] += payload(s, s["receiver_next"])
                        s["receiver_next"] += 1
                    s["peak_reorder_bytes"] = max(
                        s["peak_reorder_bytes"],
                        s["received_unique"] - s["receiver_prefix"],
                    )
                arrivals.append(
                    dict(
                        transfer=s["name"],
                        request_id=s["request_id"],
                        connection_id=s["connection_id"],
                        packet=p,
                        attempt=attempt,
                        transmission=tx,
                        time_seconds_exact=str(now),
                        duplicate=duplicate,
                        unique_received_bytes=s["received_unique"],
                        cumulative_prefix_bytes=s["receiver_prefix"],
                    )
                )
                end, ack_arrival, record = wire(
                    s["reverse"],
                    ack_bytes,
                    "ack",
                    transfer=s["name"],
                    request_id=s["request_id"],
                    connection_id=s["connection_id"],
                    packet=p,
                    attempt=attempt,
                    prefix_bytes=s["receiver_prefix"],
                )
                enqueue(
                    ack_arrival, 0, "ack", (name, p, s["receiver_prefix"], record["id"])
                )
                if s["receiver_prefix"] == s["size"] and s["all_received"] is None:
                    s["all_received"] = now
                    application.append(
                        dict(
                            request_id=s["request_id"],
                            event=s["name"] + "_complete_received",
                            time_seconds_exact=str(now),
                        )
                    )
                    if s["name"] == "upload":
                        application.append(
                            dict(
                                request_id=s["request_id"],
                                event="model_start",
                                time_seconds_exact=str(now),
                            )
                        )
                        application.append(
                            dict(
                                request_id=s["request_id"],
                                event="model_finish",
                                time_seconds_exact=str(now + model),
                            )
                        )
                        enqueue(now + model, 2, "start", (s["request_id"], "download"))
                    maybe_next(s["request_id"])
            elif kind == "ack":
                name, p, prefix, tx = data
                s = states[name]
                new = p not in s["acked"]
                before = s["outstanding"]
                prefix_before = s["sender_prefix"]
                if new:
                    s["acked"].add(p)
                    s["outstanding"] -= payload(s, p)
                    connection(s)["outstanding"] -= payload(s, p)
                    connection(s)["cwnd"] = min(
                        max_window_bytes,
                        connection(s)["cwnd"] + min(payload(s, p), ack_growth_bytes),
                    )
                s["sender_prefix"] = max(s["sender_prefix"], prefix)
                s["last_ack"] = now
                last_ack_event = now
                acks.append(
                    dict(
                        transfer=s["name"],
                        request_id=s["request_id"],
                        connection_id=s["connection_id"],
                        packet=p,
                        transmission=tx,
                        time_seconds_exact=str(now),
                        newly_acked=new,
                        released_unique_bytes=before - s["outstanding"],
                        new_receive_credit_bytes=s["sender_prefix"] - prefix_before,
                        carried_prefix_bytes=prefix,
                    )
                )
                snapshot(s, "ack", packet=p, newly_acked=new)
                if len(s["acked"]) == s["count"] and s["all_acked"] is None:
                    s["all_acked"] = now
                maybe_next(s["request_id"])
            elif kind == "timer":
                name, p, attempt, tx = data
                s = states[name]
                if p in s["acked"]:
                    status = "cancelled_by_ack"
                elif attempt != s["attempts"][p]:
                    status = "obsolete_generation"
                else:
                    if recovery_count or p != s["drop"] or attempt != 1:
                        raise ValueError(
                            f"Outside finite one-loss contract: effective timeout {name}:{p}, attempt{attempt}; raise RTO or change rates/windows"
                        )
                    recovery_count += 1
                    status = "retransmit_once"
                    transmit(s, p, True)
                    snapshot(s, "retransmit", packet=p)
                timers.append(
                    dict(
                        transfer=s["name"],
                        request_id=s["request_id"],
                        connection_id=s["connection_id"],
                        packet=p,
                        attempt=attempt,
                        transmission=tx,
                        time_seconds_exact=str(now),
                        status=status,
                    )
                )
        for state in states.values():
            pump(state)
    if any(
        s["all_received"] is None or s["all_acked"] is None or s["outstanding"]
        for s in states.values()
    ):
        raise ValueError("Finite protocol stalled without complete receive/ACK")
    request_results = []
    for rid, r in requests.items():
        pair = {name: states[(rid, name)] for name in ("upload", "download")}
        records = [row for row in transmissions if row.get("request_id") == rid]
        end = pair["download"]["all_received"]
        request_results.append(
            dict(
                request_id=rid,
                connection_id=r["connection_id"],
                submit_seconds_exact=str(r["submit"]),
                connection_ready_seconds_exact=str(r["ready"]),
                complete_received_seconds_exact=str(end),
                last_ack_seconds_exact=str(r["quiet"]),
                response_seconds_exact=str(end - r["submit"]),
                model_start_seconds_exact=str(pair["upload"]["all_received"]),
                model_finish_seconds_exact=str(pair["upload"]["all_received"] + model),
                input_bytes=input_bytes,
                output_bytes=output_bytes,
                initial_cwnd_bytes=r["initial_cwnd"],
                data_header_wire_bytes=sum(
                    data_header_bytes for row in records if row["kind"] == "data"
                ),
                transmitted_payload_bytes=sum(
                    row.get("payload_bytes", 0)
                    for row in records
                    if row["kind"] == "data"
                ),
                link_busy_seconds_exact={
                    direction: str(
                        sum(
                            (
                                F(8 * row["bytes"], rates[direction])
                                for row in records
                                if row["direction"] == direction
                            ),
                            F(0),
                        )
                    )
                    for direction in links
                },
                windows_at_complete_received=r["complete_windows"],
                windows_at_last_ack=r["quiet_windows"],
                handshake_wait_seconds_exact=str(r["ready"] - r["submit"]),
                wire_bytes_by_kind=dict(
                    Counter(
                        {
                            kind: sum(
                                row["bytes"] for row in records if row["kind"] == kind
                            )
                            for kind in ("data", "ack", "handshake")
                        }
                    )
                ),
                retransmission_wire_bytes=sum(
                    row["bytes"] for row in records if row.get("retransmission")
                ),
                transfers={
                    name: dict(
                        start_seconds_exact=str(s["start"]),
                        complete_received_seconds_exact=str(s["all_received"]),
                        all_unique_acked_seconds_exact=str(s["all_acked"]),
                        unique_received_bytes=s["received_unique"],
                        packet_count=s["count"],
                        peak_reorder_buffer_bytes=s["peak_reorder_bytes"],
                    )
                    for name, s in pair.items()
                },
            )
        )
    return dict(
        calculation="finite-ack-window-sequence",
        scenario=scenario,
        requests=request_results,
        transmissions=transmissions,
        data_arrivals=arrivals,
        ack_arrivals=acks,
        window_events=windows,
        timer_events=timers,
        application_events=application,
        connections={
            cid: {name: dict(value) for name, value in c.items()}
            for cid, c in connections.items()
        },
        links={
            direction: dict(
                wire_bytes=sum(
                    r["bytes"] for r in transmissions if r["direction"] == direction
                ),
                busy_seconds_exact=str(
                    sum(
                        (
                            F(8 * r["bytes"], rates[direction])
                            for r in transmissions
                            if r["direction"] == direction
                        ),
                        F(0),
                    )
                ),
                available_seconds_exact=str(links[direction]),
            )
            for direction in links
        },
        summary=dict(
            complete_final_image_seconds_exact=request_results[-1][
                "complete_received_seconds_exact"
            ],
            protocol_last_ack_seconds_exact=str(last_ack_event),
            recoveries=recovery_count,
            unique_input_bytes=request_count * input_bytes,
            unique_output_bytes=request_count * output_bytes,
            response_sum_seconds_exact=str(
                sum((F(r["response_seconds_exact"]) for r in request_results), F(0))
            ),
            handshake_wait_seconds_exact=str(
                sum(
                    (F(r["handshake_wait_seconds_exact"]) for r in request_results),
                    F(0),
                )
            ),
            handshake_wire_bytes=sum(
                r["bytes"] for r in transmissions if r["kind"] == "handshake"
            ),
            total_wire_bytes=sum(r["bytes"] for r in transmissions),
            complete_wall_seconds_exact=request_results[-1][
                "complete_received_seconds_exact"
            ],
            quiet_wall_seconds_exact=str(last_ack_event),
            measured_seconds=None,
        ),
    )
