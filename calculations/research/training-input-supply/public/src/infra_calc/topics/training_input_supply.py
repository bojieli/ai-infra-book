"""Finite input supply and checkpoint storage contention; rational event times."""

from fractions import Fraction
from infra_calc.sources import model_config, provenance
from infra_calc.models import qwen3
from infra_calc.units import positive_int
from infra_calc.topics.pipeline_schedule import peak_intervals


def schedule(nodes):
    """Deterministic earliest-ready nonpreemptive list scheduler."""
    pending = {x["id"]: x for x in nodes}
    done = {}
    free = {}
    while pending:
        ready = []
        for name, node in pending.items():
            if all(d in done for d in node["deps"]):
                start = max(
                    [free.get(node["resource"], Fraction(0))]
                    + [done[d]["end"] for d in node["deps"]]
                )
                ready.append((start, node["priority"], name))
        if not ready:
            raise ValueError("Cyclic event dependencies")
        start, _, name = min(ready)
        node = pending.pop(name)
        end = start + node["duration"]
        done[name] = {**node, "start": start, "end": end}
        free[node["resource"]] = end
    return done


def calculate(
    samples=None,
    pack_tokens=512,
    host_slots=2,
    device_slots=2,
    storage_bytes_per_second=2_000_000_000,
    h2d_bytes_per_second=12_000_000_000,
    packing_ns=100_000,
    consume_ns=2_000_000,
    checkpoint_every=2,
    snapshot_ns=1_000_000,
    snapshot_slots=1,
    shared_storage=True,
):
    """One CPU worker; no sample split/drop; next-fit packing and fixed padded packs."""
    if samples is None:
        samples = [
            dict(tokens=n, stored_bytes=4 * n, cpu_ns=100_000 + 500 * n)
            for n in [128, 256, 192, 320, 64, 448, 256, 256]
        ]
    if not isinstance(samples, list) or not samples:
        raise ValueError("Nonempty sample records required")
    for name, value in locals().copy().items():
        if name in ("samples", "shared_storage"):
            continue
        positive_int(
            value,
            name,
            allow_zero=name
            in ("packing_ns", "consume_ns", "checkpoint_every", "snapshot_ns"),
        )
    if type(shared_storage) is not bool:
        raise ValueError("shared_storage must be boolean")
    cfg = model_config("qwen3-8b")
    qwen3.validate(cfg)
    if pack_tokens > cfg["max_position_embeddings"]:
        raise ValueError("Context limit exceeded")
    params = sum(w.parameters for w in qwen3.weights(cfg))
    checkpoint_bytes = 14 * params
    packs = []
    current = []
    used = 0
    for i, s in enumerate(samples):
        if set(s) != {"tokens", "stored_bytes", "cpu_ns"}:
            raise ValueError("Each sample requires tokens, stored_bytes, cpu_ns")
        for key, value in s.items():
            positive_int(value, key, allow_zero=key == "cpu_ns")
        if s["tokens"] > pack_tokens:
            raise ValueError("Oversize sample; splitting not enabled")
        if used + s["tokens"] > pack_tokens:
            packs.append(current)
            current = []
            used = 0
        current.append(i)
        used += s["tokens"]
    if current:
        packs.append(current)
    # Packed IDs int64, labels int64, validity bool, segment identity int32.
    wire_bytes = pack_tokens * (8 + 8 + 1 + 4)
    rows = []
    nodes = []
    checkpoint_indices = []

    def add(name, res, ns=None, size=None, rate=None, deps=(), priority=0):
        duration = Fraction(ns, 10**9) if ns is not None else Fraction(size, rate)
        nodes.append(
            dict(
                id=name,
                resource=res,
                duration=duration,
                deps=list(deps),
                priority=priority,
            )
        )

    for p, ids in enumerate(packs):
        stored = sum(samples[i]["stored_bytes"] for i in ids)
        tokens = sum(samples[i]["tokens"] for i in ids)
        rows.append(
            dict(
                pack=p,
                samples=ids,
                valid_tokens=tokens,
                padding_tokens=pack_tokens - tokens,
                stored_bytes=stored,
                wire_bytes=wire_bytes,
            )
        )
        read_deps = [f"H{p-host_slots}"] if p >= host_slots else []
        if p:
            read_deps.append(f"R{p-1}")
        add(
            f"R{p}",
            "storage" if shared_storage else "read_storage",
            size=stored,
            rate=storage_bytes_per_second,
            deps=read_deps,
            priority=0,
        )
        add(
            f"P{p}",
            "cpu",
            ns=sum(samples[i]["cpu_ns"] for i in ids) + packing_ns,
            deps=[f"R{p}"] + ([f"P{p-1}"] if p else []),
        )
        add(
            f"H{p}",
            "h2d",
            size=wire_bytes,
            rate=h2d_bytes_per_second,
            deps=[f"P{p}"]
            + ([f"C{p-device_slots}"] if p >= device_slots else [])
            + ([f"H{p-1}"] if p else []),
        )
        consume_deps = [f"H{p}"] + ([f"C{p-1}"] if p else [])
        if p and checkpoint_every and p % checkpoint_every == 0:
            consume_deps.append(f"S{p-1}")
        add(f"C{p}", "device", ns=consume_ns, deps=consume_deps)
        if checkpoint_every and (p + 1) % checkpoint_every == 0:
            j = len(checkpoint_indices)
            snapshot_deps = [f"C{p}"]
            if j >= snapshot_slots:
                snapshot_deps.append(f"W{checkpoint_indices[j-snapshot_slots]}")
            add(f"S{p}", "device", ns=snapshot_ns, deps=snapshot_deps, priority=1)
            add(
                f"W{p}",
                "storage" if shared_storage else "write_storage",
                size=checkpoint_bytes,
                rate=storage_bytes_per_second,
                deps=[f"S{p}"]
                + ([f"W{checkpoint_indices[-1]}"] if checkpoint_indices else []),
                priority=1,
            )
            checkpoint_indices.append(p)
    events = schedule(nodes)
    host = []
    device = []
    snapshots = []
    for p, row in enumerate(rows):
        host.append(
            (
                events[f"R{p}"]["start"],
                events[f"H{p}"]["end"],
                row["stored_bytes"] + wire_bytes,
            )
        )
        device.append((events[f"H{p}"]["start"], events[f"C{p}"]["end"], wire_bytes))
    for p in checkpoint_indices:
        snapshots.append(
            (events[f"S{p}"]["start"], events[f"W{p}"]["end"], checkpoint_bytes)
        )
    training_end = events[f"C{len(packs)-1}"]["end"]
    durable_end = max(e["end"] for e in events.values())
    compute_service = len(packs) * Fraction(consume_ns, 10**9)
    snapshot_service = sum(
        (
            events[f"S{p}"]["duration"]
            for p in checkpoint_indices
            if events[f"S{p}"]["end"] <= training_end
        ),
        Fraction(0),
    )

    def intervals(values):
        return [
            dict(start_exact=str(a), end_exact=str(b), bytes=n) for a, b, n in values
        ]

    def state(values):
        return dict(
            peak_reserved_bytes=peak_intervals(values),
            byte_seconds_exact=str(
                sum(((b - a) * n for a, b, n in values), Fraction(0))
            ),
        )

    return dict(
        calculation="qwen8-training-input-supply",
        sources=provenance("qwen3-8b"),
        scenario=dict(
            samples=samples,
            pack_tokens=pack_tokens,
            host_slots=host_slots,
            device_slots=device_slots,
            storage_bytes_per_second=storage_bytes_per_second,
            h2d_bytes_per_second=h2d_bytes_per_second,
            packing_ns=packing_ns,
            consume_ns=consume_ns,
            checkpoint_every=checkpoint_every,
            snapshot_ns=snapshot_ns,
            snapshot_slots=snapshot_slots,
            shared_storage=shared_storage,
        ),
        packs=rows,
        events=[
            dict(
                id=e["id"],
                resource=e["resource"],
                deps=e["deps"],
                start_exact=str(e["start"]),
                end_exact=str(e["end"]),
                service_exact=str(e["duration"]),
            )
            for e in events.values()
        ],
        lifetimes=dict(
            host=intervals(host),
            device=intervals(device),
            snapshot=intervals(snapshots),
        ),
        buffers=dict(host=state(host), device=state(device), snapshot=state(snapshots)),
        summary=dict(
            samples=len(samples),
            valid_tokens=sum(s["tokens"] for s in samples),
            padding_tokens=len(packs) * pack_tokens - sum(s["tokens"] for s in samples),
            packs=len(packs),
            input_storage_bytes=sum(s["stored_bytes"] for s in samples),
            h2d_bytes=len(packs) * wire_bytes,
            checkpoint_parameters=params,
            checkpoint_bytes_each=checkpoint_bytes,
            checkpoint_write_bytes=len(checkpoint_indices) * checkpoint_bytes,
            cpu_core_seconds_exact=str(
                sum(
                    (e["duration"] for e in events.values() if e["resource"] == "cpu"),
                    Fraction(0),
                )
            ),
            training_end_exact=str(training_end),
            all_durable_exact=str(durable_end),
            device_compute_service_exact=str(compute_service),
            snapshot_service_before_training_end_exact=str(snapshot_service),
            device_wait_exact=str(training_end - compute_service - snapshot_service),
            target_sample_rate_exact=(
                str(Fraction(len(samples)) / compute_service)
                if compute_service
                else None
            ),
            target_input_bytes_per_second_exact=(
                str(Fraction(sum(s["stored_bytes"] for s in samples)) / compute_service)
                if compute_service
                else None
            ),
            target_h2d_bytes_per_second_exact=(
                str(Fraction(len(packs) * wire_bytes) / compute_service)
                if compute_service
                else None
            ),
        ),
        scope=[
            "Pre-tokenized sample geometry supplied by caller; next-fit without splitting, dropping or implicit EOS insertion.",
            "One CPU worker; stored bytes, preparation/consumption service and bandwidth are explicit workload assumptions, not measured Qwen performance.",
            "IDs/labels int64, validity bool, segment IDs int32. Segment-aware consumer assumed; full quadratic masks, tokenizer and GPU mask creation excluded.",
            "Two serial storage resources or one shared nonpreemptive resource. Earliest-ready, reads win ties. Checkpoint writes are whole payload jobs, not optimal I/O arbitration.",
            "Checkpoint BF16 weights plus FP32 master and two moments =14P, same declared layout as checkpoint_async; gradients and arbitrary runtime state excluded.",
            "Snapshot uses device service and stalls next consume, bounded snapshot slots retained through write completion; durability equals write completion in this contract.",
            "Host reservation conservatively includes stored pack plus packed wire tensors from read start to H2D end. Runtime peaks and metadata/workspace excluded.",
        ],
    )


def markdown(result):
    """Render all result leaves without omitting conditional scope or exact times."""
    import json

    return (
        "# Training input supply and checkpoint contention\n\n```json\n"
        + json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n```\n"
    )
