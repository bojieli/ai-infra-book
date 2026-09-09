"""Offline integrity, coverage and pairing checks; no workload regeneration."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
s=read('sources.json')
for f in s['files']:
    data=(ROOT/f['path']).read_bytes()
    assert len(data)==f['bytes'] and sha(f['path'])==f['sha256']
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f['git_blob_sha1']
summary=read('results/summary.json')
assert sha('run.py')==summary['source_sha256']
assert summary['revision']==s['revision']
cases=summary['cases']
assert {(c['source_window_start'],c['seed']) for c in cases}=={(w,s) for w in [143400,144600,337800,338400,339000] for s in [302,303,304]}
total=0
for c in cases:
    path='results/'+c['file'];assert sha(path)==c['sha256']
    rows=read(path);n=len(rows);total+=n
    assert n==c['generated_requests'] and n in (479,480)
    assert [r['request_id'] for r in rows]==list(range(n))
    times=[r['timestamp'] for r in rows]
    assert times==sorted(times) and all(math.isfinite(t) and 0<=t<120 for t in times)
    assert times[0]==c['first_s'] and times[-1]==c['last_s']
    a=[r['data']['input_tokens'] for r in rows];b=[r['data']['output_tokens'] for r in rows]
    assert all(isinstance(v,int) and v>=0 for v in a+b)
    for output,key in [(b,'input_output_spearman'),(np.random.RandomState(c['seed']+1000).permutation(b),'shuffled_output_spearman')]:
        assert math.isclose(float(spearmanr(a,output).statistic),c[key],abs_tol=1e-12)
assert total==7195
source=read('conversations-source.json')
assert sha('conversations_hashed.json')==source['sha256']
r=read('results/conversation-rows.json');p=read('results/conversation-pairs.json');a=read('results/conversation-audit.json')
assert len(r)==a['requests']==5720 and len(p)==a['adjacent_pairs']==4104
assert len({x['conversation_index'] for x in r})==a['conversations']==1616
assert sum(x['input_count']!=x['input_identifier_count'] for x in r)==5720
assert all(x['output_count']==x['output_identifier_count'] for x in r)
assert all(x['start_timestamp_gap_s']>=0 for x in p)
if (ROOT/'manifest.json').exists():
    for f in read('manifest.json')['files']:assert sha(f['path'])==f['sha256']
print('PASS: source integrity, 15 generated cases / 7195 requests, 5720 released records / 4104 adjacent pairs')
