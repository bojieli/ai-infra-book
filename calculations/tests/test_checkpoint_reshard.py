from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from infra_calc.topics.checkpoint_reshard import calculate, plan


class CheckpointReshardTests(unittest.TestCase):
    def test_actual_small_payload_reconstruction(self):
        # Independently build physical source files from each layout, then execute ranges.
        rows, columns, width = 5, 7, 2
        payload=b''.join(i.to_bytes(width,'little') for i in range(rows*columns))
        for source_layout in ('rows','flat'):
            for target_layout in ('rows','flat'):
                result=plan(rows,columns,3,4,source_layout,target_layout,width)
                count=rows if source_layout=='rows' else rows*columns
                units=[list(range(count))[sum(count//3+(r<count%3) for r in range(rank)):sum(count//3+(r<count%3) for r in range(rank+1))] for rank in range(3)]
                source_files=[]
                for indices in units:
                    elements=[r*columns+c for r in indices for c in range(columns)] if source_layout=='rows' else indices
                    source_files.append(b''.join(i.to_bytes(width,'little') for i in elements))
                destinations=[bytearray(n) for n in result['target_shard_bytes']]
                coverage=[bytearray(n) for n in result['target_shard_bytes']]
                for piece in result['pieces']:
                    src,dst=piece['source_rank'],piece['target_rank'];a=piece['source_file_offset_bytes'];b=piece['target_buffer_offset_bytes'];size=piece['length_bytes']
                    destinations[dst][b:b+size]=source_files[src][a:a+size]
                    for i in range(b,b+size):coverage[dst][i]+=1
                self.assertEqual(b''.join(destinations),payload)
                self.assertTrue(all(v==1 for row in coverage for v in row))

    def test_official_gate_four_to_eight(self):
        r=calculate()
        self.assertEqual(r['summary']['logical_checkpoint_bytes'],672*1024**2)
        self.assertEqual(r['summary']['target_payload_bytes'],[84*1024**2]*8)
        weights=r['checkpoint_component_plans'][0]
        self.assertEqual(weights['source_shard_bytes'],[24*1024**2]*4)
        for piece in weights['pieces']:
            rank=piece['target_rank']
            self.assertEqual(piece['source_rank'],rank//2)
            self.assertEqual(piece['source_file_offset_bytes'],(rank%2)*12*1024**2)
            self.assertEqual(piece['length_bytes'],12*1024**2)
            self.assertEqual(piece['target_buffer_offset_bytes'],0)
        self.assertEqual(calculate(include_optimizer=False)['summary']['logical_checkpoint_bytes'],96*1024**2)

    def test_reverse_remainder_and_moe_scope(self):
        reverse=calculate(source_parts=8,target_parts=4)
        self.assertEqual(reverse['summary']['logical_checkpoint_bytes'],672*1024**2)
        r=calculate(source_parts=7,target_parts=5,source_layout='flat')
        self.assertEqual(r['summary']['requested_read_bytes'],14*12288*4096)
        self.assertTrue(any(p['first_coordinate'][1] for p in r['checkpoint_component_plans'][0]['pieces']))
        self.assertEqual(calculate(model='qwen3-235b-a22b')['summary']['logical_checkpoint_bytes'],14*1536*4096)
        for kw in ({'source_parts':True},{'target_parts':0},{'include_optimizer':1},{'source_layout':'fused'}):
            with self.assertRaises(ValueError):calculate(**kw)
