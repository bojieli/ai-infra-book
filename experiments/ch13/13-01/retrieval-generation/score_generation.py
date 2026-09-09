"""Strict independent exact-answer scorer; no model calls, no threshold tuning.

Records schema: JSON list {id,text,output_ids,finish_reason,metrics,...}.
All frozen requests required exactly once. No fuzzy/case/substring credit.
"""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
B=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--prompts',type=Path,required=True);p.add_argument('--records',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
plan=json.loads(a.prompts.read_text());raw=json.loads(a.records.read_text());queries={q['id']:q for q in json.loads((B/'queries.json').read_text())};protocol=json.loads((B/'protocol.json').read_text())
assert hashlib.sha256((B/'protocol.json').read_bytes()).hexdigest()==plan['protocol_sha256']
expected={r['id']:r for r in plan['requests']};assert len(expected)==288
assert Counter(r['id'] for r in raw)==Counter({k:1 for k in expected})
rows=[]
for r in raw:
 req=expected[r['id']];gold=queries[req['query_id']]
 assert req['split']==gold['split']
 text=r.get('text');ids=r.get('output_ids');finish=r.get('finish_reason')
 stopped=finish=='stop' or (isinstance(finish,dict) and finish.get('type')=='stop')
 schema=isinstance(text,str) and isinstance(ids,list) and bool(ids) and all(type(i)is int and i>=0 for i in ids)
 exact=bool(schema and text.strip()==gold['answer'] and stopped)
 rows.append(dict(id=r['id'],config_id=req['config_id'],query_id=gold['id'],split=gold['split'],expected=gold['answer'],actual=text,strict_success=exact,normal_stop=stopped,evidence_present=req['evidence_present'],input_tokens=req['input_tokens']))
cells=[]
for ci,c in enumerate(plan['configs']):
 rr=[r for r in rows if r['config_id']==ci]
 cal=[r for r in rr if r['split']=='calibration'];ev=[r for r in rr if r['split']=='evaluation'];assert len(cal)==8 and len(ev)==16
 cells.append(dict(config_id=ci,**c,calibration_correct=sum(r['strict_success'] for r in cal),calibration_total=8,evaluation_correct=sum(r['strict_success'] for r in ev),evaluation_total=16,eligible=all(r['strict_success'] for r in rr)))
selected=[]
for family in [('flat',None)]+[('hnsw',ef) for ef in protocol['efSearch']]:
 eligible=[c for c in cells if (c['index'],c['efSearch'])==family and c['calibration_correct']==8]
 if eligible:
  c=min(eligible,key=lambda c:c['k']);selected.append(dict(index=family[0],efSearch=family[1],selected_config_id=c['config_id'],k=c['k'],heldout_pass=c['evaluation_correct']==16))
 else:selected.append(dict(index=family[0],efSearch=family[1],selected_config_id=None,k=None,heldout_pass=False))
a.out.write_text(json.dumps(dict(scope='24 frozen authored questions, no natural benchmark or general semantic-quality claim',prompt_file_sha256=hashlib.sha256(a.prompts.read_bytes()).hexdigest(),records_sha256=hashlib.sha256(a.records.read_bytes()).hexdigest(),strict_gate='calibration 8/8 then heldout 16/16; exact two-word answer and normal stop',cells=cells,calibration_selected=selected,rows=rows,quality_eligible_config_ids=[c['config_id'] for c in cells if c['eligible']]),indent=2)+'\n')
print(json.dumps(dict(eligible=[c['config_id'] for c in cells if c['eligible']],selected=selected)))
