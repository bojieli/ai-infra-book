"""Single-device Qwen/Llama70 capacity using actual shapes and declared quantization.

Low-bit formats are controlled storage schemes, not downloaded quantized models.
"""

from math import prod
from ..models import qwen3, qwen3_moe, llama70
from ..sources import model_config, provenance
from ..units import positive_int
from . import state


def packed_matrix(
    shape: tuple[int, ...], bits: int, group_size: int, scale_bytes: int
) -> dict:
    """Pack rows independently; the last K group may be incomplete."""
    for name, value in (
        ("bits", bits),
        ("group_size", group_size),
        ("scale_bytes", scale_bytes),
    ):
        positive_int(value, name)
    if len(shape) != 2 or bits not in (4, 8):
        raise ValueError("Grouped packing requires a matrix and 4 or 8 bits")
    for width in shape:
        positive_int(width, "matrix dimension")
    rows, width = shape
    return dict(
        packed_bytes=rows * ((width * bits + 7) // 8),
        scale_bytes=rows * ((width + group_size - 1) // group_size) * scale_bytes,
        groups=rows * ((width + group_size - 1) // group_size),
    )


def calculate(
    model: str = "qwen3-8b",
    length: int = 8192,
    capacities: list[int] | None = None,
    workspace_bytes: int = 2 * 2**30,
    group_size: int = 128,
    scale_bytes: int = 2,
) -> dict:
    capacities = (
        [24 * 10**9, 48 * 10**9, 80 * 10**9] if capacities is None else capacities
    )
    if not isinstance(capacities, list) or not capacities:
        raise ValueError("At least one explicit capacity budget is required")
    for capacity in capacities:
        positive_int(capacity, "capacity bytes")
    positive_int(workspace_bytes, "workspace bytes", allow_zero=True)
    positive_int(group_size, "group size")
    positive_int(scale_bytes, "scale bytes")
    c = model_config(model)
    if c["model_type"] == "qwen3":
        weights = qwen3.weights(c)
    elif c["model_type"] == "qwen3_moe":
        weights = qwen3_moe.weights(c)
    elif model == llama70.MODEL:
        weights = llama70.weights(c)
    else:
        raise ValueError(
            "Capacity adapter supports audited Qwen3 Dense/MoE and the pinned Llama70 model"
        )
    if model == llama70.MODEL:
        positive_int(length, "retained length")
        if length > c["max_position_embeddings"]:
            raise ValueError("Retained length exceeds pinned Llama70 context limit")
        kv = (
            2
            * c["num_hidden_layers"]
            * c["num_key_value_heads"]
            * c["head_dim"]
            * length
            * 2
        )
    else:
        kv = state.calculate(model, length)["summary"]["resident_bytes"]
    formats, comparisons = [], []
    for bits in (16, 8, 4):
        tensors = []
        for weight in weights:
            eligible = (
                len(weight.shape) == 2
                and weight.name not in ("model.embed_tokens.weight", "lm_head.weight")
                and not weight.name.endswith(".mlp.gate.weight")
            )
            if bits < 16 and eligible:
                packed = packed_matrix(weight.shape, bits, group_size, scale_bytes)
                payload, metadata = (
                    packed["packed_bytes"] * weight.copies,
                    packed["scale_bytes"] * weight.copies,
                )
            else:
                payload, metadata = 2 * weight.parameters, 0
            tensors.append(
                dict(
                    name=weight.name,
                    shape=weight.shape,
                    copies=weight.copies,
                    parameters=weight.parameters,
                    low_bit_eligible=eligible,
                    payload_bytes=payload,
                    scale_bytes=metadata,
                    total_bytes=payload + metadata,
                )
            )
        payload = sum(row["payload_bytes"] for row in tensors)
        scales = sum(row["scale_bytes"] for row in tensors)
        formats.append(
            dict(
                matrix_bits=bits,
                payload_bytes=payload,
                scale_bytes=scales,
                total_weight_bytes=payload + scales,
                tensors=tensors,
            )
        )
        for capacity in capacities:
            available = capacity - payload - scales - workspace_bytes
            requests = max(0, available // kv)
            comparisons.append(
                dict(
                    matrix_bits=bits,
                    capacity_bytes=capacity,
                    weight_bytes=payload + scales,
                    workspace_bytes=workspace_bytes,
                    kv_bytes_per_request=kv,
                    available_for_kv_bytes=available,
                    maximum_requests=requests,
                    weights_and_workspace_fit=available >= 0,
                    resident_at_maximum_bytes=payload
                    + scales
                    + workspace_bytes
                    + requests * kv,
                    next_request_exceeds_capacity=payload
                    + scales
                    + workspace_bytes
                    + (requests + 1) * kv
                    > capacity,
                )
            )
    return dict(
        schema_version=1,
        calculation=(
            "llama70-single-device-capacity-scan"
            if model == llama70.MODEL
            else "qwen-single-device-capacity-scan"
        ),
        model=model,
        scenario=dict(
            length=length,
            capacities=capacities,
            workspace_bytes=workspace_bytes,
            group_size=group_size,
            scale_bytes=scale_bytes,
            kv_element_bytes=2,
        ),
        sources=provenance(model),
        storage_formats=formats,
        capacity_comparisons=comparisons,
        summary=dict(
            logical_parameters=sum(weight.parameters for weight in weights),
            bf16_weight_bytes=formats[0]["total_weight_bytes"],
            eight_bit_scheme_bytes=formats[1]["total_weight_bytes"],
            four_bit_scheme_bytes=formats[2]["total_weight_bytes"],
            bf16_kv_bytes_per_request=kv,
            measured_resident_bytes=None,
        ),
        assumptions=[
            (
                "Shapes reuse the pinned public DeepSeek R1 Distill Llama70 adapter: 80 bias-free Llama layers, no Q/K head norms, untied vocabulary matrices; no nominal 70e9 substitution. This is TP=PP=DP=1 whole-model residency, not a distributed placement or kernel compatibility claim."
                if model == llama70.MODEL
                else "Shapes and copies reuse Qwen3 Dense/MoE weight enumeration audited against official checkpoint indices. MoE stores every expert, not only activated parameters."
            ),
            "BF16 baseline keeps all parameters at two bytes. Low-bit teaching schemes quantize eligible 2-D linear matrices per output row and K group, retaining embedding, vocabulary head, router and one-dimensional norm parameters as BF16.",
            "Each quantized row packs independently, rounding partial bytes upward; each ceil(K/group_size) group has scale_bytes metadata. Symmetric scheme has no zero points. No claim of a particular released quantized checkpoint, kernel support or quality equivalence.",
            "KV uses pinned full-history GQA geometry and BF16. Every concurrent request has the same retained length; no physical prefix sharing, paging slack, offloading or parallel replication.",
            "Capacities are explicit single-device byte budgets (defaults 24/48/80 decimal GB), not aggregate eight-card memory and not assertions about a specific SKU. Actual allocatable budget must account for reservations.",
            "Workspace is an explicit reserved budget, not a computed allocator peak. Maximum requests is conditional on it; temporary dequantization, graph pools and batch-dependent workspace may require more.",
            "Zero requests can mean weights/workspace already fail or insufficient room for one KV. The fit flag and signed remaining bytes distinguish these cases. No throughput or deployability is inferred.",
        ],
    )
