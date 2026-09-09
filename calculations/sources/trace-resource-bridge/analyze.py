#!/usr/bin/env python3
"""Fixed trace profiling, using recorded token IDs and tokenizer phase markers."""
import collections
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics
R = Path(__file__).resolve().parent

def read(path): return json.loads((R/path).read_text())
def lines(path): return [json.loads(s) for s in (R/path).read_text().splitlines()]
def dist(xs):
 return dict(count=len(xs),min=min(xs),median=statistics.median(xs),max=max(xs),mean=statistics.mean(xs)) if xs else dict(count=0)

def main():
 for f in read('source-index.json')['files']:
  assert hashlib.sha256((R/f['copy']).read_bytes()).hexdigest()==f['sha256']
 tok=read('sources/tokenizer_config.json')['added_tokens_decoder']
 token={v['content']:int(k) for k,v in tok.items()}
 begin,end,eos=[token[k] for k in ['<think>','</think>','<|im_end|>']]
 def classify(ids,thinking):
  # Phase labels are a syntactic partition, never proof of semantic reasoning.
  phase='reasoning' if thinking else 'nonreasoning'
  counts=dict(reasoning=0,nonreasoning=0,delimiter=0,termination=0,unknown=0)
  for tid in ids:
   if tid==begin: counts['delimiter']+=1;phase='reasoning'
   elif tid==end: counts['delimiter']+=1;phase='nonreasoning'
   elif tid==eos:counts['termination']+=1
   else:counts[phase]+=1
  assert sum(counts.values())==len(ids)
  return counts
 rows=[]
 captures=lines('sources/chat/capture.jsonl');prompts=read('sources/chat/prompts.json')
 assert len(captures)==len(prompts)==4
 for i,c in enumerate(captures):
  assert c['prompt']==prompts[i]
  if i:assert c['messages'][:-2]==captures[i-1]['messages']
 locations={};finished=set()
 for p in (R/'sources/chat').glob('worker*-requests/*.log'):
  for line in p.read_text().splitlines():
   if '{' not in line:continue
   e=json.loads(line[line.index('{'):]);rid=e.get('rid','')
   if not rid.startswith('book909chat-'):continue
   if e.get('event')=='request.received':
    assert rid not in locations;locations[rid]=p.parent.name
   if e.get('event')=='request.finished':finished.add(rid)
 raw=[dict(p,group='chat_capture',prompt_id=p['id']) for p in prompts]
 for q in lines('sources/chat/requests.jsonl'):
  raw.append(dict(q,group=f"chat_{q['policy']}_trial{q['trial']}",input_ids=prompts[q['prompt_id']]['input_ids']))
 last={}
 for q in raw:
  m=q['response']['meta_info'];rid=m['id'];assert rid in locations and rid in finished
  ids=q['response']['output_ids'];n=len(q['input_ids']);assert n==m['prompt_tokens']
  parts=classify(ids,False)
  assert parts['reasoning']==m['reasoning_tokens']==0
  assert len(ids)==m['completion_tokens']
  key=(q['group'],locations[rid]);gap=q['start_s']-last[key] if key in last else None;last[key]=q['end_s']
  assert gap is None or gap>=0
  rows.append(dict(group=q['group'],request=q['prompt_id'],input_tokens=n,output_id_tokens=len(ids),engine_completion_tokens=m['completion_tokens'],cached_tokens=m['cached_tokens'],output_parts=parts,worker=locations[rid],previous_same_worker_completion_gap_s=gap,model_s=q['end_s']-q['start_s'],tool_s=None,tool=None,finish=m['finish_reason']['type']))
 for mode in ['off','on']:
  base='sources/agent-'+mode;env=read(base+'/environment.json');assert env['thinking']==(mode=='on')
  assert env['source_sha256']==hashlib.sha256((R/base/'run.py').read_bytes()).hexdigest()
  rr=lines(base+'/rounds.jsonl')
  for i,q in enumerate(rr):
   assert q['turn']==i
   assert q['model_start_s']<=q['model_end_s']<=q['tool_start_s']<=q['tool_end_s']
   if i:
    p=rr[i-1];assert q['messages']==p['messages']+[dict(role='assistant',content=p['output_text']),dict(role='user',content='Tool result: '+json.dumps(p['tool_result']))]
   if mode=='on':assert q['reasoning_end_token_id']==end
   ids=q['output_token_ids'];assert len(ids)==q['engine_metrics']['num_generation_tokens']
   rows.append(dict(group='agent_thinking_'+mode,request=i,input_tokens=len(q['prompt_token_ids']),output_id_tokens=len(ids),engine_completion_tokens=len(ids),cached_tokens=q['cached_tokens'],output_parts=classify(ids,env['thinking']),worker='single_vllm',previous_same_worker_completion_gap_s=q['model_start_s']-rr[i-1]['model_end_s'] if i else None,model_s=q['model_end_s']-q['model_start_s'],tool_s=q['tool_end_s']-q['tool_start_s'],tool=q['action']['tool'],finish=q['finish_reason']))
 groups=[]
 for name in dict.fromkeys(r['group'] for r in rows):
  rr=[r for r in rows if r['group']==name];n=sum(r['input_tokens'] for r in rr);c=sum(r['cached_tokens'] for r in rr)
  assert all(0<=r['cached_tokens']<=r['input_tokens'] for r in rr)
  groups.append(dict(group=name,requests=len(rr),input_tokens=sum(r['input_tokens'] for r in rr),input_distribution=dist([r['input_tokens'] for r in rr]),output_id_tokens=sum(r['output_id_tokens'] for r in rr),output_distribution=dist([r['output_id_tokens'] for r in rr]),output_parts={k:sum(r['output_parts'][k] for r in rr) for k in rr[0]['output_parts']},cached_tokens=c,request_hit_fraction=sum(r['cached_tokens']>0 for r in rr)/len(rr),mean_request_cached_fraction=statistics.mean(r['cached_tokens']/r['input_tokens'] for r in rr),token_weighted_cached_fraction=c/n,reuse_completion_gap_s=dist([r['previous_same_worker_completion_gap_s'] for r in rr if r['previous_same_worker_completion_gap_s'] is not None]),tool_actions=dict(collections.Counter(r['tool'] for r in rr if r['tool'] is not None)),tool_wall_s=sum(r['tool_s'] or 0 for r in rr),truncated=sum(r['finish']=='length' for r in rr)))
 # Offline weights on the four captured input+returned-output-ID lengths.
 chat=[r for r in rows if r['group']=='chat_capture'];lengths=[r['input_tokens']+r['output_id_tokens'] for r in chat]
 target=sum(map(Fraction,lengths))/4;lo=min(lengths);hi=max(lengths)
 a=[Fraction(1,4)]*4;b=[Fraction(0)]*4;b[lengths.index(lo)]=(hi-target)/(hi-lo);b[lengths.index(hi)]=(target-lo)/(hi-lo)
 weighted=[]
 for label,weights in [('uniform_four_observed_requests',a),('extremes_only_reweighting',b)]:
  mean=sum(w*x for w,x in zip(weights,lengths));assert sum(weights)==1 and mean==target
  weighted.append(dict(label=label,weights=[str(w) for w in weights],mean=str(mean),variance=str(sum(w*(x-mean)**2 for w,x in zip(weights,lengths))),second_moment=str(sum(w*x*x for w,x in zip(weights,lengths))),new_requests_executed=0,cache_hit_fraction=None,latency_s=None))
 result=dict(groups=groups,requests=rows,equal_mean_offline=dict(unit='input token IDs plus returned output token IDs, including EOS when returned',observed_lengths=lengths,distributions=weighted))
 (R/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'groups':groups,'equal_mean_offline':result['equal_mean_offline']},indent=2))
if __name__=='__main__':main()
