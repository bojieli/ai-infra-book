"""Verify four measured configurations and exact replay identity."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).parent
names=['measured-chunk512','measured-chunk8192','measured-nochunk8192','measured-graph512']
envs=[]
summaries=[]
for name in names:
    p=root/'results'/name
    subprocess.run([sys.executable,str(root/'analyze.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
    e=json.loads((p/'environment.json').read_text())
    assert e['completed_trials']==3
    assert e['run_sha256']==hashlib.sha256((root/'run.py').read_bytes()).hexdigest()
    assert e['requests_sha256']==hashlib.sha256((p/'requests.json').read_bytes()).hexdigest()
    assert e['vllm']=='0.23.0'
    envs.append(e)
    summaries.append(json.loads((p/'summary.json').read_text()))
assert len({e['requests_sha256'] for e in envs})==1
for summary in summaries[1:]:
    for a,b in zip(summaries[0]['requests'],summary['requests']):
        assert (a['trial'],a['id'],a['output_token_ids'])==(b['trial'],b['id'],b['output_token_ids'])
def differences(i,j):
    a,b=envs[i]['config'],envs[j]['config']
    return {k for k in a if a[k]!=b[k]}
assert differences(0,1)=={'max_num_batched_tokens'}
assert differences(1,2)=={'enable_chunked_prefill'}
assert differences(0,3)=={'enforce_eager','compilation_config'}
assert all(e['config']['compilation_config']['mode']==0 for e in envs)
assert 'Graph capturing finished' in (root/'results/measured-graph512.log').read_text()
print('Verified 4 configurations, 72 completed requests, input/source hashes, matching output tokens, and controlled config differences.')
