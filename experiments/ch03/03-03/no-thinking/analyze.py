import hashlib,json,re
from pathlib import Path
from tasks import TASKS,answer,dp,prompt
R=Path(__file__).resolve().parent
baseline=json.loads((R/'baseline.json').read_text())
assert hashlib.sha256((R/'tasks.py').read_bytes()).hexdigest()==baseline['source_files']['tasks.py']
assert hashlib.sha256((R/'run.py').read_bytes()).hexdigest()==baseline['prepared_files']['run.py']
E=json.loads((R/'results/environment.json').read_text())
for f,h in E['source_hashes'].items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h
raw=[json.loads(s) for s in (R/'results/raw.jsonl').read_text().splitlines()];order=json.loads((R/'results/order.json').read_text());assert len(raw)==len(order)==24
truth={t['id']:answer(t) for t in TASKS};assert all(dp(t)==truth[t['id']] for t in TASKS)
markers=json.loads((R/'results/tokenizer-markers.json').read_text());assert len(set(markers.values()))==3
def tail_shape(text):
 text=text.rstrip();trailing_object=False;trailing_fence=False
 for i,char in enumerate(text):
  if char!='{':continue
  try:
   obj,used=json.JSONDecoder().raw_decode(text[i:])
   if isinstance(obj,dict) and not text[i+used:].strip():trailing_object=True
  except Exception:pass
 for match in re.finditer(r'```(?:json)?[ \t]*\n(.*?)\n```',text,re.S):
  if text[match.end():].strip():continue
  try:trailing_fence=isinstance(json.loads(match.group(1)),dict)
  except Exception:pass
 return dict(complete_trailing_json_object=trailing_object,complete_trailing_fenced_json_object=trailing_fence)
summary={};count=0;diagnostics=[]
for row,expected in zip(raw,order):
 assert all(row[k]==v for k,v in expected.items());task=next(t for t in TASKS if t['id']==row['task']);c=row['candidates'];n=1 if row['policy']=='adaptive' and len(task['values'])<=8 else 2;assert len(c)==n;count+=n
 valid=[]
 for i,x in enumerate(c):
  assert x['index']==i and len(x['output_ids'])<=4096 and x['cached_tokens']==0
  assert x['messages']==[dict(role='user',content=prompt(task))]
  assert all(x['start']<=ev['at']<=x['end'] and 0<=ev['tokens']<=len(x['output_ids']) for ev in x['events'])
  assert row['start']<=x['start']<=x['end']<=x['validation_start']<=x['validation_end']<=row['selection_start']
  assert all(a['at']<=b['at'] and a['tokens']<=b['tokens'] for a,b in zip(x['events'],x['events'][1:]));assert x['events'][-1]['tokens']==len(x['output_ids'])
  parsed_value=None;parse_error_type=None
  try:
   parsed=json.loads(x['text'].strip());assert set(parsed)=={'count'} and type(parsed['count']) is int
   parsed_value=parsed['count']
  except Exception as error:parse_error_type=type(error).__name__
  assert x['value']==parsed_value
  category='invalid_final_json' if parsed_value is None else 'correct_candidate' if parsed_value==truth[row['task']] else 'wrong_integer'
  parts=dict(reasoning=0,nonreasoning=0,delimiter=0,termination=0);phase='nonreasoning'
  for tid in x['output_ids']:
   if tid==markers['<think>']:parts['delimiter']+=1;phase='reasoning'
   elif tid==markers['</think>']:parts['delimiter']+=1;phase='nonreasoning'
   elif tid==markers['<|im_end|>']:parts['termination']+=1
   else:parts[phase]+=1
  assert sum(parts.values())==len(x['output_ids'])
  diagnostics.append(dict(output_parts=parts,parse_error_type=parse_error_type,recorded_error=x['error'],tail_shape=tail_shape(x['text']),group=row['group'],trial=row['trial'],task=row['task'],policy=row['policy'],candidate=i,category=category,finish_reason=x['finish_reason'],output_tokens=len(x['output_ids']),parsed_value=parsed_value))
  if parsed_value is not None:valid.append(parsed_value)
 if row['policy']!='parallel' and n==2:assert c[0]['validation_end']<=c[1]['start']
 if row['policy']=='parallel':assert max(x['start'] for x in c)<min(x['end'] for x in c)
 assert row['selection_start']<=row['selected_at']<=row['scored_at']
 selected=max(valid,key=lambda x:valid.count(x)) if valid else None;assert row['selected']==selected and row['correct']==(selected==truth[row['task']])
 p=summary.setdefault(row['policy'],dict(groups=0,correct=0,requests=0,input_tokens=0,output_tokens=0,wall_s=0,validation_s=0,truncated=0))
 p['groups']+=1;p['correct']+=int(row['correct']);p['requests']+=n;p['input_tokens']+=sum(len(x['input_ids']) for x in c);p['output_tokens']+=sum(len(x['output_ids']) for x in c);p['wall_s']+=row['scored_at']-row['start'];p['validation_s']+=sum(x['validation_end']-x['validation_start'] for x in c)+row['scored_at']-row['selection_start'];p['truncated']+=sum(x['finish_reason']=='length' for x in c)
assert count==44
for p in summary.values():
 p['output_tokens_per_correct']=p['output_tokens']/p['correct'] if p['correct'] else None
 p['wall_s_per_correct']=p['wall_s']/p['correct'] if p['correct'] else None
 p['fee']=None
pairs=[]
for trial in range(2):
 for task in TASKS:
  a=next(r for r in raw if r['trial']==trial and r['task']==task['id'] and r['policy']=='serial')
  b=next(r for r in raw if r['trial']==trial and r['task']==task['id'] and r['policy']=='parallel')
  pairs.append(dict(trial=trial,task=task['id'],input_ids_equal=[x['input_ids']==y['input_ids'] for x,y in zip(a['candidates'],b['candidates'])],output_ids_equal=[x['output_ids']==y['output_ids'] for x,y in zip(a['candidates'],b['candidates'])]))
assert all(all(p['input_ids_equal']) for p in pairs)
(R/'paired-output-checks.json').write_text(json.dumps(pairs,indent=2)+'\n')
(R/'candidate-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
(R/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
