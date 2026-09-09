import argparse,json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).absolute().parent
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=ROOT/'runs/paired-002');p.add_argument('--out',type=Path,default=ROOT/'analysis.json');args=p.parse_args()
cases=json.loads((ROOT/'cases.json').read_text());v4=json.loads((ROOT/'reference/v4-requests.json').read_text());qwen=json.loads((args.run/'requests.json').read_text());prep=json.loads((args.run/'prepared.json').read_text());checks=0
expected_ids=[x['id'] for x in cases['cases']]
for raw in [v4,qwen,prep]:assert len(raw)==8 and sorted(x['case_id'] for x in raw)==sorted(expected_ids);checks+=1
vi={x['case_id']:x for x in v4};qi={x['case_id']:x for x in qwen};pi={x['case_id']:x for x in prep};rows=[]
for c in cases['cases']:
 i=c['id'];v=vi[i];q=qi[i];prepared=pi[i]
 answers=re.findall('retrieval phrase is "([^"]+)"',c['messages'][1]['content']);assert answers==[c['answer']];checks+=1
 h=hashlib.sha256(json.dumps(c['messages'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 assert prepared['messages']==c['messages'] and prepared['messages_sha256']==q['messages_sha256']==h;checks+=1
 assert v['input_ids']==c['input_ids'] and q['input_ids']==prepared['input_ids'];checks+=1
 assert v['sampling_params']==cases['sampling'];assert q['sampling']==dict(temperature=0,top_p=1,top_k=1,max_tokens=32);checks+=2
 vt=v['response']['text'];vf=v['response']['meta_info']['finish_reason']['type'];qt=q['text'];qf=q['finish_reason']
 assert v['status']=='returned' and q['output_ids'] and v['response']['output_ids'];checks+=1
 rows.append(dict(case_id=i,messages_sha256=h,expected=c['answer'],position=c['position'],variant=c['variant'],v4_input_tokens=len(v['input_ids']),qwen_input_tokens=len(q['input_ids']),v4_text=vt,qwen_text=qt,v4_finish=vf,qwen_finish=qf,v4_strict=vt.strip()==c['answer'] and vf=='stop',qwen_strict=qt.strip()==c['answer'] and qf=='stop',v4_output_tokens=len(v['response']['output_ids']),qwen_output_tokens=len(q['output_ids'])))
result=dict(checks=checks,unique_cases=8,identical_message_pairs=8,rows=rows,qwen_strict=sum(x['qwen_strict'] for x in rows),v4_flash_strict=sum(x['v4_strict'] for x in rows),other_candidates=dict(v4_pro=None,kimi_k3=None),selection=('No quality preference established on this eight-case task; cost/performance are not compared here.' if all(x['qwen_strict']==x['v4_strict'] for x in rows) else 'Task-specific quality differences observed; inspect per-case results, not a general model ranking.'),scope='Fresh Qwen outputs paired with sealed historical V4 Flash outputs for identical messages; native templates and deployment precision differ; not general quality or simultaneous performance.')
args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))
