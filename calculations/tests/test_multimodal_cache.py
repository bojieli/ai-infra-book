import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from infra_calc.topics import multimodal_cache


class MultimodalCacheTests(unittest.TestCase):
    def test_official_features_kv_and_interface_bytes(self):
        result = multimodal_cache.calculate()
        summary = result['summary']
        self.assertEqual(summary['preprocessed_grid_thw'], [1, 40, 40])
        self.assertEqual(summary['complete_encoder_shape'], [400, 10240])
        self.assertEqual(summary['complete_encoder_bytes_per_image'], 8192000)
        self.assertEqual(sum(row['bytes'] for row in result['multimodal_encoder_components']), 8192000)
        self.assertEqual([row['vision_block'] for row in result['multimodal_encoder_components']], [None, 5, 11, 17])
        self.assertEqual(summary['visual_kv_bytes_per_image'], 56.25 * 1024**2)
        self.assertEqual(summary['visual_positions_per_request'], 1600)
        self.assertEqual(summary['declared_input_kv_bytes'], 281.25 * 1024**2)
        self.assertEqual(Fraction(summary['compressed_image_uplink_exact_seconds']), 1)
        self.assertEqual(Fraction(summary['complete_encoder_uplink_exact_seconds']), Fraction(256, 25))
        fast = multimodal_cache.calculate(images_per_request=1, text_tokens=0,
                                          network_bytes_per_second=25 * 10**9)['summary']
        self.assertEqual(Fraction(fast['one_image_ec_network_exact_seconds']), Fraction(256, 781250))
        fp32 = multimodal_cache.calculate(dtype='fp32', kv_dtype='bf16')['summary']
        self.assertEqual(fp32['complete_encoder_bytes_per_image'], 2 * summary['complete_encoder_bytes_per_image'])
        self.assertEqual(fp32['declared_input_kv_bytes'], summary['declared_input_kv_bytes'])

    def test_patch_groups_and_preprocessed_boundaries(self):
        # Independent coordinate enumeration: four 16px patches map to one merged position.
        for height, width in ((256, 256), (640, 640), (640, 672), (672, 672), (256, 4096)):
            groups = {}
            for y in range(0, height, 16):
                for x in range(0, width, 16):
                    groups.setdefault((y // 32, x // 32), []).append((y, x))
            summary = multimodal_cache.calculate(preprocessed_height=height,
                                                  preprocessed_width=width)['summary']
            self.assertTrue(all(len(group) == 4 for group in groups.values()))
            self.assertEqual(summary['image_visual_positions'], len(groups))
            self.assertEqual(summary['pre_merge_patch_count'], sum(map(len, groups.values())))
        self.assertEqual(multimodal_cache.calculate(preprocessed_height=4096, preprocessed_width=4096,
                                                    images_per_request=16, text_tokens=0)['summary']['declared_input_positions'], 262144)
        for inputs in ({'preprocessed_height': 639}, {'preprocessed_width': 656},
                       {'preprocessed_height': 32, 'preprocessed_width': 32},
                       {'preprocessed_height': 4128, 'preprocessed_width': 4096},
                       {'preprocessed_height': 4096, 'preprocessed_width': 4096,
                        'images_per_request': 16, 'text_tokens': 1},
                       {'text_tokens': True}, {'dtype': 'fp8'}, {'encoder_cache_hit_fraction': '101/100'}):
            with self.assertRaises(ValueError):
                multimodal_cache.calculate(**inputs)
        processor, sources = multimodal_cache.read_auxiliary()
        processor['merge_size'] = 1
        with patch.object(multimodal_cache, 'read_auxiliary', return_value=(processor, sources)):
            with self.assertRaises(ValueError):
                multimodal_cache.calculate()

    def test_integer_pools_hits_and_known_capacity_boundary(self):
        cold = multimodal_cache.calculate()
        warm = multimodal_cache.calculate(encoder_cache_hit_fraction='3/4')
        self.assertEqual(cold['summary']['best_pool_splits'], [dict(encoder_workers=2, pd_workers=2)])
        self.assertEqual(Fraction(cold['summary']['best_known_bound_requests_per_second_exact']), 6)
        self.assertEqual(warm['summary']['best_pool_splits'], [dict(encoder_workers=1, pd_workers=3)])
        self.assertEqual(Fraction(warm['summary']['best_known_bound_requests_per_second_exact']), Fraction(9375, 1024))
        self.assertEqual(cold['summary']['ec_transfer_bytes_per_request'], warm['summary']['ec_transfer_bytes_per_request'])
        # Enumerate known stage work per request, independently derive server time bounds.
        for hit in (Fraction(0), Fraction(3, 4), Fraction(1)):
            result = multimodal_cache.calculate(encoder_cache_hit_fraction=str(hit))
            for row in result['multimodal_pool_assignments']:
                e, pd = row['encoder_workers'], row['pd_workers']
                resource_seconds = [Fraction(1, 4 * pd), Fraction(32768000, 300000000)]
                if hit < 1:
                    resource_seconds.append(4 * (1 - hit) / (12 * e))
                else:
                    self.assertIsNone(row['uncached_encode_requests_per_second_exact'])
                self.assertEqual(Fraction(row['bound_requests_per_second_exact']), 1 / max(resource_seconds))
            self.assertFalse(result['summary']['encoder_cache_service_capacity_known'])
        equality = multimodal_cache.calculate(encoder_cache_hit_fraction='3/4',
                                              arrival_requests_per_second='9375/1024')
        self.assertFalse(equality['summary']['arrival_strictly_below_best_known_bound'])
        # A one-request/s shared link dominates every positive split: retain all ties.
        tie = multimodal_cache.calculate(network_bytes_per_second=32768000)
        self.assertEqual(len(tie['summary']['best_pool_splits']), 3)


if __name__ == '__main__':
    unittest.main()
