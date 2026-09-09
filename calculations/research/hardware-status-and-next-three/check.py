"""Read-only public hardware acceptance consistency check; writes only this report."""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sys.path.insert(0,str(PROJECT/'src'))
from infra_calc import hardware
from infra_calc.sources import records

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
current=hardware.catalog()  # verifies official archives and every device schema
replayed=hardware.audit_catalog(current)
stored=json.loads((PROJECT/'results/hardware-audit.json').read_text())
source_rows=sorted([r for r in records() if r.get('model')=='hardware'],key=lambda r:(r['id'],r['file']))
plan=(PROJECT/'PLAN.md').read_text()
acceptance={}
for code,file in [('H05','h05-source-review.json'),('H07','h07-source-review.json')]:
 entry=json.loads((PROJECT/'inventory'/file).read_text());binding=entry['binding']
 acceptance[code]=dict(plan_checked=bool(re.search(r'^- \[x\] '+code+r'\b',plan,re.M)),
                      accepted=entry['may_check_plan_item'],hardware_hash_matches=binding['hardware_sha256']==sha(PROJECT/'configs/hardware.json'),
                      source_subset_hash_matches=binding['hardware_sources_subset_sha256']==canonical(source_rows))
summary=dict(plan_checked={f'H{i:02}':bool(re.search(r'^- \[x\] H'+f'{i:02}'+r'\b',plan,re.M)) for i in range(1,8)},
             audit_exact_replay=replayed==stored,catalog_validation_passed=True,
             summary=replayed['summary'],acceptance=acceptance,hardware_sources=len(source_rows),
             catalog_status=current['status'],pending_families=current['pending_families'],
             interpretation='Acceptance covers finite official-source review, not all fields numerically known; status/pending prose is stale relative to accepted scope.')
files=['PLAN.md','configs/hardware.json','src/infra_calc/hardware.py','results/hardware-audit.json','inventory/h05-source-review.json','inventory/h07-source-review.json']
summary['input_bindings']=[dict(file=f,sha256=sha(PROJECT/f)) for f in files]
(HERE/'verification.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['input_bindings','pending_families']},indent=2))
