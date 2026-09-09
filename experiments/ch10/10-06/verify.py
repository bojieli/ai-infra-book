"""Offline validation of saved chunks and actual resumption records."""
import hashlib
import itertools
import json
from pathlib import Path

root=Path(__file__).parent
results=root/'results'
manifest=json.loads((results/'checkpoint-manifest.json').read_text())
for name,record in manifest['files'].items():
    p=results/'checkpoint'/name
    assert p.stat().st_size==record['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
for name,tensor in manifest['tensors'].items():
    shape=tensor['shape'];covered=set()
    for chunk in tensor['chunks']:
        assert len(chunk['sizes'])==len(shape)
        for o,n,size in zip(chunk['offsets'],chunk['sizes'],shape):assert 0<=o<=o+n<=size
        positions=set(itertools.product(*(range(o,o+n) for o,n in zip(chunk['offsets'],chunk['sizes']))))
        assert not covered.intersection(positions),name
        covered.update(positions)
    assert covered==set(itertools.product(*(range(s) for s in shape))),name
reference=json.loads((results/'reference.json').read_text())
run_hash=hashlib.sha256((root/'run.py').read_bytes()).hexdigest()
for mode,world,axis in [('save',2,0),('load',2,0),('load',3,1),('load',1,0)]:
    for rank in range(world):
        r=json.loads((results/f'{mode}-w{world}-axis{axis}-rank{rank}.json').read_text())
        assert r['source_sha256']==run_hash
        assert r['world_size']==world and r['rank']==rank and r['axis']==axis
        if mode=='load':
            assert r['restored_hashes']==reference['before']
            assert r['next_state_hashes']==reference['after']
            assert r['next_loss']==reference['next_loss']
            assert r['optimizer_loss_negative_control_detected']
print('Verified checkpoint hashes and complete non-overlapping tensor coverage; 2→2, 2→3 row-to-column, and 2→1 restorations plus next-step and negative controls.')
