"""Read-only validation of the parent's actual public rendering."""
from pathlib import Path
import hashlib
import json
import sys
HERE=Path(__file__).resolve().parent;P=HERE.parents[1];C=HERE.parent/'capacity-curves'
sys.path.insert(0,str(P/'src'))
from infra_calc import capacity_plot as m
D=P/'figures/capacity-curves'
manifest=json.loads((D/'manifest.json').read_text())
assert len(manifest['inputs'])==13 and len(manifest['artifacts'])==4
for row in manifest['inputs']+manifest['artifacts']:
    assert hashlib.sha256((P/row['file']).read_bytes()).hexdigest()==row['sha256']
assert json.loads((D/'data.json').read_text())==json.loads((C/'figures/data.json').read_text())==m.calculate()
assert m.verify()=={'verified_figures':3}
(HERE/'rendered-results.json').write_text(json.dumps({'public_verify':m.verify(),'input_hashes':13,'artifact_hashes':4,'data_equal':True,'png_byte_equal_to_candidate':(D/'figure.png').read_bytes()==(C/'figures/figure.png').read_bytes(),'manifest_sha':hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),'module_sha':hashlib.sha256((P/'src/infra_calc/capacity_plot.py').read_bytes()).hexdigest()},indent=2)+'\n')
print('Actual public manifest/data accepted')
