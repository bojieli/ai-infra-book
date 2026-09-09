"""Independent references and invariants that detect substantive accounting errors."""
import csv
import copy
import io
import json
import random
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from infra_calc.models import qwen3, qwen3_moe, forward
from infra_calc.schema import Scenario
from infra_calc.report import operator_csv
from infra_calc.sources import model_config, read_source, verify_sources
from infra_calc.topics import state, projection, experts, hyper_connections, v4_attention, transforms, v4_forward, k3_mla, k3_kda, attn_res, kda_chunk, kda_math, k3_forward, k3_checkpoint, cache_sequence, resource_basics, memory_concurrency, decode_budget, ring_collective, tree_collective, all_to_all, numa_staging, moe_dedup, capacity_scan, dense_placement, dense_communication, pipeline_schedule
from infra_calc import hardware
from infra_calc.traffic import account


class MoEAccounting(unittest.TestCase):
    def test_checkpoint_keys_and_bytes(self):
        for model in ('qwen3-30b-a3b', 'qwen3-235b-a22b'):
            with self.subTest(model=model):
                tensors = qwen3_moe.weights(model_config(model))
                index = json.loads(read_source(f'sources/{model}/model.safetensors.index.json'))
                keys = {w.name.format(layer=i) for w in tensors for i in range(w.copies)}
                self.assertEqual(keys, set(index['weight_map']))
                self.assertEqual(sum(w.parameters * 2 for w in tensors), index['metadata']['total_size'])

    def test_routing_changes_payload_not_arithmetic(self):
        for model in ('qwen3-30b-a3b', 'qwen3-235b-a22b'):
            scenario = Scenario(batch=64, history=8192, tokens=1)
            balanced = forward(model, scenario)['summary']
            concentrated = forward(model, scenario, 'concentrated')['summary']
            self.assertEqual(balanced['matrix_flops'], concentrated['matrix_flops'])
            self.assertEqual(balanced['expert_union_per_layer'], 128)
            self.assertEqual(concentrated['expert_union_per_layer'], 8)
            self.assertEqual(balanced['routed_expert_unique_weight_payload_bytes'],
                             16 * concentrated['routed_expert_unique_weight_payload_bytes'])
            self.assertEqual(balanced['weight_resident_bytes'], concentrated['weight_resident_bytes'])

    def test_histogram_matches_distinct_token_choices(self):
        for rows in (1, 3, 17):
            for experts, top in ((4, 1), (4, 3), (7, 7)):
                observed = [0] * experts
                for token in range(rows):
                    choices = {(token * top + j) % experts for j in range(top)}
                    self.assertEqual(len(choices), top)
                    for expert in choices:
                        observed[expert] += 1
                self.assertEqual(qwen3_moe.routing_counts(rows, experts, top, 'balanced'), observed)
        for invalid in ([4, 0, 0, 0], [1, 1, 0, 0], [True, 1, 2, 2], {'a': 1}, [1.5, 1.5, 1.5, 1.5]):
            with self.assertRaises(ValueError):
                qwen3_moe.routing_counts(3, 4, 2, 'balanced', invalid)

    def test_concrete_expert_matrices_and_csv_conserve_work(self):
        model = 'qwen3-30b-a3b'
        report = forward(model, Scenario(batch=3, tokens=1), counts=[3] * 8 + [0] * 120)
        work = 0
        for expert in report['expert_matrices']:
            for key, copies in (('gate_and_up_each', 2), ('down', 1)):
                gemm = expert[key]
                m, k = gemm['A']
                self.assertEqual(k, gemm['W_math'][0])
                work += copies * 2 * m * k * gemm['Y'][1]
        self.assertEqual(work * 48, report['summary']['routed_expert_matrix_flops'])
        rows = list(csv.DictReader(io.StringIO(operator_csv(report))))
        self.assertEqual(sum(int(row['matrix_flops']) for row in rows), report['summary']['matrix_flops'])

    def test_moe_prefix_split_conserves_work(self):
        def work(history, tokens):
            return forward('qwen3-235b-a22b', Scenario(history=history, tokens=tokens, output_head='none'))['summary']['matrix_flops']
        self.assertEqual(work(0, 17), work(0, 11) + work(11, 6))


class KDAChunkBuffers(unittest.TestCase):
    def test_chunk_triangular_form_matches_recurrence_and_final_state(self):
        rng = random.Random(20260909)
        for length, d, v in [(1, 2, 3), (7, 3, 2), (9, 4, 4)]:
            q, k = [[[rng.uniform(-0.3, 0.3) for _ in range(d)] for _ in range(length)] for _ in range(2)]
            values = [[rng.uniform(-0.5, 0.5) for _ in range(v)] for _ in range(length)]
            gates = [[rng.uniform(-0.4, -0.01) for _ in range(d)] for _ in range(length)]
            beta = [rng.random() for _ in range(length)]
            initial = [[rng.uniform(-0.1, 0.1) for _ in range(v)] for _ in range(d)]
            expected = kda_math.recurrent(q, k, values, gates, beta, initial)
            for chunk in (1, 2, 4, 16):
                actual = kda_math.chunked(q, k, values, gates, beta, initial, chunk)
                for lhs, rhs in zip(actual, expected):
                    for x, y in zip(lhs, rhs):
                        for a, b in zip(x, y):
                            self.assertAlmostEqual(a, b, places=12)

    def test_partial_block_work_uses_valid_triangles(self):
        work = kda_math.work(65, 64, 128, 128)
        self.assertEqual([(r['valid_tokens'], r['chunks']) for r in work['blocks']], [(64, 1), (1, 1)])
        tail = work['blocks'][1]['matrix_stages_per_chunk']
        self.assertEqual(tail['lower_kk'], 0)
        self.assertEqual(tail['solve_w_u'], 0)
        self.assertEqual(tail['causal_qk'], 256)

    def test_partial_chunk_allocation_uses_distinct_token_and_chunk_axes(self):
        result = kda_chunk.calculate(tokens=65)
        s = result['summary']
        self.assertEqual(s['chunks_per_sequence'], 2)
        self.assertEqual(s['last_chunk_valid_tokens'], 1)
        self.assertEqual(s['allocated_Aqk_bytes'], 65 * 96 * 64 * 2)
        self.assertEqual(s['per_layer_chunk_state_bytes'], 2 * 96 * 128 * 128 * 2)

    def test_final_state_and_chunk_workspace_are_not_interchangeable(self):
        result = kda_chunk.calculate(tokens=8192)
        s = result['summary']
        self.assertEqual(s['per_layer_chunk_state_bytes'], 384 * 2**20)
        self.assertEqual(s['all_kda_final_states_bytes'], 414 * 2**20)
        self.assertEqual(s['known_live_subset_max_bytes'], 1926 * 2**20)
        self.assertIsNone(s['full_workspace_peak_bytes'])
        names = result['known_live_phases'][1]['objects']
        self.assertNotIn('Akkd', names)
        self.assertNotIn('qg', names)


class AttentionResidualAccounting(unittest.TestCase):
    def test_boundary_order_and_unused_first_attention_parameters(self):
        result = attn_res.calculate(tokens=1)
        calls = {(r['layer'], r['branch']): r for r in result['attn_res_calls']}
        self.assertNotIn((0, 'attention'), calls)
        self.assertEqual(calls[(0, 'ffn')]['candidates'], 2)
        self.assertEqual(calls[(12, 'attention')]['candidates'], 2)
        self.assertEqual(calls[(12, 'ffn')]['candidates'], 3)
        self.assertEqual(calls[('output', 'output')]['candidates'], 9)
        self.assertEqual(result['summary']['mixing_calls'], 186)
        self.assertEqual(result['summary']['allocated_norm_and_projection_parameters'], 374 * 7168)
        self.assertEqual(result['summary']['prefix_accumulation_scalar_flops'], 178 * 7168)

    def test_score_weight_is_once_per_call_not_per_token(self):
        one = attn_res.calculate(tokens=1)['summary']
        two = attn_res.calculate(tokens=2)['summary']
        self.assertEqual(2 * one['mixing_scalar_flops'] - two['mixing_scalar_flops'], 186 * 7168)
        self.assertEqual(two['weighted_sum_matrix_flops'], 2 * one['weighted_sum_matrix_flops'])
        self.assertEqual(one['final_saved_block_stack_bytes'], 8 * 7168 * 2)


class K3KDAAccounting(unittest.TestCase):
    def test_projection_and_shared_head_norm_dimensions(self):
        report = k3_kda.calculate()
        rows = {x['name']: x for x in report['matrices']}
        self.assertEqual(rows['f_a_proj']['weight_storage_each'], [128, 7168])
        self.assertEqual(rows['f_b_proj']['weight_storage_each'], [12288, 128])
        self.assertEqual(rows['g_proj']['weight_storage_each'], [12288, 7168])
        self.assertEqual(report['summary']['output_norm_parameters'], 69 * 128)
        self.assertEqual(report['summary']['recurrent_state_fp32_bytes'], 414 * 2**20)

    def test_recurrent_work_is_linear_in_tokens_but_state_is_not(self):
        one, many = k3_kda.calculate(tokens=1), k3_kda.calculate(tokens=7)
        for key in ('projection_matrix_flops', 'recurrent_and_other_scalar_flops'):
            self.assertEqual(many['summary'][key], 7 * one['summary'][key])
        self.assertEqual(many['summary']['recurrent_state_fp32_bytes'], one['summary']['recurrent_state_fp32_bytes'])
        self.assertIn('chunk', many['scenario']['reference_dispatch'])
        row = next(x for x in one['non_matrix_operations'] if x['name'] == 'recurrent_state_update_and_query')
        d = 128
        explicit = d*d + (2*d*d-d) + d + d + 2*d*d + (2*d*d-d) + d
        self.assertEqual(row['scalar_flops'], 69 * 96 * explicit)


class K3MLAAccounting(unittest.TestCase):
    def test_compact_preserves_parameter_count_but_changes_attention_work(self):
        expanded = k3_mla.calculate(tokens=8192)['summary']
        compact = k3_mla.calculate(tokens=8192, path='compact')['summary']
        self.assertEqual(expanded['matrix_parameters'], compact['matrix_parameters'])
        self.assertEqual(expanded['projection_matrix_flops'], compact['projection_matrix_flops'])
        self.assertEqual(compact['valid_attention_matrix_flops'] * 10, expanded['valid_attention_matrix_flops'] * 34)
        self.assertEqual(compact['kv_resident_after_bytes'], 216 * 2**20)
        self.assertEqual(expanded['kv_resident_after_bytes'], 12079595520)

    def test_absorbed_qk_and_pv_match_explicit_small_matrices(self):
        q, latent, wk, wv = [2, 3], [[1, 2, 4], [3, 1, 2]], [[1, 2, 0], [0, 1, 3]], [[2, 0, 1], [1, 3, 0]]
        dot = lambda a, b: sum(x * y for x, y in zip(a, b))
        q_absorbed = [sum(q[i] * wk[i][j] for i in range(2)) for j in range(3)]
        for c in latent:
            self.assertEqual(dot(q, [dot(c, row) for row in wk]), dot(q_absorbed, c))
        probabilities = [0.25, 0.75]
        expanded_output = [sum(probabilities[i] * dot(latent[i], row) for i in range(2)) for row in wv]
        weighted_latent = [sum(probabilities[i] * latent[i][j] for i in range(2)) for j in range(3)]
        self.assertEqual(expanded_output, [dot(weighted_latent, row) for row in wv])

    def test_layer_ids_gate_and_nope_extra_branch(self):
        result = k3_mla.calculate(batch=2, tokens=1, history=3, path='compact')
        rows = {r['name']: r for r in result['matrices']}
        self.assertEqual(rows['g_proj']['weight_storage_each'], [12288, 7168])
        self.assertEqual(rows['o_proj']['layer_ids'][-2:], [91, 92])
        self.assertEqual(result['attention_shapes']['query'], [2, 96, 1, 576])
        self.assertEqual(result['summary']['output_gate_sigmoid_ops'], 24 * 2 * 12288)


class V4ForwardComposition(unittest.TestCase):
    def test_routing_changes_known_tiles_not_effective_total_or_parameters(self):
        balanced = v4_forward.calculate('deepseek-v4-pro', batch=64, tokens=1, history=8192)
        concentrated = v4_forward.calculate('deepseek-v4-pro', batch=64, tokens=1, history=8192, routing='concentrated')
        for key in ('logical_parameters_excluding_mtp_and_quant_scales', 'matrix_flops_effective_attention'):
            self.assertEqual(balanced['summary'][key], concentrated['summary'][key])
        self.assertGreater(balanced['summary']['matrix_flops_with_reference_sparse_and_expert_tiles'], concentrated['summary']['matrix_flops_with_reference_sparse_and_expert_tiles'])
        self.assertIsNone(balanced['summary']['complete_hbm_traffic_bytes'])
        self.assertTrue(balanced['coverage']['checkpoint_index_validation'])

    def test_global_head_last_row_and_norm_accounting(self):
        one = v4_forward.calculate('deepseek-v4-flash', tokens=1)
        many = v4_forward.calculate('deepseek-v4-flash', tokens=8)
        self.assertEqual(one['summary']['vocabulary_head_matrix_flops'], many['summary']['vocabulary_head_matrix_flops'])
        self.assertEqual(many['parameter_components']['external_norms'], 87 * 4096)
        self.assertEqual(many['parameter_components']['compressor_norms'], 41 * 512 + 21 * 128)
        self.assertEqual(many['summary']['hash_routing_table_int32_bytes'], 3 * 129280 * 6 * 4)

    def test_checkpoint_headers_match_exact_parameters_and_payload(self):
        for model, keys, size in [('deepseek-v4-flash', 69187, 159609485896),
                                 ('deepseek-v4-pro', 145116, 864704792696)]:
            result = v4_forward.calculate(model, tokens=1)
            checkpoint = result['checkpoint']
            self.assertEqual(checkpoint['verified_tensors'], keys)
            self.assertEqual(checkpoint['checkpoint_tensor_payload_bytes'], size)
            self.assertEqual(checkpoint['base_logical_parameters_excluding_scales_and_hash'], result['summary']['logical_parameters_excluding_mtp_and_quant_scales'])
            self.assertEqual(checkpoint['byte_groups']['base_hash_table_bytes'], 2 * result['summary']['hash_routing_table_int32_bytes'])


class V4AttentionAccounting(unittest.TestCase):
    def test_butterfly_count_and_quantization_groups(self):
        for width in (2, 4, 128):
            values = list(range(width))
            operations = 0
            stride = 1
            while stride < width:
                for start in range(0, width, 2 * stride):
                    for offset in range(stride):
                        i, j = start + offset, start + offset + stride
                        values[i], values[j] = values[i] + values[j], values[i] - values[j]
                        operations += 2
                stride *= 2
            self.assertEqual(transforms.hadamard(1, width)['scalar_flops'], operations + width)
        quant = transforms.simulated_quantization(128, 32, 'FP4')
        self.assertEqual(quant['scalar_flops'], 260)
        self.assertEqual(quant['special_ops']['amax_compare'], 124)
        with self.assertRaises(ValueError):
            transforms.simulated_quantization(127, 32, 'FP4')

    def test_sparse_tile_padding_and_single_shared_kv_read(self):
        result = v4_attention.calculate('deepseek-v4-flash', tokens=8)
        s = result['sparse_kernel_summary']
        self.assertEqual(s['matrix_flops'], 43 * 4 * 8 * 64 * 512 * 64)
        self.assertGreater(s['matrix_flops'], s['effective_matrix_flops'])
        pairs = sum(len(g['layer_ids']) * g['selected_attention_pairs_per_layer'] for g in result['attention_layer_groups'])
        self.assertEqual(s['gathered_kv_bytes'], pairs * 512 * 2)
        self.assertEqual(s['online_softmax_scalar_flops'], 43 * 8 * 64 * (3 * 64 + 2 + 512 + 512 + 2))

    def test_prefill_index_width_differs_from_valid_pairs(self):
        result = v4_attention.calculate('deepseek-v4-pro', tokens=8192)
        indexed = next(g for g in result['sparse_kernel_groups'] if g['compress_ratio'] == 4)
        self.assertEqual(indexed['allocated_index_slots_per_query'], 128 + 1024)
        self.assertEqual(indexed['tiles_per_query'], 18)
        self.assertEqual(indexed['index_read_bytes'], 30 * 8192 * 1152 * 4)

    def test_compression_boundary_controls_pooling_not_projection(self):
        before = v4_attention.calculate('deepseek-v4-flash', tokens=1, history=2)
        boundary = v4_attention.calculate('deepseek-v4-flash', tokens=1, history=3)
        def row(result, name):
            return next(x for x in result['non_matrix_operations'] if x['name'] == name)
        self.assertEqual(row(before, 'compress_r4_main_weighted_pool')['scalar_flops'], 0)
        self.assertEqual(row(boundary, 'compress_r4_main_weighted_pool')['scalar_flops'], 21 * 512 * 15)
        self.assertEqual(before['summary']['projection_matrix_flops'], boundary['summary']['projection_matrix_flops'])

    def test_prefill_overlap_ape_state_save_and_norm_width(self):
        result = v4_attention.calculate('deepseek-v4-flash', tokens=5)
        rows = {x['name']: x for x in result['non_matrix_operations']}
        self.assertEqual(rows['compress_r4_main_ape']['scalar_flops'], 21 * (5 + 4) * 2 * 512)
        self.assertEqual(rows['compress_r4_main_pool_softmax']['special_ops']['exp'], 21 * 512 * 8)
        self.assertEqual(rows['q_head_norm']['scalar_flops'], 43 * 5 * 64 * (3 * 512 + 1))
        self.assertEqual(rows['q_lowrank_norm']['scalar_flops'], 43 * 5 * (4 * 1024 + 1))

    def test_closed_pair_sum_matches_enumeration(self):
        for n in (0, 1, 4, 127, 128, 8192):
            for ratio, cap in ((1, 128), (4, 512), (128, 100)):
                self.assertEqual(v4_attention.capped_floor_sum(n, ratio, cap), sum(min(t // ratio, cap) for t in range(1, n + 1)))

    def test_grouped_output_and_index_rectangular_work(self):
        result = v4_attention.calculate('deepseek-v4-flash', tokens=8)
        rows = {row['name']: row for row in result['matrices']}
        self.assertEqual(rows['wo_a_grouped']['matrix_flops'], 43 * 8 * 2 * 8 * 4096 * 1024)
        indexed = next(row for row in result['attention_layer_groups'] if row['compress_ratio'] == 4)
        self.assertEqual(indexed['actual_index_rectangular_matrix_flops'], 21 * 2 * 64 * 128 * 8 * 2)
        self.assertEqual(indexed['causal_index_matrix_flops'], 21 * 2 * 64 * 128 * 6)

    def test_compressor_projects_without_completed_record(self):
        result = v4_attention.calculate('deepseek-v4-pro', tokens=1, history=8192)
        group = next(row for row in result['attention_layer_groups'] if row['compress_ratio'] == 128)
        self.assertEqual(group['completed_compressed_rows_per_request'], 0)
        proj = next(row for row in result['matrices'] if row['name'] == 'compress_r128_wkv')
        self.assertGreater(proj['matrix_flops'], 0)
        with self.assertRaises(ValueError):
            v4_attention.calculate('deepseek-v4-flash', tokens=2, history=4)


class HyperConnectionAccounting(unittest.TestCase):
    def test_sinkhorn_passes_and_arithmetic(self):
        # c=1: affine 8, initial softmax 3, each normalization 2.
        self.assertEqual(hyper_connections.sinkhorn_work(1, 1)['scalar_flops'], 13)
        first = hyper_connections.sinkhorn_work(4, 1)
        twenty = hyper_connections.sinkhorn_work(4, 20)
        self.assertEqual(twenty['normalization_passes'], 39)
        self.assertEqual(twenty['scalar_flops'] - first['scalar_flops'], 38 * (12 + 32))
        self.assertEqual(twenty['special_ops'], first['special_ops'])

    def test_mhc_both_sublayers_and_all_row_head(self):
        r = hyper_connections.calculate('deepseek-v4-flash', batch=2, tokens=3)
        ops = {x['name']: x for x in r['residual_operations']}
        self.assertEqual(ops['pre_mix_projection']['matrix_flops'], 86 * 2 * 6 * 16384 * 24)
        self.assertEqual(ops['head_mix_projection']['matrix_flops'], 2 * 6 * 16384 * 4)
        self.assertEqual(r['summary']['hc_parameters'], 86 * (24 * 16384 + 24 + 3) + 4 * 16384 + 4 + 1)
        self.assertEqual(r['summary']['residual_activation_tensor_bytes'], 6 * 4 * 4096 * 2)


class ExpertMatrixAccounting(unittest.TestCase):
    def test_v4_fp4_storage_includes_scales_but_mma_is_fp8(self):
        result = experts.calculate('deepseek-v4-flash', batch=64)
        fmt = result['routed_expert_format']
        params = 43 * 256 * 3 * 4096 * 2048
        self.assertEqual(fmt['summary']['resident_weight_and_scale_bytes'], params * 17 // 32)
        self.assertEqual(fmt['accumulator'], 'FP32')
        self.assertFalse(fmt['native_fp4_peak_eligible'])
        self.assertEqual(fmt['summary']['valid_matrix_flops'], result['summary']['routed_matrix_flops'])

    def test_reference_expert_tile_padding_depends_on_histogram(self):
        balanced = experts.calculate('deepseek-v4-pro', batch=64)['routed_expert_format']['summary']
        concentrated = experts.calculate('deepseek-v4-pro', batch=64, routing='concentrated')['routed_expert_format']['summary']
        self.assertEqual(balanced['valid_matrix_flops'], concentrated['valid_matrix_flops'])
        self.assertEqual(balanced['padded_tile_matrix_flops'], 32 * balanced['valid_matrix_flops'])
        self.assertEqual(concentrated['padded_tile_matrix_flops'], concentrated['valid_matrix_flops'])
        self.assertEqual(concentrated['logical_scale_accumulation_flops'], concentrated['padded_scale_accumulation_flops'])

    def test_dispatch_kimi_permutation_conserves_rows(self):
        selected = [[2, 0], [1, 2], [0, 1]]
        flat = [e for token in selected for e in token]
        permutation = sorted(range(len(flat)), key=flat.__getitem__)
        restored = [None] * len(flat)
        for sorted_row, original in enumerate(permutation):
            restored[original] = permutation[sorted_row] // 2
        self.assertEqual(restored, [0, 0, 1, 1, 2, 2])
        result = experts.calculate('kimi-k3', batch=3)
        ops = {op['name']: op for op in result['dispatch_operations']}
        self.assertEqual(ops['restore_assignment_order']['write_bytes'], 92 * 3 * 16 * 3584 * 2)
        self.assertEqual(ops['count_matrix_zero']['write_bytes'], 92 * 3 * 896 * 8)
        self.assertEqual(result['dispatch_summary']['device_to_host_count_bytes'], 92 * 896 * 8)
        self.assertIsNone(result['dispatch_summary']['sorting_or_histogram_internal_bytes'])

    def test_v4_dispatch_mask_cost_tracks_expert_union_and_index_dtype(self):
        result = experts.calculate('deepseek-v4-flash', batch=64)
        concentrated = experts.calculate('deepseek-v4-flash', batch=64, routing='concentrated')
        masks = [x for x in result['dispatch_operations'] if x['name'] == 'expert_equality_masks']
        self.assertEqual([x['read_bytes_per_layer'] for x in masks], [256 * 384 * 4, 256 * 384 * 8])
        self.assertEqual([len(x['layer_ids']) for x in masks], [3, 40])
        small = [x for x in concentrated['dispatch_operations'] if x['name'] == 'expert_equality_masks']
        for lhs, rhs in zip(masks, small):
            self.assertEqual(lhs['write_bytes'] * 6, rhs['write_bytes'] * 256)

    def test_fp32_dispatch_does_not_materialize_noop_casts(self):
        result = experts.calculate('kimi-k3', element_bytes=4)
        names = {x['name'] for x in result['dispatch_operations']}
        self.assertNotIn('outputs_cast_fp32', names)
        self.assertNotIn('combined_cast', names)

    def test_probability_weighting_uses_reference_intermediate_or_output_width(self):
        for model, width, layers, top in [('deepseek-v4-flash', 2048, 43, 6), ('kimi-k3', 3584, 92, 16)]:
            result = experts.calculate(model, batch=3)
            row = next(x for x in result['non_matrix_operations'] if x['name'] == 'routed_probability_multiply')
            self.assertEqual(row['scalar_flops'], 3 * top * width * layers)

    def test_kimi_situ_includes_up_tanh_and_dense_first_layer(self):
        result = experts.calculate('kimi-k3', batch=1)
        rows = {x['name']: x for x in result['non_matrix_operations']}
        n = 33792
        self.assertEqual(rows['dense_activation']['scalar_flops'], 6 * n)
        self.assertEqual(rows['dense_activation']['special_ops'], {'tanh': 2 * n, 'sigmoid': n})
        self.assertEqual(rows['latent_rmsnorm']['scalar_flops'], 92 * (4 * 3584 + 1))
        self.assertEqual(rows['routed_combine']['scalar_flops'], 92 * 15 * 3584)

    def test_v4_hash_excludes_topk_but_keeps_score_and_normalization(self):
        result = experts.calculate('deepseek-v4-flash', batch=2)
        rows = {x['name']: x for x in result['non_matrix_operations']}
        self.assertEqual(rows['router_topk']['special_ops']['topk_rows'], 2 * 40)
        self.assertEqual(rows['router_score']['special_ops']['softplus'], 2 * 256 * 43)
        self.assertEqual(rows['router_normalize_scale']['scalar_flops'], 2 * 17 * 43)
        self.assertEqual(rows['routed_activation']['special_ops']['clamp_bound_comparisons'], 3 * 2 * 6 * 2048 * 43)

    def test_qwen_ledger_matches_full_graph(self):
        for model in ('qwen3-30b-a3b', 'qwen3-235b-a22b'):
            ledger = experts.calculate(model, batch=7)['summary']
            graph = forward(model, Scenario(batch=7, tokens=1))['summary']
            self.assertEqual(ledger['ffn_matrix_flops'], graph['routed_expert_matrix_flops'] + graph['router_matrix_flops'])

    def test_kimi_uses_latent_routed_but_full_width_shared_and_router(self):
        report = experts.calculate('kimi-k3', batch=1)
        rows = {row['name']: row for row in report['matrices']}
        self.assertEqual(rows['routed_gate']['weight_storage_each'], [3072, 3584])
        self.assertEqual(rows['shared_gate']['weight_storage_each'], [6144, 7168])
        self.assertEqual(rows['router']['weight_storage_each'], [896, 7168])
        self.assertEqual(rows['dense_gate']['layer_ids'], [0])
        self.assertEqual(rows['routed_gate']['layer_ids'], list(range(1, 93)))
        self.assertEqual(report['summary']['routed_matrix_flops'], 92 * 16 * 6 * 3584 * 3072)
        self.assertEqual(report['summary']['latent_matrix_flops'], 92 * 4 * 7168 * 3584)
        self.assertEqual(report['summary']['dense_matrix_flops'], 6 * 7168 * 33792)

    def test_v4_hash_layers_keep_router_gemm_and_integer_table(self):
        for model, layers, h, e, f in [('deepseek-v4-flash', 43, 4096, 256, 2048),
                                      ('deepseek-v4-pro', 61, 7168, 384, 3072)]:
            report = experts.calculate(model, batch=64)
            summary = report['summary']
            self.assertEqual(summary['router_matrix_flops'], layers * 2 * 64 * h * e)
            self.assertEqual(summary['hash_lookup_resident_int32_bytes'], 3 * 129280 * 6 * 4)
            self.assertEqual(summary['routed_matrix_flops'], layers * 6 * 64 * 6 * h * f)
            self.assertEqual(summary['shared_matrix_flops'], layers * 6 * 64 * h * f)
            self.assertEqual(summary['router_bias_elements'], (layers - 3) * e)


class QwenAccounting(unittest.TestCase):
    def test_complete_weight_keys_and_bytes_match_official_checkpoint_index(self):
        for model in ("qwen3-8b", "qwen3-32b"):
            with self.subTest(model=model):
                config = model_config(model)
                weights = qwen3.weights(config)
                expected = json.loads(read_source(f"sources/{model}/model.safetensors.index.json"))
                expanded = {row.name.format(layer=layer) for row in weights for layer in range(row.copies)}
                self.assertEqual(expanded, set(expected["weight_map"]))
                self.assertEqual(sum(row.parameters * 2 for row in weights), expected["metadata"]["total_size"])

    def test_qwen32_attention_width_is_not_hidden_size(self):
        result = qwen3.calculate("qwen3-32b", Scenario(tokens=1))
        query = next(row for row in result["operators"] if row["name"] == "q_proj")
        self.assertEqual(query["shapes"]["weight_storage"], [8192, 5120])

    def test_published_book_hand_calculations(self):
        summary = qwen3.calculate("qwen3-8b", Scenario())["summary"]
        self.assertEqual(summary["backbone_projection_ffn_flops"], 113799453474816)
        self.assertEqual(summary["causal_attention_matrix_flops"], 19793625219072)
        self.assertEqual(summary["kv_bytes_per_token_per_request"], 147456)
        self.assertEqual(summary["kv_resident_after_bytes"], 1207959552)

    def test_causal_pairs_match_explicit_enumeration(self):
        for batch in (1, 3):
            for history in (0, 1, 5):
                for tokens in (1, 2, 7):
                    pairs = sum(1 for _ in range(batch) for query in range(tokens)
                                for key in range(history + tokens) if key <= history + query)
                    self.assertEqual(Scenario(batch=batch, history=history, tokens=tokens).pairs, pairs)

    def test_prefix_split_conserves_valid_matrix_work(self):
        def flops(history, tokens):
            return qwen3.calculate("qwen3-8b", Scenario(history=history, tokens=tokens, output_head="none"))["summary"]["matrix_flops"]
        self.assertEqual(flops(0, 8192), flops(0, 6144) + flops(6144, 2048))

    def test_output_head_policy_is_explicit(self):
        last = qwen3.calculate("qwen3-8b", Scenario(tokens=8))["summary"]
        all_rows = qwen3.calculate("qwen3-8b", Scenario(tokens=8, output_head="all"))["summary"]
        self.assertEqual(all_rows["matrix_flops"] - last["matrix_flops"], 7 * 2 * 4096 * 151936)

    def test_batch_reuses_weights_but_does_not_share_request_history(self):
        one = qwen3.calculate("qwen3-8b", Scenario(tokens=1, history=8192))
        many = qwen3.calculate("qwen3-8b", Scenario(batch=64, tokens=1, history=8192))
        self.assertEqual(many["summary"]["matrix_flops"], 64 * one["summary"]["matrix_flops"])
        self.assertEqual(many["summary"]["kv_resident_after_bytes"], 64 * one["summary"]["kv_resident_after_bytes"])
        def projection(report):
            return next(row for row in report["operators"] if row["name"] == "q_proj")["weight_read_bytes"]
        self.assertEqual(projection(one), projection(many))

    def test_pv_uses_shared_v_but_query_head_compute(self):
        report = qwen3.calculate("qwen3-8b", Scenario(tokens=1, history=3))
        pv = next(row for row in report["operators"] if row["name"] == "pv")
        self.assertEqual(pv["shapes"]["V_shared"], [1, 8, 4, 128])
        self.assertEqual(pv["matrix_flops"], 2 * 32 * 4 * 128)

    def test_generated_sequence_matches_individual_forwards(self):
        batch, history, steps = 2, 3, 7
        sequence = qwen3.generation("qwen3-8b", batch, history, steps)["summary"]
        reports = [qwen3.calculate("qwen3-8b", Scenario(batch=batch, tokens=1, history=history + i))["summary"] for i in range(steps)]
        self.assertEqual(sequence["matrix_flops"], sum(row["matrix_flops"] for row in reports))
        self.assertEqual(sequence["kv_existing_history_read_bytes"], sum(row["kv_resident_before_bytes"] for row in reports))

    def test_expanded_csv_conserves_flops_and_layer_order(self):
        report = qwen3.calculate("qwen3-8b", Scenario(tokens=1))
        rows = list(csv.DictReader(io.StringIO(operator_csv(report))))
        self.assertEqual(sum(int(row["matrix_flops"]) for row in rows), report["summary"]["matrix_flops"])
        layers = [int(row["layer"]) for row in rows if row["layer"] != "global"]
        self.assertEqual(layers, sorted(layers))
        self.assertEqual(set(layers), set(range(36)))

    def test_reject_unsupported_or_invalid_input(self):
        for kwargs in ({"batch": 0}, {"tokens": -1}, {"history": -1}, {"batch": True}, {"output_head": "maybe"}):
            with self.assertRaises(ValueError):
                Scenario(**kwargs)
        with self.assertRaises(ValueError):
            qwen3.calculate("qwen3-235b-a22b", Scenario(tokens=1))
        with self.assertRaises(ValueError):
            qwen3.calculate("qwen3-8b", Scenario(history=40960, tokens=1))


class StateAccounting(unittest.TestCase):
    def test_flash_matches_preexisting_independent_note(self):
        report = state.calculate("deepseek-v4-flash", 8192)
        self.assertEqual(report["layer_counts"], {"window": 2, "CSA": 21, "HCA": 20})
        self.assertEqual(report["summary"]["history_resident_bytes"], 59.125 * 2**20)
        self.assertEqual(report["summary"]["selected_history_payload_bytes"], 27.625 * 2**20)
        self.assertEqual(report["summary"]["compressor_buffer_bytes"], 11.640625 * 2**20)

    def test_pro_is_not_scaled_flash(self):
        report = state.calculate("deepseek-v4-pro", 8192)
        self.assertEqual(report["layer_counts"], {"HCA": 31, "CSA": 30})
        csa = next(row for row in report["layers"] if row["kind"] == "CSA")
        self.assertEqual(csa["main_selected_payload_bytes"], (128 + 1024) * 512 * 2)

    def test_compression_boundary_and_short_window(self):
        before = state.calculate("deepseek-v4-flash", 3)["layers"][2]
        after = state.calculate("deepseek-v4-flash", 4)["layers"][2]
        self.assertTrue(before["next_token_completes_compression"])
        self.assertFalse(after["next_token_completes_compression"])
        self.assertEqual(before["window_history_bytes"], 3 * 512 * 2)
        self.assertEqual(after["compressed_history_bytes"] - before["compressed_history_bytes"], 512 * 2)

    def test_k3_paths_and_precision_match_independent_note(self):
        compact = state.calculate("kimi-k3", 8192)
        expanded = state.calculate("kimi-k3", 8192, mla_path="expanded")
        self.assertEqual(compact["layer_counts"], {"KDA": 69, "MLA": 24})
        self.assertEqual(compact["components"]["mla_history_bytes"], 216 * 2**20)
        self.assertEqual(expanded["components"]["mla_history_bytes"], 11.25 * 2**30)
        self.assertEqual(compact["components"]["kda_recurrent_bytes"], 414 * 2**20)
        half = state.calculate("kimi-k3", 8192, recurrent_bytes=2)
        self.assertEqual(half["components"]["kda_recurrent_bytes"], 207 * 2**20)


class HardwareAccounting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.devices = {row["id"]: row for row in hardware.catalog()["devices"]}

    def test_accumulator_and_product_distinction(self):
        gpu = self.devices["rtx4090"]
        fp16 = hardware.select_peak(gpu, "FP16", "FP16", "tensor", "dense")
        fp32 = hardware.select_peak(gpu, "FP16", "FP32", "tensor", "dense")
        self.assertEqual(fp16["tera_ops_per_second"], 330.3)
        self.assertEqual(fp32["tera_ops_per_second"], 165.2)
        workstation = hardware.select_peak(self.devices["rtx-pro6000-blackwell-ws"], "BF16", "FP32", "tensor", "dense")
        self.assertEqual(workstation["tera_ops_per_second"], 503.8)

    def test_refuse_ambiguous_or_integer_peak(self):
        for gpu, precision, accumulator, unit, sparsity in [
            ("m2-max-38gpu-96gb", "BF16", "FP32", "tensor", "dense"),
            ("ascend-950dt-max-spec", "BF16", "unspecified", "cube", "unspecified"),
            ("a100-80gb-sxm", "INT8", "INT32", "tensor", "dense"),
            ("rtx4090", "FP32", "FP32", "tensor", "dense"),
        ]:
            with self.assertRaises(ValueError):
                hardware.select_peak(self.devices[gpu], precision, accumulator, unit, sparsity)

    def test_sparse_is_not_automatic(self):
        with self.assertRaises(ValueError):
            hardware.roofline("a100-80gb-sxm", 10**12, 10**9, sparsity="structured")

    def test_hopper_accumulator_evidence_and_nvl_variants(self):
        sxm = hardware.select_peak(self.devices["h100-sxm"], "BF16", "FP32", "tensor", "dense")
        pcie = hardware.select_peak(self.devices["h100-pcie-80gb"], "BF16", "FP32", "tensor", "dense")
        self.assertEqual((sxm["tera_ops_per_second"], pcie["tera_ops_per_second"]), (989.4, 756))
        self.assertIn("1830", sxm["clock_basis"])
        self.assertEqual(self.devices["h100-nvl-94gb"]["memory"]["nominal_capacity"], 94)
        self.assertEqual(self.devices["h200-nvl"]["memory"]["nominal_capacity"], 141)
        with self.assertRaises(ValueError):
            hardware.select_peak(self.devices["h100-sxm"], "BF16", "FP16", "tensor", "dense")

    def test_apple_memory_bins_are_distinct(self):
        self.assertEqual(self.devices["m3-max-30gpu-96gb"]["memory"]["bandwidth_bytes_per_second"], 300e9)
        self.assertEqual(self.devices["m3-max-40gpu-128gb"]["memory"]["bandwidth_bytes_per_second"], 400e9)
        self.assertEqual(self.devices["m6-12gpu-16gb"]["memory"]["bandwidth_bytes_per_second"], 153e9)
        self.assertEqual(self.devices["m6-12gpu-32gb"]["memory"]["bandwidth_bytes_per_second"], 170e9)
        self.assertIsNone(self.devices["m1-8gpu-16gb"]["memory"]["bandwidth_bytes_per_second"])

    def test_unknown_server_peaks_do_not_inherit_workstation(self):
        device = self.devices["rtx-pro6000-blackwell-server"]
        self.assertEqual(device["memory"]["bandwidth_bytes_per_second"], 1597e9)
        with self.assertRaises(ValueError):
            hardware.select_peak(device, "BF16", "FP32", "tensor", "dense")

    def test_gb300_fp4_does_not_follow_twofold_assumption(self):
        peaks = [row for row in self.devices["gb300-nvl72"]["peak_rates"] if row["input_precision"] == "FP4"]
        values = {row["sparsity"]: row["tera_ops_per_second"] for row in peaks}
        self.assertEqual(values["dense"], 1080000)
        self.assertEqual(values["structured"], 1440000)
        result = hardware.roofline("gb200-superchip", 10**12, 10**9)
        self.assertEqual((result["resource_scope"], result["gpu_count"]), ("gpu_aggregate", 2))

    def test_field_provenance_and_duplicate_peak_validation(self):
        device = copy.deepcopy(self.devices["h100-sxm"])
        device["peak_rates"][0]["source_id"] = "not-in-device-sources"
        with self.assertRaises(ValueError):
            hardware.validate_device(device)
        device = copy.deepcopy(self.devices["h100-sxm"])
        device["peak_rates"].append(copy.deepcopy(device["peak_rates"][0]))
        with self.assertRaises(ValueError):
            hardware.validate_device(device)

    def test_resource_bound_and_efficiency(self):
        result = hardware.roofline("rtx4090", 165200000000000, 1008000000000)
        self.assertEqual(result["summary"]["compute_service_seconds"], 1.0)
        self.assertEqual(result["summary"]["memory_service_seconds"], 1.0)
        half = hardware.roofline("rtx4090", 165200000000000, 1008000000000, compute_efficiency=0.5)
        self.assertEqual(half["summary"]["resource_time_lower_bound_seconds"], 2.0)


class ProjectionAccounting(unittest.TestCase):
    def test_qwen32_projection_uses_query_width_and_beta_zero(self):
        result = projection.calculate("qwen3-32b", "h100-sxm", 1, 8192)
        self.assertEqual(result["shapes"]["W_storage"], [8192, 5120])
        self.assertEqual(result["summary"]["matrix_flops"], 687194767360)
        # Two 80 MiB operands plus a 128 MiB output, no old-C read.
        self.assertEqual(result["summary"]["cold_memory_payload_bytes"], 288 * 2**20)

    def test_weight_reuse_changes_compute_and_memory_balance(self):
        one = projection.calculate("qwen3-8b", "rtx4090", 1)["summary"]
        many = projection.calculate("qwen3-8b", "rtx4090", 256)["summary"]
        self.assertEqual(many["matrix_flops"], 256 * one["matrix_flops"])
        self.assertEqual(many["weight_read_bytes"], one["weight_read_bytes"])
        self.assertGreater(one["memory_service_seconds"], one["compute_service_seconds"])
        self.assertGreater(many["compute_service_seconds"], many["memory_service_seconds"])

    def test_partial_evidence_is_visible_and_aggregate_needs_sharding(self):
        apple = projection.calculate("qwen3-8b", "m2-max-38gpu-96gb")["summary"]
        self.assertIsNone(apple["roofline_lower_bound_seconds"])
        self.assertIsNone(apple["compute_service_seconds"])
        self.assertGreater(apple["memory_service_seconds"], 0)
        with self.assertRaises(ValueError):
            projection.calculate("qwen3-8b", "gb200-superchip")


class K3CheckpointAccounting(unittest.TestCase):
    def test_all_headers_and_explicit_config_discrepancy(self):
        result = k3_checkpoint.calculate()
        self.assertEqual(result['verified_tensors'], 497220)
        self.assertEqual(result['verified_shards'], 96)
        self.assertEqual(result['checkpoint_tensor_payload_bytes'], 1560860324864)
        mismatches = result['config_shape_mismatches']
        self.assertEqual(len(mismatches), 69)
        self.assertEqual({int(row['tensor'].split('.')[3]) for row in mismatches},
                         {i - 1 for i in model_config('kimi-k3')['text_config']['linear_attn_config']['kda_layers']})
        for row in mismatches:
            self.assertTrue(row['tensor'].endswith('.self_attn.A_log'))
            self.assertEqual(row['config_shape'], [96])
            self.assertEqual(row['checkpoint_shape'], [128])
        self.assertFalse(result['config_shape_match'])
        self.assertEqual(result['text_parameter_delta_from_config'], 69 * (128 - 96))
        # 92 layers, 896 experts, three matrices, packed payload + group-32 scales.
        logical_experts = 92 * 896 * 3 * 3584 * 3072
        self.assertEqual(result['byte_groups']['text_U8_bytes'], logical_experts * 17 // 32)
        self.assertEqual(result['byte_groups']['text_quant_scales_bytes'], logical_experts // 32)


class K3ForwardAccounting(unittest.TestCase):
    def test_paths_preserve_parameters_and_change_only_attention_work_and_cache(self):
        expanded = k3_forward.calculate(tokens=7)
        compact = k3_forward.calculate(tokens=7, mla_path='compact')
        self.assertEqual(expanded['parameter_components'], compact['parameter_components'])
        delta = compact['summary']['matrix_flops'] - expanded['summary']['matrix_flops']
        expected = 2 * 24 * 96 * (7 * 8 // 2) * (1088 - 320)
        self.assertEqual(delta, expected)
        self.assertGreater(expanded['summary']['state_resident_after_bytes'], compact['summary']['state_resident_after_bytes'])

    def test_generation_head_slices_only_head_work(self):
        last = k3_forward.calculate(batch=2, tokens=7)
        all_positions = k3_forward.calculate(batch=2, tokens=7, output_head='all')
        c = model_config('kimi-k3')['text_config']
        self.assertEqual(all_positions['summary']['matrix_flops'] - last['summary']['matrix_flops'],
                         2 * 2 * (7 - 1) * c['hidden_size'] * c['vocab_size'])
        self.assertEqual(last['scalar_components'], all_positions['scalar_components'])
        self.assertEqual(last['parameter_components'], all_positions['parameter_components'])
        self.assertIsNone(last['summary']['complete_actual_weight_bytes'])
        self.assertIsNone(last['summary']['predicted_latency_seconds'])

    def test_chunk_replaces_recurrent_core_and_exponentials(self):
        recurrent = k3_forward.calculate(tokens=65, kda_algorithm='recurrent')
        chunk = k3_forward.calculate(tokens=65, kda_algorithm='chunk')
        core = next(row['scalar_flops'] for row in recurrent['components']['kda']['non_matrix_operations']
                    if row['name'] == 'recurrent_state_update_and_query')
        block = chunk['components']['kda_chunk']['summary']
        self.assertEqual(chunk['summary']['matrix_flops'] - recurrent['summary']['matrix_flops'],
                         block['mathematical_block_matrix_flops'])
        self.assertEqual(chunk['summary']['accounted_scalar_flops'] - recurrent['summary']['accounted_scalar_flops'],
                         block['mathematical_block_scalar_flops'] - core)
        self.assertNotIn('exp_decay', chunk['summary']['accounted_special_ops'])
        self.assertNotIn('exp_block', recurrent['summary']['accounted_special_ops'])
        self.assertEqual(k3_forward.calculate(tokens=1)['scenario']['kda_algorithm'], 'recurrent')
        with self.assertRaises(ValueError):
            k3_forward.calculate(kda_algorithm='unknown')


class CacheSequenceAccounting(unittest.TestCase):
    def test_closed_form_matches_stepwise_cache_and_uncached_execution(self):
        for prompt, steps, hit in ((1, 0, 0), (3, 1, 3), (7, 5, 4)):
            result = cache_sequence.calculate(batch=2, prompt=prompt, steps=steps, prefix_hit=hit)
            summary = result['summary']
            self.assertEqual(summary['decode_prior_history_records_per_request'], sum(range(prompt, prompt + steps)))
            self.assertEqual(summary['uncached_recompute_pairs_per_request'],
                             sum(n * (n + 1) // 2 for n in range(prompt + 1, prompt + steps + 1)))
            self.assertEqual(summary['saved_prefill_pairs_per_request'], hit * (hit + 1) // 2)
            for row in result['cache_variants']:
                unit = 2 * row['history_bytes_per_token']
                self.assertEqual(row['final_history_bytes'] - row['initial_history_bytes'], row['decode_append_write_bytes'])
                self.assertEqual(row['decode_visible_kv_operand_bytes'], row['decode_prior_history_read_payload_bytes'] + steps * unit)

    def test_gqa_changes_cache_but_not_query_interaction(self):
        rows = cache_sequence.calculate()['cache_variants']
        gqa, mha, mqa = rows
        self.assertEqual(mha['history_bytes_per_token'], 4 * gqa['history_bytes_per_token'])
        self.assertEqual(gqa['history_bytes_per_token'], 8 * mqa['history_bytes_per_token'])
        self.assertEqual(len({row['decode_attention_matrix_flops'] for row in rows}), 1)
        self.assertEqual(mha['kv_projection_parameters'], 4 * gqa['kv_projection_parameters'])

    def test_k3_persistent_state_and_prefix_boundary(self):
        rows = cache_sequence.calculate('kimi-k3', batch=2, prompt=7, steps=5, prefix_hit=4)['cache_variants']
        for row in rows:
            expected = state.calculate('kimi-k3', 12, 2, mla_path=row['name'])
            self.assertEqual(row['final_persistent_state_bytes'], expected['summary']['resident_bytes'])
            self.assertEqual(row['decode_recurrent_read_plus_write_bytes'], 10 * row['recurrent_bytes'])
            checkpoint = state.calculate('kimi-k3', 4, 2, mla_path=row['name'])
            self.assertEqual(row['prefix_checkpoint_payload_bytes'], checkpoint['summary']['resident_bytes'])
        self.assertEqual(rows[1]['decode_attention_matrix_flops'] * 5, rows[0]['decode_attention_matrix_flops'] * 17)
        with self.assertRaises(ValueError):
            cache_sequence.calculate(prompt=7, prefix_hit=8)
        with self.assertRaises(ValueError):
            cache_sequence.calculate(steps=-1)


class ResourceBasicsAccounting(unittest.TestCase):
    def test_decimal_binary_and_bit_byte_units(self):
        result = resource_basics.calculate()['summary']
        self.assertEqual(result['weight_payload_bytes'], 140000000000)
        self.assertEqual(result['weight_payload_GB'], 140)
        self.assertEqual(result['weight_payload_GiB'], 140000000000 / 1073741824)
        self.assertEqual(result['raw_one_direction_GB_per_second'], 50)
        self.assertEqual(result['ideal_payload_service_seconds'], 2.8)

    def test_aggregate_fit_does_not_prove_each_card_fit(self):
        skew = resource_basics.calculate(shard_parameters=[70000000000, 0])['summary']
        self.assertTrue(skew['aggregate_capacity_sufficient'])
        self.assertFalse(skew['every_card_fits_declared_budget'])
        reserved = resource_basics.calculate(workspace_bytes_per_card=11000000000)['summary']
        self.assertFalse(reserved['every_card_fits_declared_budget'])
        with self.assertRaises(ValueError):
            resource_basics.calculate(shard_parameters=[1, 2])

    def test_packing_rounds_per_card_and_message_count_only_scales_startup(self):
        packed = resource_basics.calculate(parameters=2, weight_bits=4, shard_parameters=[1, 1])
        self.assertEqual(packed['summary']['weight_payload_bytes'], 2)
        one = resource_basics.calculate(payload_bytes=4096, messages=1)['summary']
        many = resource_basics.calculate(payload_bytes=4096, messages=4)['summary']
        self.assertEqual(one['modeled_payload_service_seconds'], many['modeled_payload_service_seconds'])
        self.assertEqual(many['modeled_startup_seconds'], 4 * one['modeled_startup_seconds'])
        with self.assertRaises(ValueError):
            resource_basics.calculate(link_efficiency=1.01)


class MemoryConcurrencyAccounting(unittest.TestCase):
    def test_official_kv_payload_and_teaching_window(self):
        s = memory_concurrency.calculate()['summary']
        self.assertEqual(s['logical_kv_payload_bytes'], 36 * 2 * 8 * 128 * 2 * 8192)
        self.assertEqual(s['required_transactions'], 3907)
        self.assertEqual(s['effective_bandwidth_upper_bytes_per_second'], 32768000000)
        self.assertAlmostEqual(s['window_constrained_service_lower_seconds'], 0.036864)

    def test_more_bandwidth_cannot_remove_window_limit(self):
        s = memory_concurrency.calculate(transactions=4096, bandwidth_bytes_per_second=2000000000000)['summary']
        self.assertEqual(s['effective_bandwidth_upper_bytes_per_second'], 1048576000000)
        self.assertEqual(s['limiter'], 'transaction_window')
        self.assertAlmostEqual(s['window_constrained_service_lower_seconds'], 0.001152)

    def test_ceil_boundary_and_batch_is_not_transaction_count(self):
        exact = memory_concurrency.calculate(transaction_bytes=100, latency_ns=100)['summary']
        above = memory_concurrency.calculate(transaction_bytes=100, latency_ns=101)['summary']
        self.assertEqual(exact['required_transactions'], 1000)
        self.assertEqual(above['required_transactions'], 1010)
        one = memory_concurrency.calculate()['summary']
        two = memory_concurrency.calculate(batch=2)['summary']
        self.assertEqual(two['effective_bandwidth_upper_bytes_per_second'], one['effective_bandwidth_upper_bytes_per_second'])
        self.assertEqual(two['window_constrained_service_lower_seconds'], 2 * one['window_constrained_service_lower_seconds'])
        with self.assertRaises(ValueError):
            memory_concurrency.calculate(latency_ns=0)


class DecodeBudgetAccounting(unittest.TestCase):
    def test_textbook_memory_bound_and_counterfactual_resources(self):
        base = decode_budget.calculate()['summary']
        compute = decode_budget.calculate(compute_multiplier=2)['summary']
        bandwidth = decode_budget.calculate(bandwidth_multiplier=2)['summary']
        self.assertAlmostEqual(base['memory_service_seconds'], 70e9 / 3.35e12)
        self.assertEqual(compute['resource_lower_bound_seconds'], base['resource_lower_bound_seconds'])
        self.assertEqual(bandwidth['resource_lower_bound_seconds'], base['resource_lower_bound_seconds'] / 2)

    def test_storage_does_not_select_a_different_compute_precision(self):
        low = decode_budget.calculate(weight_bits=4)
        high = decode_budget.calculate(weight_bits=16)
        self.assertEqual(low['selected_peak'], high['selected_peak'])
        self.assertFalse(high['summary']['fits_declared_budget'])
        self.assertIsNone(high['summary']['resource_lower_bound_seconds'])
        self.assertIsNone(high['summary']['capacity_feasible_throughput_upper_tokens_per_second'])

    def test_batch_crossover_and_kv_can_prevent_it(self):
        base = decode_budget.calculate()['summary']
        crossing = base['compute_memory_crossover_batch']
        self.assertEqual(decode_budget.calculate(batch=crossing)['summary']['dominant_resource'], 'compute')
        self.assertEqual(decode_budget.calculate(batch=crossing - 1)['summary']['dominant_resource'], 'memory')
        with_kv = decode_budget.calculate(kv_history_bytes_per_request=1073741824)['summary']
        self.assertIsNone(with_kv['compute_memory_crossover_batch'])


class RingCollectiveAccounting(unittest.TestCase):
    def test_round_schedule_reduces_then_distributes_every_chunk(self):
        for p in (1, 2, 4, 8):
            values = [[100 * rank + chunk for chunk in range(p)] for rank in range(p)]
            expected = [sum(100 * rank + chunk for rank in range(p)) for chunk in range(p)]
            for round in ring_collective.schedule(p, 2):
                previous = [row[:] for row in values]
                for edge in round['edges']:
                    sender, receiver, chunk = edge['sender'], edge['receiver'], edge['chunk']
                    if round['phase'] == 'reduce_scatter':
                        values[receiver][chunk] += previous[sender][chunk]
                    else:
                        values[receiver][chunk] = previous[sender][chunk]
            self.assertEqual(values, [expected] * p)

    def test_formula_volume_and_identity(self):
        result = ring_collective.calculate()['summary']
        self.assertEqual(result['message_bytes_per_rank'], 8192)
        self.assertEqual(result['all_reduce_rounds'], 14)
        self.assertEqual(result['all_reduce_network_send_bytes'], 2 * 7 * 8192)
        self.assertAlmostEqual(result['dense_tp_serial_collective_seconds'], 72 * (14 * 2e-6 + 14 * 1024 / 50e9))
        identity = ring_collective.calculate(participants=1)['summary']
        self.assertEqual(identity['all_reduce_modeled_seconds'], 0)
        with self.assertRaises(ValueError):
            ring_collective.calculate(participants=3)


class TreeCollectiveAccounting(unittest.TestCase):
    def test_reduction_and_broadcast_replay_including_incomplete_trees(self):
        for p in (1, 2, 3, 5, 8, 9):
            values = [rank + 1 for rank in range(p)]
            for row in tree_collective.schedule(p, 2):
                previous = values[:]
                for edge in row['edges']:
                    if row['phase'] == 'reduce':
                        values[edge['receiver']] += previous[edge['sender']]
                    else:
                        values[edge['receiver']] = previous[edge['sender']]
            self.assertEqual(values, [p * (p + 1) // 2] * p)

    def test_equal_volume_but_message_size_changes_algorithm_order(self):
        for tokens in (1, 8192):
            ring = ring_collective.calculate(tokens=tokens)['summary']
            tree = tree_collective.calculate(tokens=tokens)['summary']
            self.assertEqual(tree['all_reduce_network_send_bytes'], ring['all_reduce_network_send_bytes'])
            self.assertEqual(tree['all_reduce_global_reduction_adds'], ring['all_reduce_global_reduction_adds'])
            self.assertEqual(tree['all_reduce_rounds'], 6)
            self.assertGreater(tree['maximum_rank_send_bytes'], ring['all_reduce_send_bytes_per_rank'])
            self.assertEqual(tree['all_reduce_modeled_seconds'] < ring['all_reduce_modeled_seconds'], tokens == 1)


class AllToAllAccounting(unittest.TestCase):
    def test_equal_global_bytes_do_not_imply_equal_endpoint_load(self):
        balanced = all_to_all.calculate()
        hotspot = all_to_all.calculate(routing='hotspot')
        a, b = balanced['summary'], hotspot['summary']
        self.assertEqual(a['dispatch_network_send_bytes'], b['dispatch_network_send_bytes'])
        self.assertEqual(b['dispatch_maximum_receive_bytes'], 8 * a['dispatch_maximum_receive_bytes'])
        self.assertGreater(b['dispatch_pairwise_modeled_seconds'], a['dispatch_pairwise_modeled_seconds'])

    def test_every_remote_assignment_occurs_once_and_reverse_conserves(self):
        result = all_to_all.calculate(routing='hotspot')
        counts = result['scenario']['counts']
        dispatch, combine = (result['all_to_all_phases'][name] for name in ('dispatch', 'combine'))
        found = {}
        for row in dispatch['rounds']:
            self.assertEqual(len({edge['sender'] for edge in row['edges']}), len(row['edges']))
            self.assertEqual(len({edge['receiver'] for edge in row['edges']}), len(row['edges']))
            for edge in row['edges']:
                found[edge['sender'], edge['receiver']] = edge['assignments']
        self.assertEqual(found, {(i,j): value for i,row in enumerate(counts) for j,value in enumerate(row) if i != j and value})
        self.assertEqual(dispatch['send_bytes_per_rank'], combine['receive_bytes_per_rank'])
        self.assertEqual(dispatch['receive_bytes_per_rank'], combine['send_bytes_per_rank'])
        self.assertGreaterEqual(dispatch['pairwise_barrier_modeled_seconds'], dispatch['endpoint_service_lower_seconds'])

    def test_local_identity_and_invalid_topk_placement(self):
        identity = all_to_all.calculate(participants=1)['summary']
        self.assertEqual(identity['dispatch_network_send_bytes'], 0)
        self.assertEqual(identity['dispatch_plus_combine_modeled_seconds'], 0)
        with self.assertRaises(ValueError):
            all_to_all.calculate(participants=32, routing='hotspot')
        with self.assertRaises(ValueError):
            all_to_all.calculate(counts=[[0] * 8 for _ in range(8)])


class PhysicalTrafficAccounting(unittest.TestCase):
    def test_numa_placement_preserves_logical_bytes_and_changes_paths(self):
        expected = [('all-a', 'grouped', 96, 0, 24), ('sender-local', 'grouped', 48, 48, 12),
                    ('sender-local', 'alternating', 48, 48, 24)]
        for placement, order, a, b, intersocket in expected:
            result = numa_staging.calculate(placement=placement, order=order)
            resources = {row['resource']: row['bytes'] for row in result['physical_traffic']['resources']}
            self.assertEqual(result['summary']['logical_send_bytes'], 48 * 2**20)
            self.assertEqual(resources.get('dram_A', 0), a * 2**20)
            self.assertEqual(resources.get('dram_B', 0), b * 2**20)
            self.assertEqual(resources['A_to_B'], intersocket * 2**20)
            self.assertEqual(resources['B_to_A'], intersocket * 2**20)
            self.assertAlmostEqual(result['summary']['aggregate_resource_lower_seconds'], intersocket * 2**20 / 8e9)
            for gpu in range(4):
                self.assertEqual(resources[f'gpu{gpu}_to_host'], 12 * 2**20)
                self.assertEqual(resources[f'gpu{gpu}_from_host'], 12 * 2**20)

    def test_shared_resource_sums_flows_and_round_barriers_are_distinct(self):
        rounds = [dict(edges=[dict(sender=0, receiver=1, bytes=100), dict(sender=2, receiver=3, bytes=100)]),
                  dict(edges=[dict(sender=1, receiver=0, bytes=200)])]
        result = account(rounds, {(0,1): ['A'], (2,3): ['A'], (1,0): ['B']}, {'A': 100, 'B': 100})
        self.assertEqual(result['logical_send_bytes'], 400)
        self.assertEqual(result['aggregate_resource_lower_seconds'], 2)
        self.assertEqual(result['sum_round_resource_lower_seconds'], 4)
        with self.assertRaises(ValueError):
            account(rounds, {(0,1): ['A']}, {'A': 100})


class MoEDedupAccounting(unittest.TestCase):
    def test_same_histogram_different_destination_unions(self):
        clustered = moe_dedup.calculate(pattern='clustered')
        spread = moe_dedup.calculate(pattern='spread')
        self.assertEqual(clustered['assignment_counts'], spread['assignment_counts'])
        a, b = clustered['summary'], spread['summary']
        self.assertEqual(a['per_assignment_dispatch_bytes'], 8 * a['deduplicated_dispatch_bytes'])
        self.assertEqual(b['per_assignment_dispatch_bytes'], b['deduplicated_dispatch_bytes'])
        for summary in (a, b):
            self.assertEqual(summary['original_source_reduction_adds'], summary['destination_reduction_adds'] + summary['remaining_source_reduction_adds'])

    def test_weighted_partial_combine_preserves_exact_integer_sum(self):
        result = moe_dedup.calculate(tokens_per_rank=2)
        for token in result['token_routes']:
            weighted = [(expert + 1) * (index + 2) for index, expert in enumerate(token['experts'])]
            partials = {}
            for expert, value in zip(token['experts'], weighted):
                destination = expert // 16
                partials[destination] = partials.get(destination, 0) + value
            self.assertEqual(sum(weighted), sum(partials.values()))
        routes = result['scenario']['routes']
        routes[0][0][1] = routes[0][0][0]
        with self.assertRaises(ValueError):
            moe_dedup.calculate(tokens_per_rank=2, routes=routes)


class CapacityScanAccounting(unittest.TestCase):
    def test_packing_rounds_rows_and_partial_groups_independently(self):
        packed = capacity_scan.packed_matrix((3, 5), 4, 4, 2)
        self.assertEqual(packed['packed_bytes'], 9)
        self.assertEqual(packed['groups'], 6)
        self.assertEqual(packed['scale_bytes'], 12)

    def test_exact_budget_boundary_and_next_request(self):
        result = capacity_scan.calculate()
        s = result['summary']
        budget = s['bf16_weight_bytes'] + 2**31 + 3 * s['bf16_kv_bytes_per_request']
        exact = capacity_scan.calculate(capacities=[budget])['capacity_comparisons'][0]
        below = capacity_scan.calculate(capacities=[budget - 1])['capacity_comparisons'][0]
        self.assertEqual(exact['maximum_requests'], 3)
        self.assertEqual(below['maximum_requests'], 2)
        self.assertTrue(exact['next_request_exceeds_capacity'])
        self.assertEqual(s['bf16_weight_bytes'], 2 * s['logical_parameters'])
        for scheme in result['storage_formats']:
            embedding = next(row for row in scheme['tensors'] if row['name'] == 'model.embed_tokens.weight')
            self.assertEqual(embedding['payload_bytes'], 2 * embedding['parameters'])
            self.assertEqual(embedding['scale_bytes'], 0)

    def test_moe_counts_all_experts_and_longer_context_reduces_capacity(self):
        small = capacity_scan.calculate('qwen3-235b-a22b')
        self.assertGreater(small['summary']['logical_parameters'], 200_000_000_000)
        self.assertTrue(all(row['maximum_requests'] == 0 for row in small['capacity_comparisons']))
        short = capacity_scan.calculate()['capacity_comparisons']
        long = capacity_scan.calculate(length=32768)['capacity_comparisons']
        for a, b in zip(short, long):
            self.assertEqual(b['maximum_requests'], a['maximum_requests'] // 4)


class DensePlacementAccounting(unittest.TestCase):
    def test_single_rank_matches_full_forward_and_pipeline_preserves_weights(self):
        placed = dense_placement.calculate(tp=1, history=7, tokens=3)
        full = qwen3.calculate('qwen3-8b', Scenario(history=7, tokens=3))
        self.assertEqual(placed['summary']['physical_weight_bytes'], full['summary']['weight_resident_bytes'])
        self.assertEqual(placed['summary']['physical_matrix_flops'], full['summary']['matrix_flops'])
        pipeline = dense_placement.calculate(tp=1, pp=8, history=7, tokens=3)
        self.assertEqual(pipeline['summary']['physical_weight_bytes'], placed['summary']['physical_weight_bytes'])
        self.assertEqual(pipeline['summary']['physical_matrix_flops'], placed['summary']['physical_matrix_flops'])
        self.assertEqual(sorted(i for row in pipeline['placement_cards'] for i in row['layer_ids']), list(range(36)))
        for row in pipeline['placement_cards']:
            names = {w['name'] for w in row['weights']}
            self.assertEqual('model.embed_tokens.weight' in names, row['stage'] == 0)
            self.assertEqual('lm_head.weight' in names, row['stage'] == 7)

    def test_kv_replication_above_head_count_and_norm_replication(self):
        one = dense_placement.calculate(tp=1)['summary']
        eight = dense_placement.calculate(tp=8)['summary']
        sixteen = dense_placement.calculate(tp=16)['summary']
        self.assertEqual(eight['physical_kv_bytes'], one['physical_kv_bytes'])
        self.assertEqual(sixteen['physical_kv_bytes'], 2 * one['physical_kv_bytes'])
        norm_parameters = 36 * (2 * 4096 + 2 * 128) + 4096
        kv_projection_parameters = 36 * 2 * 4096 * 8 * 128
        self.assertEqual(sixteen['excess_weight_bytes_over_unsharded_replicas'], 2 * (15 * norm_parameters + kv_projection_parameters))

    def test_replica_scaling_and_invalid_partitions(self):
        one = dense_placement.calculate(tp=2, pp=2, dp=1)['summary']
        two = dense_placement.calculate(tp=2, pp=2, dp=2)['summary']
        self.assertEqual(two['physical_weight_bytes'], 2 * one['physical_weight_bytes'])
        self.assertEqual(two['physical_kv_bytes'], 2 * one['physical_kv_bytes'])
        self.assertEqual(two['maximum_card_resident_bytes'], one['maximum_card_resident_bytes'])
        with self.assertRaises(ValueError):
            dense_placement.calculate(tp=3)
        with self.assertRaises(ValueError):
            dense_placement.calculate(pp=37)


class DenseCommunicationAccounting(unittest.TestCase):
    def test_embedding_and_last_logits_are_not_lost(self):
        result = dense_communication.calculate()
        ops = result['communication_operations']
        self.assertEqual(sum(row['name'].endswith('_reduce') for row in ops), 73)
        logits = next(row for row in ops if row['name'] == 'last_position_logits_all_gather')
        self.assertEqual(logits['network_send_bytes_per_replica'], 7 * 4 * 151936)
        prefill = dense_communication.calculate(tokens=8192)
        prefill_logits = next(row for row in prefill['communication_operations'] if row['name'] == logits['name'])
        self.assertEqual(logits['network_send_bytes_per_replica'], prefill_logits['network_send_bytes_per_replica'])

    def test_pipeline_feedback_and_replica_bytes(self):
        result = dense_communication.calculate(tp=2, pp=4)
        ops = result['communication_operations']
        pp = [row for row in ops if row['name'] == 'pipeline_hidden_transfer']
        self.assertEqual(len(pp), 3)
        self.assertEqual(sum(row['network_send_bytes_per_replica'] for row in pp), 3 * 2 * 8192)
        feedback = next(row for row in ops if row['name'] == 'selected_token_to_first_stage')
        self.assertEqual(feedback['network_send_bytes_per_replica'], 4)
        twice = dense_communication.calculate(tp=2, pp=4, dp=2)['summary']
        self.assertEqual(twice['network_send_bytes_all_replicas'], 2 * result['summary']['network_send_bytes_all_replicas'])
        self.assertEqual(twice['serial_communication_path_seconds'], result['summary']['serial_communication_path_seconds'])
        self.assertEqual(dense_communication.calculate(tp=1)['summary']['serial_communication_path_seconds'], 0)


class PipelineScheduleAccounting(unittest.TestCase):
    def test_equal_stages_match_fill_and_drain_formula(self):
        result = pipeline_schedule.calculate(microbatches=8, steps=1, stage_ns=[10]*4, transfer_ns=[0]*3, feedback_ns=0)
        self.assertEqual(result['summary']['finish_ns'], (8 + 4 - 1) * 10)
        self.assertEqual(result['summary']['first_completion_ns'], 40)

    def test_single_request_cannot_pipeline_dependent_tokens(self):
        result = pipeline_schedule.calculate(microbatches=1, steps=3, stage_ns=[10,20], transfer_ns=[5], feedback_ns=7)
        self.assertEqual(result['completion_ns_by_microbatch'], [[35,77,119]])
        self.assertEqual(result['summary']['maximum_inter_step_completion_ns'], 42)

    def test_resource_nonoverlap_feedback_and_joint_live_intervals(self):
        result = pipeline_schedule.calculate(transfer_ns=[2000000]*3)
        for stage in range(4):
            rows = [row for row in result['pipeline_operations'] if row['stage'] == stage]
            self.assertTrue(all(a['end_ns'] <= b['start_ns'] for a,b in zip(rows,rows[1:])))
        for row in result['pipeline_operations']:
            if row['stage'] == 0 and row['step']:
                previous = result['completion_ns_by_microbatch'][row['microbatch']][row['step']-1]
                self.assertGreaterEqual(row['start_ns'], previous + 100000)
        self.assertEqual(pipeline_schedule.peak_intervals([(0,10,4),(10,20,4)]), 4)
        self.assertEqual(pipeline_schedule.peak_intervals([(0,11,4),(10,20,4)]), 8)


class FinitePipelineBufferAccounting(unittest.TestCase):
    def test_double_buffer_recovers_overlap_but_single_slot_stalls(self):
        args = dict(microbatches=4, steps=1, stage_ns=[10,10], transfer_ns=[10], feedback_ns=0)
        unlimited = pipeline_schedule.calculate(**args)
        single = pipeline_schedule.calculate(**args, buffer_slots=1)
        double = pipeline_schedule.calculate(**args, buffer_slots=2)
        self.assertEqual(unlimited['summary']['finish_ns'], 60)
        self.assertEqual(single['summary']['finish_ns'], 90)
        self.assertEqual(double['summary']['finish_ns'], 60)
        self.assertGreater(single['summary']['summed_sender_buffer_wait_ns'], 0)

    def test_slots_not_reused_before_release_and_peaks_fit_pool(self):
        for slots in (1,2):
            result = pipeline_schedule.calculate(buffer_slots=slots, transfer_ns=[2000000]*3)
            size = result['summary']['activation_bytes_per_boundary']
            for boundary in range(3):
                for slot in range(slots):
                    rows = [r for r in result['pipeline_transfers'] if r['boundary'] == boundary and r['sender_slot'] == slot]
                    self.assertTrue(all(a['end_ns'] <= b['sender_reserved_ns'] for a,b in zip(rows,rows[1:])))
                    rows = [r for r in result['pipeline_transfers'] if r['boundary'] == boundary and r['receiver_slot'] == slot]
                    self.assertTrue(all(a['receiver_release_ns'] <= b['start_ns'] for a,b in zip(rows,rows[1:])))
            for row in result['pipeline_buffers']:
                self.assertLessEqual(row['sender_peak_bytes'], slots * size)
                self.assertLessEqual(row['receiver_peak_bytes'], slots * size)
            self.assertLessEqual(result['summary']['declared_boundary_buffer_peak_bytes'], result['summary']['reserved_boundary_pool_bytes'])
        with self.assertRaises(ValueError):
            pipeline_schedule.calculate(buffer_slots=0)


class Reproducibility(unittest.TestCase):
    def test_sources_have_verified_bytes(self):
        self.assertGreaterEqual(verify_sources()["verified"], 40)

    def test_cli_does_not_depend_on_current_directory(self):
        cli = Path(__file__).resolve().parents[1] / "calc.py"
        process = subprocess.run([sys.executable, str(cli), "state", "--model", "kimi-k3"],
                                 cwd="/tmp", capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(process.stdout)["model"], "kimi-k3")


if __name__ == "__main__":
    unittest.main()
