from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.cache_restart import calculate


class RestartTests(unittest.TestCase):
    def test_real_file_geometry_and_reuse_gap(self):
        s=calculate()['summary'];page=36*2*8*128*2*16
        self.assertEqual(s['kv_page_bytes'],page)
        self.assertEqual(s['stored_payload_bytes'],65*page)
        self.assertEqual(s['consumer_read_file_bytes'],64*page)
        self.assertEqual(s['consumer_reusable_bytes'],63*page)
        self.assertEqual(s['read_but_not_reused_token_equivalent_bytes'],page)

    def test_successful_set_is_not_new_file_count(self):
        r=calculate();calls={(row['phase'],row['method']):row for row in r['restart_storage_calls']}
        self.assertEqual(calls['consumer','set']['calls'],1)
        self.assertEqual(r['summary']['verified_payload_files'],65)
        self.assertEqual([row['cached_tokens'] for row in r['restart_requests']],[0,1008,1008,1008,1008,1008])
        saved={row['prefill_saved_matrix_flops'] for row in r['restart_requests'] if row['cached_tokens']}
        self.assertEqual(len(saved),1);self.assertGreater(next(iter(saved)),0)

    def test_actual_payload_corruption_rejected_without_writing(self):
        original=Path.read_bytes
        def read(path):
            data=original(path)
            if 'sources/cache-restart/storage-v3/' in str(path):
                return bytes([data[0]^1])+data[1:]
            return data
        with patch.object(Path,'read_bytes',read):
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):calculate()
