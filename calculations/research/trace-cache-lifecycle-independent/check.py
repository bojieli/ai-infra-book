"""Raw token/time audit and exact transfer-boundary checks."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal
import sys,json,hashlib
H=Path(__file__).resolve().parent
C=H.parent/'trace-cache-lifecycle'
sys.path.insert(0,str(C))
from calculate import calculate
from infra_calc.topics.trace_resource_bridge import SOURCE_ROOT
p=json.loads((SOURCE_ROOT/'sources/chat/prompts.json').read_text(),parse_float=Decimal)
r=calculate();checks=0
for a,b,row in zip(p,p[1:],r['transitions']):
    sequence=a['input_ids']+a['response']['output_ids'][:-1]
    mismatch=next((i for i,(x,y) in enumerate(zip(sequence,b['input_ids'])) if x!=y),min(len(sequence),len(b['input_ids'])))
    assert mismatch==row['reported_cached_tokens'];checks+=1
    gap=F(b['start_s']-a['end_s'])
    assert gap==F(row['recorded_application_gap_seconds_exact']);checks+=1
    size=mismatch*36*2*8*128*2
    assert size==row['conditional_bf16_prefix_payload_bytes'];checks+=1
    threshold=F(size)/gap
    assert F(row['minimum_host_bytes_per_second_exact'])==threshold;checks+=1
    floor=threshold.numerator//threshold.denominator
    for rate,expected in ((floor,False),(floor+1,True)):
        case=calculate(host_bytes_per_second=rate)['transitions'][b['id']-1]
        assert case['host_copy_fits_recorded_gap']==expected;checks+=1
    remaining=gap-F(10000,10**9)-F(size,25_000_000_000)
    remote_threshold=row['minimum_remote_bytes_per_second_exact']
    assert (remote_threshold is None)==(remaining<=0);checks+=1
    if remaining>0:
        assert F(remote_threshold)==F(size)/remaining;checks+=1
    assert F(row['conditional_retain_through_gap_byte_seconds_exact'])==size*gap;checks+=1
(H/'verification.json').write_text(json.dumps(dict(checks=checks,module_sha256=hashlib.sha256((C/'calculate.py').read_bytes()).hexdigest(),scope='Root independent raw-ID/decimal-time/KV and threshold arithmetic audit; no observed physical lifetime'),indent=2)+'\n')
print(checks,'checks passed')
