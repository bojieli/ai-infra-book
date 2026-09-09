"""Small self-written arithmetic example, not a Sparsepipe simulator."""
from pathlib import Path
import json

D = Path(__file__).resolve().parent
A = [[1, 2, 0, 0], [0, 3, 4, 0], [0, 0, 5, 0], [0, 0, 0, 6]]
u = [1, 1, 1, 1]
n = len(u)
entries = [(i, j, A[i][j]) for i in range(n) for j in range(n) if A[i][j]]


def vxm(vector):
    return [sum(vector[i] * A[i][j] for i in range(n)) for j in range(n)]


y = vxm(u)
v = [x + 1 for x in y]
z = vxm(v)
assert y == [1, 5, 9, 6] and v == [2, 6, 10, 7] and z == [2, 22, 74, 42]

# A topologically legal ideal schedule; step is not a clock cycle.
# Each column completes OS, then that scalar passes through f, then any
# buffered matrix records with a ready row input can contribute to IS.
resident = {}
ready = {}
partial = [0] * n
consumed = set()
trace = []
for col in range(n):
    loaded = [(i, j, value) for i, j, value in entries if j == col]
    for i, j, value in loaded:
        resident[(i, j)] = value
    scalar_y = sum(u[i] * value for i, _, value in loaded)
    ready[col] = scalar_y + 1
    used = []
    for (i, j), value in list(resident.items()):
        if i in ready:
            partial[j] += ready[i] * value
            consumed.add((i, j))
            used.append([i, j])
            del resident[(i, j)]
    trace.append({"column": col, "loaded_coordinates": [[i, j] for i, j, _ in loaded], "completed_y": scalar_y, "ready_v": ready[col], "IS_consumed_coordinates": used, "partial_z_after_step": partial[:], "remaining_value_coordinates": [list(k) for k in resident]})
assert partial == z and len(consumed) == len(entries) and not resident

value_bytes, coordinate_bytes, pointer_bytes = 8, 4, 4
record_bytes = len(entries) * (value_bytes + coordinate_bytes)
vector_bytes = n * value_bytes
both_pointer_tables = 2 * (n + 1) * pointer_bytes
compulsory_vector_io = 2 * vector_bytes  # read u, write z
separate_intermediate_io = 4 * vector_bytes  # write/read y, write/read v
separate = 2 * record_bytes + both_pointer_tables + compulsory_vector_io + separate_intermediate_io
producer_consumer = 2 * record_bytes + both_pointer_tables + compulsory_vector_io
cross_iteration = record_bytes + both_pointer_tables + compulsory_vector_io
assert [record_bytes, both_pointer_tables, separate, producer_consumer, cross_iteration] == [72, 40, 376, 248, 176]

result = {
    "kind": "self_written_exact_arithmetic_and_dependency_trace_not_paper_measurement",
    "matrix": A, "u": u, "y": y, "v": v, "z": z,
    "semantics": "y=uA; v_j=y_j+1; z=vA, same constant sparse A in both vxm operations",
    "n": n, "nnz": len(entries), "value_bytes": value_bytes, "coordinate_bytes": coordinate_bytes, "pointer_bytes": pointer_bytes,
    "matrix_record_bytes_one_orientation": record_bytes,
    "two_pointer_tables_bytes": both_pointer_tables,
    "vector_bytes": vector_bytes,
    "common_input_output_vector_bytes": compulsory_vector_io,
    "cases": [
        {"name": "separate", "matrix_record_io": 144, "pointer_io": 40, "input_output_io": 64, "intermediate_io": 128, "total_bytes": separate},
        {"name": "producer_consumer_only", "matrix_record_io": 144, "pointer_io": 40, "input_output_io": 64, "intermediate_io": 0, "total_bytes": producer_consumer},
        {"name": "producer_consumer_and_cross_iteration", "matrix_record_io": 72, "pointer_io": 40, "input_output_io": 64, "intermediate_io": 0, "total_bytes": cross_iteration},
    ],
    "producer_consumer_saved_bytes": separate - producer_consumer,
    "additional_cross_iteration_saved_bytes": producer_consumer - cross_iteration,
    "dependency_trace": trace,
    "assumptions": [
        "Ideal byte traffic, no cache-line overfetch, alignment, bus transaction or DRAM burst rounding.",
        "u and z accumulation stay on chip; y/v are not externally observable intermediate outputs.",
        "Both row/column pointer arrays read once in all three cases; each nonzero record has one 64-bit value and one 32-bit coordinate in its selected compressed orientation.",
        "Cross-iteration case retains/locally converts every needed nonzero until its other orientation consumes it, with no OOM/reload or extra DRAM conversion traffic.",
        "Separate and producer-consumer-only baselines have no cross-iteration matrix record cache hit; this is an explicit baseline assumption.",
        "Offline preprocessing, format construction, row reordering, on-chip copies, mapping metadata, allocator reservations and control traffic excluded.",
        "Trace is a topological witness only, not cycle timing, real controller implementation, occupancy model or speedup measurement.",
    ],
    "capacity_caution": "Two complete unblocked on-chip copies of value/coordinate records alone would require 144 B, not the 72 B external-read count. Pointer tables, vectors, mapping/consumption state and reserved slots add capacity; actual Sparsepipe streams windows and may use blocked shared data.",
}
(D / "byte-example.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"totals_B": [separate, producer_consumer, cross_iteration], "savings_B": [128, 72], "output": z}))
