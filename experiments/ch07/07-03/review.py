"""Independent raw-to-CSV linkage and acceptance audit; stdlib only."""
import csv,json,re,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
rows=list(csv.DictReader((P/'rows.csv').open()));checks=[]
def ck(n,b):
 assert b,n
 checks.append(n)
for r in rows:
 a=(P/r['source']).read_text().splitlines()[int(r['line'])-1].split(); o=5 if r['mode']=='out_of_place' else 9
 ck(r['run']+':raw_row',int(a[0])==int(r['size_bytes']) and int(a[1])==int(r['count']) and [float(x) for x in a[o:o+4]]==[float(r[k]) for k in ['time_us','algbw_GB_s','busbw_GB_s','wrong']])
 ck(r['run']+':factor',abs(float(r['bus_factor'])-(2-2/int(r['nranks'])))<1e-12)
for x in json.loads((P/'runs.json').read_text()):
 text=(P/x['path']).read_text(); expected='Out of bounds values : 0 OK' in text and all(float(r['wrong'])==0 for r in rows if r['run']==x['id'])
 ck(x['id']+':acceptance',x['eligible_curve']==expected)
for r in ['corrupt_0','corrupt_1']:ck(r+':rejected',not next(x['eligible_curve'] for x in json.loads((P/'runs.json').read_text()) if x['id']==r))
ck('all_mode_rows',len(rows)==176)
# Check extraction back to the frozen API body, independently of parser offsets.
objects=[json.loads((P/'sources/nccl-tests-309.json').read_text()),json.loads((P/'sources/nccl-1403.json').read_text())]+json.loads((P/'sources/nccl-tests-309-comments.json').read_text())+json.loads((P/'sources/nccl-1403-comments.json').read_text())
for x in json.loads((P/'runs.json').read_text()):
 if x['path'].startswith('raw/'):
  obj=next(v for v in objects if v['html_url']==x['url']);ck(x['id']+':original_body',(P/x['path']).read_text() in obj['body'].replace('\r\n','\n'))
(P/'independent-review.json').write_text(json.dumps(dict(checks=len(checks),all_passed=True,checked=checks),indent=2)+'\n')
print(len(checks),'independent checks passed')
