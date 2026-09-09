"""Separate raw-only checks; does not use analyze.py's derived step formulas."""
import json,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parents[1];checks=[]
def check(name,value):checks.append({'check':name,'pass':bool(value)})
for mode in ['ar','dflash-7','dflash-15']:
 e=[json.loads(x) for x in (P/'raw'/mode/'events.jsonl').read_text().splitlines()]
 first=min(x['t'] for x in e if x['kind']=='schedule'); obs=[x for x in e if x['t']>=first]
 submits={x['request_id'] for x in e if x['kind']=='submit' and x['phase']=='observed'}
 results={x['request_id']:x for x in e if x['kind']=='result' and x['phase']=='observed'}
 previous={};n_draft=0;n_accept=0;n_proposals=0
 for x in obs:
  if x['kind']=='schedule':
   for rid,ids in x['drafts'].items():check(mode+'/scheduled_real_proposal/'+str(x['step'])+'/'+rid,previous.get(rid,[])[:len(ids)]==ids)
  if x['kind']=='tokens':check(mode+'/output_prefix/'+str(x['t']),results[x['request_id']]['token_ids'][:len(x['token_ids'])]==x['token_ids'])
  if x['kind']!='boundary':continue
  for rid in x['request_ids']:check(mode+'/id_mapping/'+rid,rid[:-9] in ({z['request_id'] for z in e if z['kind']=='submit'} if x['boundary']=='GPUModelRunner.execute_model' else submits) and len(rid.rsplit('-',1)[-1])==8)
  if x['boundary']=='SpecDecodeBaseProposer.propose':
   previous.update(zip(x['request_ids'],x['draft_ids']))
  if x['boundary']=='RejectionSampler.forward':
   m=x['metadata'];check(mode+'/logits_rows/'+str(x['step']),x['logits_shape'][0]==sum(m['num_draft_tokens'])+len(x['request_ids']))
   for ids,k in zip(x['sampled_token_ids'],m['num_draft_tokens']):
    valid=sum(v>=0 for v in ids);check(mode+'/placeholder_suffix/'+str(x['step']),all(v==-1 for v in ids[valid:]))
    if k:n_draft+=k;n_accept+=valid-1;n_proposals+=1
 stats=[x['scheduler']['spec_decoding_stats'] for x in obs if x['kind']=='stats' and x['scheduler']['spec_decoding_stats']]
 if stats:
  check(mode+'/aggregate_draft_tokens',sum(x['num_draft_tokens'] for x in stats)==n_draft)
  check(mode+'/aggregate_accepted_tokens',sum(x['num_accepted_tokens'] for x in stats)==n_accept)
  check(mode+'/aggregate_drafts',sum(x['num_drafts'] for x in stats)==n_proposals)
 config=next(x for x in e if x['kind']=='configuration')
 check(mode+'/original_input_sha',config['input_sha256']==hashlib.sha256((P.parent/'inputs.json').read_bytes()).hexdigest())
 check(mode+'/natural_stop',all(x['finish_reason']=='stop' and len(x['token_ids'])<128 for x in results.values()))
 check(mode+'/quality_failures_preserved',sum(x['quality_pass'] for x in results.values())==2)
(P/'results/independent-checks.json').write_text(json.dumps(checks,indent=2));print(len(checks),'checks',sum(x['pass'] for x in checks),'passed')
assert all(x['pass'] for x in checks),[x for x in checks if not x['pass']][:10]
