import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from infra_calc.topics import fa4_resource_balance as calculate

class TileTests(unittest.TestCase):
    def test_reject_unsupported_shapes(self):
        for m,n,d in [(127,128,128),(128,129,128),(128,128,256),(True,128,128),(0,128,128)]:
            with self.assertRaises(ValueError):calculate.tile(m,n,d)
    def test_rates_and_ties(self):
        with self.assertRaises(ValueError):calculate.tile(128,128,128,0)
        with self.assertRaises(ValueError):calculate.tile(128,128,128,True)
        self.assertEqual(calculate.tile(128,128,128)['tied_limiting_resources'],['matrix','exp'])
        self.assertEqual(calculate.tile(128,128,128,2,2,1)['tied_limiting_resources'],['smem'])
    def test_corrupt_source_rejected(self):
        record=json.loads((calculate.ROOT/'configs/fa4-resource-inputs.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config_path=root/'configs/fa4-resource-inputs.json'
            config_path.parent.mkdir(parents=True,exist_ok=True)
            config_path.write_text(json.dumps(record))
            for source in record['sources']:
                path=root/source['file'];path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((calculate.ROOT/source['file']).read_bytes())
            for source in record['sources']:
                path=root/source['file'];old=path.read_bytes();path.write_bytes(old+b'corrupt')
                with patch.object(calculate,'ROOT',root),self.assertRaises(ValueError):calculate.inputs()
                path.write_bytes(old)
