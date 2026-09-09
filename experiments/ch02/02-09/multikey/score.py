"""Score fixed multi-key retrieval, retaining raw responses and all negatives."""
import argparse, json
from pathlib import Path
from common import save

def strict_object(text):
    def pairs(items):
        obj={}
        for key,value in items:
            if key in obj: raise ValueError('duplicate key')
            obj[key]=value
        return obj
    try:
        value=json.loads(text,object_pairs_hook=pairs)
        return value if type(value) is dict else None
    except (ValueError,TypeError): return None

def score(out):
    frozen=json.loads((out/'cases.json').read_text())
    rows=json.loads((out/'requests.json').read_text()) if (out/'requests.json').exists() else []
    ids=[c['id'] for c in frozen['cases']]
    assert len(ids)==len(set(ids))==4
    record_ids=[r.get('case_id') for r in rows]
    complete=len(record_ids)==4 and set(record_ids)==set(ids)
    scores=[]
    for c in frozen['cases']:
        matches=[r for r in rows if r.get('case_id')==c['id']]
        r=matches[0] if len(matches)==1 else {}
        response=r.get('response') or {}
        if not isinstance(response,dict):response={}
        meta=response.get('meta_info') or {}
        finish=meta.get('finish_reason') if isinstance(meta,dict) else None
        normal=isinstance(finish,dict) and finish.get('type')=='stop'
        text=response.get('text');obj=strict_object(text)
        correct=obj==c['expected']
        output=response.get('output_ids')
        schema=isinstance(text,str) and isinstance(output,list) and bool(output) and all(type(t) is int and t>=0 for t in output)
        input_match=r.get('input_ids')==c['input_ids']
        sampling_match=r.get('sampling_params')==frozen['sampling']
        success=complete and r.get('status')=='returned' and schema and input_match and sampling_match and normal and correct
        scores.append(dict(case_id=c['id'],strict_success=bool(success),json_exact=correct,normal_stop=normal,
                           schema_valid=schema,input_matches=input_match,sampling_matches=sampling_match,
                           expected=c['expected'],parsed=obj,finish_reason=finish))
    save(out/'scores.json',dict(scope='four known Qwen long-context tasks; not blind or general quality',
                               record_set_complete=complete,denominator=4,strict_success=sum(r['strict_success'] for r in scores),cases=scores,
                               requests_present=len(rows),strict_numerical_clearance=False))
    log=(out/'run.log').read_text(errors='replace') if (out/'run.log').exists() else ''
    save(out/'pool-log-evidence.json',dict(lines=[l for l in log.splitlines() if any(s in l for s in ['DSV4 pool sizes:','DSV4 memory calculation:','Load weight end','KV Cache'])]))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);score(p.parse_args().out)
