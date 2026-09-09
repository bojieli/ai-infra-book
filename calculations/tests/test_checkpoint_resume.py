import json
from pathlib import Path
from itertools import product
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics import checkpoint_resume as resume


class CheckpointResumeTests(unittest.TestCase):
    def test_independent_coordinates_and_payload(self):
        r=resume.calculate()
        for t in r['checkpoint_resume_tensors']:
            coords=[]
            for c in t['saved_chunks']:
                coords.extend(product(*(range(o,o+n) for o,n in zip(c['offsets'],c['sizes']))))
            expected=set(product(*(range(n) for n in t['shape'])))
            self.assertEqual(set(coords),expected);self.assertEqual(len(coords),len(expected))
        params=129*257+257+257*17+17
        logical=12*params+4*4+2*5056+8
        self.assertEqual(r['summary']['unique_logical_state_bytes'],logical)
        self.assertEqual(r['summary']['actual_checkpoint_file_bytes'],247788+264331+6393)
        for group in r['checkpoint_resume_groups']:
            self.assertEqual(group['sum_rank_local_logical_bytes'],logical+(group['world']-1)*(2*5056+4*4+8))

    def test_coverage_holes_overlap_scalar(self):
        resume.coverage([], [dict(offsets=[],sizes=[])])
        for chunks in ([dict(offsets=[0],sizes=[2])],[dict(offsets=[0],sizes=[2]),dict(offsets=[1],sizes=[2])]):
            with self.assertRaises(ValueError):resume.coverage([3],chunks)
        with self.assertRaises(ValueError):resume.coverage([], [dict(offsets=[],sizes=[])]*2)

    def test_next_update_and_negative_control_required(self):
        raw,sources=resume.read_records();key='results/load-w3-axis1-rank0.json'
        for field,value in [('next_loss',0),('optimizer_loss_negative_control_detected',False)]:
            record=json.loads(raw[key]);record[field]=value;changed=dict(raw);changed[key]=json.dumps(record).encode()
            with patch.object(resume,'read_records',return_value=(changed,sources)):
                with self.assertRaises(ValueError):resume.calculate()
