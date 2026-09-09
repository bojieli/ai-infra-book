"""Self-written paper-and-pencil arithmetic; not FloatAP implementation code."""
from pathlib import Path
import json

def calculate():
    # Positive integer mantissas only: no exponent, sign, rounding or overflow model.
    a = [1, 2, 3, 4] * 4
    b = [5, 6, 7, 8] * 4
    m, rows = 4, 16
    direct = sum(x * y for x, y in zip(a, b))
    partials = [sum(x * ((y >> j) & 1) for x, y in zip(a, b)) for j in range(m)]
    reordered = sum((1 << j) * v for j, v in enumerate(partials))
    # Count only A's lower m-bit data cells; upper product bits and metadata excluded.
    original_a_bytes = len(a) * m // 8
    replicated_a_bytes = len(a) * m * m // 8
    formats = {}
    for name, e, mbits in [('FP32', 8, 23), ('FP16', 5, 10), ('BF16', 8, 7)]:
        formats[name] = {'e': e, 'm': mbits,
            'vfredsum_cycles': e + 4 * mbits + 10,
            'vfadd_cycles': 4 * e + 7 * mbits + 18,
            'vfmul_cycles': 5 * mbits + 2,
            'vfdot_cycles': 5 * e + mbits * mbits + 3 * mbits + 13}
    vector_length = 2304 * 32
    data_bytes = vector_length * 32 * 4
    return {
        'scope': 'Independent integer identity, selected storage cells and published Table II arithmetic only. No simulated or measured speedup.',
        'toy': {'a': a, 'b': b, 'mantissa_bits': m, 'physical_rows': rows,
            'direct_dot': direct, 'partials_lsb_first': partials, 'reordered_dot': reordered,
            'unreplicated_a_bytes': original_a_bytes,
            'replicated_a_lower_bits_bytes': replicated_a_bytes,
            'available_a_lower_bits_bytes': rows * m // 8,
            'unreplicated_terms_per_residency': rows,
            'replicated_terms_per_residency': rows // m,
            'unreplicated_residencies_for_16_terms': len(a) // rows,
            'replicated_residencies_for_16_terms': len(a) // (rows // m),
            'excluded': ['B storage', 'upper product bits', 'exponents', 'sign', 'tag/metadata', 'accumulator', 'load/store traffic', 'cycle timing', 'IEEE floating point rounding']},
        'table_ii': formats,
        'ideal_full_vector_vfdot_ratios': {
            'FP16_over_FP32': 2 * formats['FP32']['vfdot_cycles'] / formats['FP16']['vfdot_cycles'],
            'BF16_over_FP16': formats['FP16']['vfdot_cycles'] / formats['BF16']['vfdot_cycles'],
            'conditions': 'Identical full occupancy; two 16-bit half-chains; no other latency, bandwidth, capacity, quality or load/store limit.'},
        'capacity': {'FP32_elements_per_vector': vector_length,
            'data_vectors_per_core': 32, 'data_bytes_per_core': data_bytes,
            'data_MiB_per_core': data_bytes / 2**20,
            'cores': 110, 'aggregate_data_bytes': 110 * data_bytes,
            'aggregate_data_MiB': 110 * data_bytes / 2**20,
            'nominal_13B_FP32_weight_bytes': 13_000_000_000 * 4,
            'assumptions': '13B is a nominal teaching count, not independently verified OPT tensor inventory. Aggregate SRAM is distributed, not one shared pool.'},
        'area': {'A100_total_mm2': 826, 'A100_SM_count': 108,
            'whole_area_divided_by_SM_count_mm2': 826 / 108,
            'FloatAP_total_mm2': 815, 'area_ratio': 815 / 826,
            'scope': 'Whole GPU area/count allocation, not an isolated SM layout measurement.'},
        'energy_assumptions': {'A100_assumed_watts': 0.6 * 400, 'FloatAP_modeled_watts': 352,
            'FP32_dot_TFLOPS_per_watt_ratio': (67.8 / 352) / (19.5 / 240),
            'BF16_dot_TFLOPS_per_watt_ratio_vs_TC': (717 / 352) / (312 / 240),
            'scope': 'Arithmetic under paper power and peak throughput assumptions; not measured joules/request.'},
        'listing_2_literal_order_caveat': {
            'one_positive_mantissa_pair': [1, 1], 'exact_integer_product': 1,
            'final_iteration_add_then_double': 2 * 1,
            'scope': 'Literal paper Listing 2 ends each bit iteration with doubling, unlike Eq. 2. May be pseudocode convention/typography; author implementation not checked.'}}

if __name__ == '__main__':
    result = calculate()
    assert result['toy']['direct_dot'] == result['toy']['reordered_dot'] == 280
    Path(__file__).with_name('budget.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
